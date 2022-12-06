import logging
import os
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
from .get_pretty_banner import (
    get_pretty_banner,
)
from ..execute_task_queues import QueueExecutor
from ...openshift import get_openshift_client

logger = logging.getLogger(__name__)

BY_DAY_FILES_DIR = os.path.join("synthetic", "synth-data", "BY_DAY_ZIPPED")
PROCESSING_SPEED_CONVERGING_RESULTS_DIR = os.path.join(
    "synthetic", "results", "get-processing-speed-converging"
)
os.makedirs(PROCESSING_SPEED_CONVERGING_RESULTS_DIR, exist_ok=True)


def get_processing_speed_converging():
    logger.info(get_pretty_banner("Processing speed converging"))

    logging.getLogger("s3transfer").setLevel(logging.INFO)
    logging.getLogger("boto3").setLevel(logging.INFO)
    logging.getLogger("botocore").setLevel(logging.INFO)

    # verify_db_empty()
    # verify_buckets_empty()

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
        base_dir=PROCESSING_SPEED_CONVERGING_RESULTS_DIR
    )

    with enlighten.get_manager() as manager:
        status = manager.status_bar(
            status_format="Running sequential tests to see how processing speed converges.{fill}"
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

                    status.update(stage=f"Executing test for day {zip_file}")
                    scheduler.determine_optimal_schedule()
                    executor = QueueExecutor(
                        openshift_client=get_openshift_client()
                    )
                    executor.execute_task_queues(
                        instantly=True, ignore_timeout=True
                    )

                    # Sleep for 5 sec to ensure all pods are fully stopped and removed
                    time.sleep(5)

                    close_old_connections()
                else:
                    logger.warning("Skipping file %s", zip_file)
                    continue

            p_bar.update()

        df, _, df_files, df_pods = extract_all_data()

        df.to_csv(os.path.join(iteration_dir_name, "data.csv"))
        df_files.to_csv(os.path.join(iteration_dir_name, "data_files.csv"))
        df_pods.to_csv(os.path.join(iteration_dir_name, "data_pods.csv"))
