import logging
import os
from datetime import timedelta

import enlighten
from django.db import close_old_connections
from django.utils.timezone import now

from config import settings
from entsoe_client import get_entsoe_api_client
from entsoe_service import EntsoeService
from utils.FileStates import PipelineProcessor
from utils.s3_utils import S3Resource
from .extract_all_data import extract_all_data
from .get_iteration_dir import get_iteration_dir
from .get_pretty_banner import get_pretty_banner
from .verify_buckets_empty import verify_buckets_empty
from .verify_db_empty import verify_db_empty
from ..execute_task_queues import QueueExecutor
from ...models import File, Metric, Pod, TaskQueue
from ...openshift import get_openshift_client

logger = logging.getLogger(__name__)

BY_DAY_FILES_DIR = os.path.join("synthetic", "synth-data", "BY_DAY_ZIPPED")
FULL_SYSTEM_DATA_GATHERING_RESULTS_DIR = os.path.join(
    "synthetic", "results", "full-system-data-gathering"
)
os.makedirs(FULL_SYSTEM_DATA_GATHERING_RESULTS_DIR, exist_ok=True)


def _upload_file_to_s3(
    day_dir: str,
    zip_file: str,
):
    s3_resource = S3Resource()
    with open(
        os.path.join(BY_DAY_FILES_DIR, day_dir, zip_file), "rb"
    ) as file_obj:
        s3_resource.upload_fileobj(
            file_obj,
            bucket=settings.pending_bucket,
            key=zip_file,
        )


def _run_test_without_scheduler(scheduler):
    old_max_concurrency = settings.get("MAX_CONCURRENT_PROCESSORS")
    settings.MAX_CONCURRENT_PROCESSORS = 1

    scheduler.determine_optimal_schedule()

    executor = QueueExecutor(openshift_client=get_openshift_client())
    executor.execute_task_queues(instantly=True, ignore_timeout=False)

    close_old_connections()

    settings.MAX_CONCURRENT_PROCESSORS = old_max_concurrency


def _run_test_using_scheduler(scheduler) -> timedelta:
    scheduler.determine_optimal_schedule()

    task_queues = TaskQueue.objects.filter(
        files__is_popped=False,
    ).distinct()
    if len(task_queues) != 1:
        raise ValueError(
            "There should be exactly one task queue with unpopped files"
        )
    task_queue = task_queues[0]
    start_time_in = task_queue.start_time - now()
    if start_time_in <= timedelta():
        raise ValueError("Task queue should not be starting in the past!")

    logger.info(
        "The scheduler would have waited %s, executing immediately",
        start_time_in,
    )

    executor = QueueExecutor(openshift_client=get_openshift_client())
    executor.execute_task_queues(instantly=True, ignore_timeout=False)
    return start_time_in


