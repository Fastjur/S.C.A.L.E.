import logging
import threading
import time
import uuid
from datetime import datetime
from typing import Optional

from django.db.models import QuerySet
from django.utils.timezone import now
from enlighten import Counter

from config import settings
from energy_calculator import KwhUsedAtReadTime
from scheduler.celery import app as celery_app
from scheduling_app.models import (
    TaskQueue,
    File,
    Pod,
    Metric,
    MetricKwhMeasurement,
)
from scheduling_app.openshift import (
    get_openshift_client,
    OpenshiftClientInterface,
)
from utils.FileStates import FileStateCode, FileProcessStep, PipelineProcessor

logger = logging.getLogger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_):
    if not settings.AUTOMATED_DATA_GATHERING:
        sender.add_periodic_task(
            settings.execute_task_queues_interval,
            execute_task_queues,
            name="execute_task_queues",
        )


@celery_app.task(queue="execute_task_queues_queue")
def execute_task_queues():
    logger.info("Executing all applicable task queues")
    executor = QueueExecutor(openshift_client=get_openshift_client())
    executor.execute_task_queues()


class QueueExecutor:
    def __init__(self, openshift_client: OpenshiftClientInterface):
        self._openshift_client = openshift_client

    def execute_task_queues(
        self,
        instantly: bool = False,
        manager=None,
        ignore_timeout: bool = False,
    ):
        task_queues = (
            TaskQueue.objects.filter(
                start_time__lte=now() if not instantly else datetime.max,
                files__is_popped=False,
            )
            .distinct()
            .order_by("start_time")
        )
        if len(task_queues) > 1:
            logger.warning(
                "More than one task queue is ready to start, this is not properly "
                "handled yet, for now they just execute in order"
            )

        for task_queue in task_queues:
            logger.info("Starting task queue %s", task_queue)

            threads: list[TaskQueueExecutor] = []
            lock = threading.Lock()

            p_bar = None
            p_bar_lock = None
            if manager:
                p_bar = manager.counter(
                    total=task_queue.files.count(),
                    unit="tasks",
                )
                p_bar_lock = threading.Lock()

            for _ in range(settings.get("MAX_CONCURRENT_PROCESSORS")):
                thread = TaskQueueExecutor(
                    task_queue,
                    self._openshift_client,
                    lock,
                    p_bar,
                    p_bar_lock,
                    ignore_timeout=ignore_timeout,
                )
                threads.append(thread)

            for thread in threads:
                thread.start()

            for thread in threads:
                thread.join()

            logger.info("Finished task queue %s", task_queue)
        logger.info("Finished executing all applicable task queues")


class TaskTimeoutException(Exception):
    pass


