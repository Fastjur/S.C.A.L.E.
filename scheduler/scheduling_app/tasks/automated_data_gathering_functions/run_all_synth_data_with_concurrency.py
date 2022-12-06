import logging
import os
import sys
import time

import enlighten
from django.db import close_old_connections

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
from ...models import File, Metric, Pod
from ...openshift import get_openshift_client

logger = logging.getLogger(__name__)

BY_DAY_FILES_DIR = os.path.join("synthetic", "synth-data", "BY_DAY_ZIPPED")
ALL_SYNTH_DATA_WITH_CONCURRENCY = os.path.join(
    "synthetic", "results", "all-synth-data-with-concurrency"
)
os.makedirs(ALL_SYNTH_DATA_WITH_CONCURRENCY, exist_ok=True)


def run_all_synth_data_with_concurrency():
    logger.info(
        get_pretty_banner(
            "Running all synthetic data with concurrency, day by day"
        )
    )

    if settings.MAX_CONCURRENT_PROCESSORS <= 1:
        logger.critical(
            "MAX_CONCURRENT_PROCESSORS should probably be greater than 1 for this test!"
        )
        sys.exit(1)

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
        base_dir=ALL_SYNTH_DATA_WITH_CONCURRENCY
    )

    with enlighten.get_manager() as manager:
        status = manager.status_bar(
            status_format="All synth data with concurrency tests.{fill}"
            "Stage: {stage}{fill}"
            "{elapsed}",
            justify=enlighten.Justify.CENTER,
            autorefresh=True,
            stage="Initial",
        )

        dirs = os.listdir(BY_DAY_FILES_DIR)
        dirs.sort()

        number_of_days = len(dirs)
        p_bar = manager.counter(total=number_of_days, unit="days")

        for day_dir in dirs:
            s3_resource.delete_all_files_in_bucket(settings.processing_bucket)
            s3_resource.delete_all_files_in_bucket(settings.pending_bucket)

            zip_files = os.listdir(os.path.join(BY_DAY_FILES_DIR, day_dir))
            zip_files.sort()
            for zip_file in zip_files:
                if zip_file.endswith(".zip"):
                    zip_file_path = os.path.join(
                        BY_DAY_FILES_DIR, day_dir, zip_file
                    )
                    with open(zip_file_path, "rb") as file_obj:
                        s3_resource.upload_fileobj(
                            file_obj,
                            bucket=settings.pending_bucket,
                            key=zip_file,
                        )
                else:
                    logger.warning("Skipping file %s", zip_file)
                    continue

            status.update(stage=f"Executing test for day {day_dir}")
            scheduler.determine_optimal_schedule()
            executor = QueueExecutor(openshift_client=get_openshift_client())

            p_bar.update(incr=0)
            executor.execute_task_queues(instantly=True, ignore_timeout=True)

            s3_resource.delete_all_files_in_bucket(settings.pending_bucket)
            s3_resource.delete_all_files_in_bucket(settings.processing_bucket)

            # Sleep for 5 sec to ensure all pods are fully stopped and removed
            time.sleep(5)

            close_old_connections()
            p_bar.update()

        df, df_kwh, df_files, df_pods = extract_all_data()

        df.to_csv(os.path.join(iteration_dir_name, "data.csv"))
        df_kwh.to_csv(os.path.join(iteration_dir_name, "kwh.csv"))
        df_files.to_csv(os.path.join(iteration_dir_name, "files.csv"))
        df_pods.to_csv(os.path.join(iteration_dir_name, "pods.csv"))

        s3_resource.delete_all_files_in_bucket(settings.pending_bucket)
        s3_resource.delete_all_files_in_bucket(settings.processing_bucket)

        File.objects.all().delete()
        Metric.objects.all().delete()
        Pod.objects.all().delete()
        scheduler.reset_queues()
