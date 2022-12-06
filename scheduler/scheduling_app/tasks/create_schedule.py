import logging
import statistics

import arrow
import pandas as pd
from django.db.models import QuerySet
from django.utils.timezone import now, timedelta

from config import settings
from emissions_client import get_emissions_client
from emissions_client.emissions_client import EmissionsClientInterface
from entsoe_client import get_entsoe_api_client
from entsoe_service import EntsoeServiceInterface, EntsoeService
from scheduler.celery import app as celery_app
from scheduling_app.models import (
    File,
    Metric,
    TaskQueue,
    TaskQueueSourceFile,
)
from scheduling_app.openshift import (
    OpenshiftClientInterface,
    get_openshift_client,
)
from utils.FileStates import FileStateCode, FileProcessStep
from utils.s3_utils import S3ResourceInterface, S3Resource

logger = logging.getLogger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **_):
    if not settings.AUTOMATED_DATA_GATHERING:
        sender.add_periodic_task(
            settings.create_schedule_interval,
            create_schedule_task,
            name="create_schedule_task",
        )


class Scheduler:
    SLIDING_WINDOW_TIMEDELTA = timedelta(days=30)
    SLIDING_WINDOW_DATE_START_DATE = now() - SLIDING_WINDOW_TIMEDELTA

    @classmethod
    def reset_queues(cls):
        logger.warning("Resetting queues, any data in them is lost")
        queues = TaskQueue.objects.all()
        logger.debug("Old queues: %s", queues)
        queues.delete()

    def __init__(
        self,
        entsoe_service: EntsoeServiceInterface,
        openshift_client: OpenshiftClientInterface,
        s3_resource: S3ResourceInterface,
    ):
        self._entsoe_service = entsoe_service
        self._openshift_client = openshift_client
        self._s3_resource = s3_resource

    def get_pending_files_and_update_db(self):
        logger.info("Running get_pending_files_and_update_db task")
        # Get files in S3 in pending bucket
        s3_files = self._s3_resource.list_all_files(settings.pending_bucket)

        for s3_file in s3_files:
            file_bucket = s3_file.bucket_name
            file_key = s3_file.key
            file, created = File.objects.get_or_create(
                file_path=f"{file_bucket}/{file_key}",
                file_size=s3_file.size,
                defaults={
                    "state_code": FileStateCode.PENDING.code,
                    "process_step": FileProcessStep.NEW.code,
                    "created_date": now(),
                },
            )
            if created:
                logger.info("Created new file %s", file)
            else:
                logger.info(
                    "File %s already exists, "
                    "but is not moved out of pending bucket yet",
                    file,
                )
            try:
                metric = file.metric
                logger.debug("File %s already has a metric: %s", file, metric)
            except File.metric.RelatedObjectDoesNotExist:
                metric = Metric.objects.create(
                    source_file=file,
                )
                logger.info("Created new metric %s for file %s", metric, file)

    def determine_optimal_schedule(
        self, filename_to_save_forecast_to: str = None
    ):
        """
        Determines the optimal schedule for the files in the pending bucket
        :param filename_to_save_forecast_to: Debug only parameter, this is used to save
        the forecast to a file when running the automated data gathering.
        :return:
        """
        logger.info("Determining optimal schedule")
        self.get_pending_files_and_update_db()

        pending_source_files = Scheduler._get_pending_source_files()
        if len(pending_source_files) <= 0:
            # Nothing to do, nothing is pending
            logger.debug("Nothing to do, no pending source files")
            return

        median_speed = self._determine_median_processing_speed()
        logger.debug("Median processing speed: %s B/s", median_speed)
        expected_total_duration = (
            timedelta(
                seconds=sum(
                    file.file_size / median_speed
                    for file in pending_source_files
                )
            )
            / settings.MAX_CONCURRENT_PROCESSORS
        )
        logger.debug("Expected total duration: %s", expected_total_duration)
        start_date = arrow.get(now())
        renewable_percentage_forecast = self._entsoe_service.get_renewable_percentage_forecast_until_last_available(
            start_date=start_date,
        )

        if (
            settings.MOCK_ENTSOE_API_CLIENT == "squeezed"
            and filename_to_save_forecast_to
        ):
            emissions_client = get_emissions_client()
            emissions = emissions_client.get_emissions_per_kwh(
                start_date=start_date,
            )
            emissions_df = pd.DataFrame(
                data=[
                    {
                        "datetime": point.datetime,
                        EmissionsClientInterface.CARBON_INTENSITY_COL_NAME: point.carbon_intensity,
                    }
                    for point in emissions.emissions_per_kwh_at_time
                ]
            )
            emissions_df.to_csv(filename_to_save_forecast_to, index=False)

        highest_renewable_percentage = (
            renewable_percentage_forecast.get_highest_renewable_percentage()
        )
        logger.debug(
            "Highest renewable percentage: %s", highest_renewable_percentage
        )
        first_file_start = (
            highest_renewable_percentage.datetime - expected_total_duration / 2
        )
        logger.debug("First file start: %s", first_file_start)
        task_queue = TaskQueue.objects.create(
            start_time=first_file_start.datetime,
        )
        self._map_to_task_queue_files(
            pending_files=pending_source_files,
            median_processing_speed=median_speed,
            task_queue=task_queue,
        )

    @staticmethod
    def _get_pending_source_files() -> QuerySet[File]:
        files = File.objects.filter(
            state_code=FileStateCode.PENDING.code,
            process_step=FileProcessStep.NEW.code,
        )
        logger.info("Found %i files to be processed", len(files))
        logger.debug("Pending files: %s", files)
        return files

    def _determine_median_processing_speed(self) -> float:
        logger.info(
            "Considering metrics after %s",
            self.SLIDING_WINDOW_DATE_START_DATE,
        )
        metrics = Metric.objects.filter(
            start_time__isnull=False,
            end_time__isnull=False,
            start_time__gt=self.SLIDING_WINDOW_DATE_START_DATE,
        )
        if len(metrics) <= 0:
            logger.warning(
                "No metrics found, returning %i B/s",
                settings.NO_DATA_DEFAULT_PROCESSING_SPEED,
            )
            return settings.NO_DATA_DEFAULT_PROCESSING_SPEED
        logger.info("Found %i metrics", len(metrics))
        logger.debug("Metrics: %s", metrics)
        processing_speeds = [metric.processing_speed for metric in metrics]
        median_speed = statistics.median(processing_speeds)
        logger.info("Median processing speed: %s B/s", median_speed)
        return median_speed

    def _map_to_task_queue_files(
        self,
        pending_files: QuerySet[File],
        median_processing_speed: float,
        task_queue: TaskQueue,
    ) -> list[TaskQueueSourceFile]:
        res: list[TaskQueueSourceFile] = []
        for file in pending_files:
            expected_duration = timedelta(
                seconds=file.file_size / median_processing_speed
            )
            task_queue_source_file = TaskQueueSourceFile.objects.create(
                task_queue=task_queue,
                source_file=file,
                expected_duration=expected_duration,
            )
            file.process_step = FileProcessStep.SCHEDULED.code
            file.save()
            res.append(task_queue_source_file)
        return res


@celery_app.task(queue="create_schedule_queue")
def create_schedule_task():
    scheduler = Scheduler(
        entsoe_service=EntsoeService(get_entsoe_api_client()),
        openshift_client=get_openshift_client(),
        s3_resource=S3Resource(),
    )
    scheduler.determine_optimal_schedule()