class TaskQueueExecutor(threading.Thread):
    def __init__(
        self,
        task_queue: TaskQueue,
        openshift_client: OpenshiftClientInterface,
        lock: threading.Lock,
        progress_bar: Counter = None,
        p_bar_lock: threading.Lock = None,
        ignore_timeout: bool = False,
    ):
        super().__init__()

        self._task_queue = task_queue
        self._openshift_client = openshift_client
        self._lock = lock
        self._progress_bar = progress_bar
        self._p_bar_lock = p_bar_lock

        self._gfc_queue: Optional[QuerySet[File]] = None
        self._unzip_queue: Optional[QuerySet[File]] = None
        self._unpickle_queue: Optional[QuerySet[File]] = None
        self._ignore_timeout = ignore_timeout

    def run(self):
        logger.info("[%s] Starting task queue executor thread", self.ident)

        if not self._task_queue.has_started:
            self._task_queue.has_started = True
            self._task_queue.save()

        logger.info("[%s] Executing %s", self.ident, self._task_queue)
        self._execute()

        logger.info("[%s] Finished executing %s", self.ident, self._task_queue)

    def join(self, timeout=None):
        logger.info("[%s] Joining task queue executor thread", self.ident)
        super().join(timeout)

    def _has_unpopped_files(self):
        self._lock.acquire()
        return self._task_queue.has_unpopped_source_files

    def _execute(self):
        while self._has_unpopped_files():
            logger.debug(
                "[%s] Task queue has unpopped files, processing next",
                self.ident,
            )
            task_queue_source_file = self._task_queue.pop()
            self._lock.release()
            source_file = task_queue_source_file.source_file
            logger.info(
                "[%s] Processing source_file %s from task queue",
                self.ident,
                source_file,
            )

            # GFC
            gfc_files = File.objects.filter(file_path=source_file.file_path)
            for file in gfc_files:
                file.metric.start_time = now()
                file.metric.expected_duration_at_schedule_time = (
                    task_queue_source_file.expected_duration
                )
                file.metric.max_concurrency_at_execution_time = settings.get(
                    "MAX_CONCURRENT_PROCESSORS"
                )
                file.metric.save()
            try:
                self._process_files(
                    files=gfc_files,
                    processor=PipelineProcessor.SYNTHETIC_GFC,
                    metric=source_file.metric,
                )
            except TaskTimeoutException as err:
                logger.error("Task timed out: %s", err)
                continue

            # UNZIP
            unzip_files_from_source_file = File.objects.filter(
                source_file=source_file,
                state_code=FileStateCode.DOWNLOADED.code,
                process_step=FileProcessStep.NEW.code,
            )
            try:
                self._process_files(
                    files=unzip_files_from_source_file,
                    processor=PipelineProcessor.SYNTHETIC_UNZIP,
                    metric=source_file.metric,
                )
            except TaskTimeoutException as err:
                logger.error("Task timed out: %s", err)
                continue

            # UNPICKLE
            unpickle_files_from_source_file = File.objects.filter(
                source_file=source_file,
                state_code=FileStateCode.UNZIPPED.code,
                process_step=FileProcessStep.NEW.code,
            )
            try:
                self._process_files(
                    files=unpickle_files_from_source_file,
                    processor=PipelineProcessor.SYNTHETIC_UNPICKLE,
                    metric=source_file.metric,
                )
            except TaskTimeoutException as err:
                logger.error("Task timed out: %s", err)
                continue

            unzip_all_finished = all(
                file.process_step == FileProcessStep.FINISHED.code
                for file in unzip_files_from_source_file
            )
            unpickle_all_finished = all(
                file.process_step == FileProcessStep.FINISHED.code
                for file in unpickle_files_from_source_file
            )

            if unzip_all_finished and unpickle_all_finished:
                for file in gfc_files:
                    file.metric.end_time = now()
                    file.metric.save()

            if self._progress_bar and self._p_bar_lock:
                self._p_bar_lock.acquire(timeout=3)
                self._progress_bar.update()
                self._p_bar_lock.release()

            logger.debug(
                "[%s] Finished processing source_file %s from task queue",
                self.ident,
                source_file,
            )
        self._lock.release()
        logger.debug(
            "[%s] Task queue has no unpopped files, exiting", self.ident
        )

    def _process_files(
        self,
        files: QuerySet[File],
        processor: PipelineProcessor,
        metric: Metric,
    ):
        pod_identifier = uuid.uuid4()
        pod = Pod.objects.create(
            pod_identifier=pod_identifier,
            created_date=now(),
        )
        files.update(pod=pod)

        os_pod = self._openshift_client.run_pod_for_processor(
            processor, pod_identifier
        )

        metric_thread_return_val: list[Optional[list[KwhUsedAtReadTime]]] = [
            None
        ]
        gather_metrics_thread = threading.Thread(
            target=self._openshift_client.gather_pod_resource_consumption_statistics,
            args=(os_pod, metric_thread_return_val),
        )
        gather_metrics_thread.start()

        pod.name = os_pod.name
        pod.namespace = os_pod.namespace
        pod.ip = os_pod.ip
        pod.status = os_pod.status
        pod.labels = os_pod.labels
        pod.last_status_update = now()
        pod.save()

        # Allow for 2x the expected duration for the pods to finish, otherwise timeout
        timeout = (
            metric.start_time + metric.expected_duration_at_schedule_time * 2
        )

        pod_timeout_ignored_counter = {}

        assigned_files = files.filter(pod=pod)
        while not (
            all(
                file.process_step == FileProcessStep.FINISHED.code
                for file in assigned_files
            )
        ):
            if self._progress_bar and self._p_bar_lock:
                self._p_bar_lock.acquire(timeout=3)
                self._progress_bar.update(incr=0)
                self._p_bar_lock.release()
            if now() > timeout:
                if self._ignore_timeout:
                    ctr = pod_timeout_ignored_counter.setdefault(
                        pod_identifier, 0
                    )
                    ctr += 1
                    pod_timeout_ignored_counter[pod_identifier] = ctr

                    logger.warning(
                        "Task timed out, but ignoring timeout due to flag for "
                        "%s times before killing pod",
                        60 - ctr,
                    )

                    if ctr > 60:
                        self._openshift_client.delete_pod(os_pod, force=True)
                        files.update(
                            state_code=FileStateCode.ERROR.code,
                            process_step=FileProcessStep.FINISHED,
                        )
                        raise TaskTimeoutException(
                            f"Task timed out, pod with identifier {os_pod.pod_identifier} "
                            "did not finish in time"
                        )
                else:
                    self._openshift_client.delete_pod(os_pod, force=True)
                    files.update(
                        state_code=FileStateCode.ERROR.code,
                        process_step=FileProcessStep.FINISHED,
                    )
                    raise TaskTimeoutException(
                        f"Task timed out, pod with identifier {os_pod.pod_identifier} "
                        "did not finish in time"
                    )
            logger.debug(
                "[%s] Waiting for all files to be finished processing for pod %s",
                self.ident,
                os_pod.pod_identifier,
            )
            time.sleep(1)
            assigned_files = files.filter(pod=pod)

        logger.debug(
            "[%s] Waiting for metric gather tread to join for pod %s",
            self.ident,
            os_pod.pod_identifier,
        )
        gather_metrics_thread.join()
        logger.debug(
            "[%s] Finished gathering metrics for pod %s",
            self.ident,
            os_pod.pod_identifier,
        )
        kwh_used_measurements = metric_thread_return_val[0]
        if kwh_used_measurements:
            MetricKwhMeasurement.objects.bulk_create(
                [
                    MetricKwhMeasurement(
                        metric=metric,
                        read_time=measurement.read_time.datetime,
                        kwh=measurement.kwh_used,
                    )
                    for measurement in kwh_used_measurements
                ]
            )
        else:
            logger.error("Metric thread did not return a value")