def full_system_data_gathering():
    logger.info(get_pretty_banner("Testing system CO2 reduction"))

    logging.getLogger("s3transfer").setLevel(logging.INFO)
    logging.getLogger("boto3").setLevel(logging.INFO)
    logging.getLogger("botocore").setLevel(logging.INFO)

    verify_db_empty()
    verify_buckets_empty()

    # Imported here to avoid circular import
    from .. import Scheduler

    openshift_client = get_openshift_client()
    scheduler = Scheduler(
        entsoe_service=EntsoeService(get_entsoe_api_client()),
        openshift_client=openshift_client,
        s3_resource=S3Resource(),
    )

    openshift_client = get_openshift_client()
    openshift_client.scale_pipeline_processor(
        processor=PipelineProcessor.SYNTHETIC_GFC, replicas=0
    )
    openshift_client.scale_pipeline_processor(
        processor=PipelineProcessor.SYNTHETIC_UNZIP, replicas=0
    )
    openshift_client.scale_pipeline_processor(
        processor=PipelineProcessor.SYNTHETIC_UNPICKLE, replicas=0
    )

    s3_resource = S3Resource()

    iteration_dir_name = get_iteration_dir(
        base_dir=FULL_SYSTEM_DATA_GATHERING_RESULTS_DIR
    )

    first_run = True

    with enlighten.get_manager() as manager:
        status = manager.status_bar(
            status_format="CO2 reduction tests.{fill}"
            "Stage: {stage}{fill}"
            "{elapsed}",
            justify=enlighten.Justify.CENTER,
            autorefresh=True,
            stage="Initial",
        )

        dirs = os.listdir(BY_DAY_FILES_DIR)
        dirs.sort()

        pbar = manager.counter(
            total=len(dirs),
            unit="days",
        )
        for day_dir in dirs:
            zip_files = os.listdir(os.path.join(BY_DAY_FILES_DIR, day_dir))
            zip_files.sort()
            for zip_file in zip_files:
                if not zip_file.endswith(".zip"):
                    logger.warning("Skipping non-zip file: %s", zip_file)
                    continue
                status.update(stage=f"Uploading zip file {zip_file} to S3")
                _upload_file_to_s3(day_dir, zip_file)

            status.update(stage=f"Running test without scheduler {day_dir}")
            _run_test_without_scheduler(scheduler)

            (
                without_scheduler_df,
                without_scheduler_kwh_df,
                without_scheduler_files_df,
                without_scheduler_pods_df,
            ) = extract_all_data()
            without_scheduler_df.to_csv(
                os.path.join(iteration_dir_name, "without_scheduler.csv"),
                mode="a",
                header=first_run,
            )
            without_scheduler_kwh_df.to_csv(
                os.path.join(iteration_dir_name, "without_scheduler_kwh.csv"),
                mode="a",
                header=first_run,
            )
            without_scheduler_files_df.to_csv(
                os.path.join(
                    iteration_dir_name, "without_scheduler_files.csv"
                ),
                mode="a",
                header=first_run,
            )
            without_scheduler_pods_df.to_csv(
                os.path.join(iteration_dir_name, "without_scheduler_pods.csv"),
                mode="a",
                header=first_run,
            )

            s3_resource.delete_all_files_in_bucket(settings.pending_bucket)
            s3_resource.delete_all_files_in_bucket(settings.processing_bucket)

            File.objects.all().delete()
            Metric.objects.all().delete()
            Pod.objects.all().delete()
            scheduler.reset_queues()

            for zip_file in zip_files:
                if not zip_file.endswith(".zip"):
                    logger.warning("Skipping non-zip file: %s", zip_file)
                    continue
                status.update(stage=f"Uploading zip file {zip_file} to S3")
                _upload_file_to_s3(day_dir, zip_file)

            status.update(
                stage=f"Running test using the scheduler ({zip_file})"
            )
            execution_earlier_timedelta = _run_test_using_scheduler(scheduler)

            (
                with_scheduler_df,
                with_scheduler_kwh_df,
                with_scheduler_files_df,
                with_scheduler_pods_df,
            ) = extract_all_data()

            with_scheduler_df["start_time"] = (
                with_scheduler_df["start_time"] + execution_earlier_timedelta
            )
            with_scheduler_df["end_time"] = (
                with_scheduler_df["end_time"] + execution_earlier_timedelta
            )
            with_scheduler_df.to_csv(
                os.path.join(iteration_dir_name, "with_scheduler.csv"),
                mode="a",
                header=first_run,
            )

            with_scheduler_kwh_df["read_time"] = (
                with_scheduler_kwh_df["read_time"]
                + execution_earlier_timedelta
            )
            with_scheduler_kwh_df.sort_values("read_time", inplace=True)
            with_scheduler_kwh_df.to_csv(
                os.path.join(iteration_dir_name, "with_scheduler_kwh.csv"),
                mode="a",
                header=first_run,
            )

            with_scheduler_files_df["created_date"] = (
                with_scheduler_files_df["created_date"]
                + execution_earlier_timedelta
            )
            with_scheduler_files_df["deadline"] = (
                with_scheduler_files_df["deadline"]
                + execution_earlier_timedelta
            )
            with_scheduler_files_df.to_csv(
                os.path.join(
                    iteration_dir_name, "without_scheduler_files.csv"
                ),
                mode="a",
                header=first_run,
            )

            with_scheduler_pods_df["created_date"] = (
                with_scheduler_pods_df["created_date"]
                + execution_earlier_timedelta
            )
            with_scheduler_pods_df["last_status_update"] = (
                with_scheduler_pods_df["last_status_update"]
                + execution_earlier_timedelta
            )
            with_scheduler_pods_df.to_csv(
                os.path.join(iteration_dir_name, "without_scheduler_pods.csv"),
                mode="a",
                header=first_run,
            )

            s3_resource.delete_all_files_in_bucket(settings.pending_bucket)
            s3_resource.delete_all_files_in_bucket(settings.processing_bucket)

            File.objects.all().delete()
            Metric.objects.all().delete()
            Pod.objects.all().delete()
            scheduler.reset_queues()

            first_run = False

            pbar.update()

    logger.info(get_pretty_banner("Finished running tests"))
