import logging
import os
import tempfile
import time

import enlighten

from config import settings
from entsoe_client import get_entsoe_api_client
from entsoe_service import EntsoeService
from random_file_creator import RandomFileCreator
from scheduling_app.models import File, Pod, Metric
from scheduling_app.openshift import get_openshift_client
from utils.FileStates import PipelineProcessor
from utils.s3_utils import S3Resource
from .extract_all_data import extract_all_data
from .get_iteration_dir import get_iteration_dir
from .get_pretty_banner import get_pretty_banner
from .verify_buckets_empty import verify_buckets_empty
from .verify_db_empty import verify_db_empty
from ..create_schedule import Scheduler
from ..execute_task_queues import QueueExecutor

logger = logging.getLogger(__name__)

BASE_PROCESSING_SPEED_RESULTS_DIR = os.path.join(
    "synthetic", "results", "base-processing-speed"
)
GET_SYSTEM_BASE_PROCESSING_SPEED_NUM_FILES = 100
MIN_NUM_PICKLES = 1
MAX_NUM_PICKLES = 3


def get_system_base_processing_speed():
    logger.info(get_pretty_banner("Getting system base processing speed"))

    logging.getLogger("s3transfer").setLevel(logging.INFO)
    logging.getLogger("boto3").setLevel(logging.INFO)
    logging.getLogger("botocore").setLevel(logging.INFO)

    verify_db_empty()
    verify_buckets_empty()

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

    scheduler = Scheduler(
        entsoe_service=EntsoeService(get_entsoe_api_client()),
        openshift_client=openshift_client,
        s3_resource=S3Resource(),
    )

    with enlighten.get_manager() as manager:
        status = manager.status_bar(
            status_format="Getting system base processing speed.{fill}"
            "Stage: {stage}{fill}"
            "{elapsed}",
            justify=enlighten.Justify.CENTER,
            autorefresh=True,
            stage="Initial",
        )
        with tempfile.TemporaryDirectory() as tmp_dir:
            logger.debug("Temporary directory: %s", tmp_dir)
            tmp_dir_files_dir = os.path.join(tmp_dir, "files")
            if settings.AUTOMATED_DATA_GATHERING_USE_PRE_CREATED_FILES:
                logger.warning(
                    "Using pre-created files, skipping creation of random files"
                )
                os.makedirs(tmp_dir_files_dir)
                for file in os.listdir(
                    settings.AUTOMATED_DATA_GATHERING_PRE_CREATED_FILES_DIR
                ):
                    os.symlink(
                        os.path.join(
                            os.getcwd(),
                            settings.AUTOMATED_DATA_GATHERING_PRE_CREATED_FILES_DIR,
                            file,
                        ),
                        os.path.join(tmp_dir_files_dir, file),
                    )
            else:
                random_file_creator = RandomFileCreator(tmp_dir)
                status.update(stage="Creating random files")
                random_file_bar = manager.counter(
                    total=GET_SYSTEM_BASE_PROCESSING_SPEED_NUM_FILES,
                    unit="random files",
                )
                for _ in range(GET_SYSTEM_BASE_PROCESSING_SPEED_NUM_FILES):
                    random_file_creator.create_random_file(
                        MIN_NUM_PICKLES, MAX_NUM_PICKLES
                    )
                    random_file_bar.update()
                random_file_bar.close()
            random_files = os.listdir(tmp_dir_files_dir)

            if not random_files:
                raise ValueError(
                    "No random files found! Either rewrite code to use pre-created files "
                    "or validate that random files are being created correctly"
                )

            logger.info("Random files: %s", random_files)

            # Upload random files to pending bucket
            s3_resource = S3Resource()
            status.update(stage="Uploading files to pending bucket")
            upload_bar = manager.counter(
                total=len(random_files),
                unit="upload files",
            )
            for random_file in random_files:
                with open(
                    os.path.join(tmp_dir, "files", random_file), "rb"
                ) as file_obj:
                    s3_resource.upload_fileobj(
                        file_obj,
                        bucket=settings.pending_bucket,
                        key=random_file,
                    )
                upload_bar.update()
            upload_bar.close()

            scheduler.determine_optimal_schedule()

            status.update(stage="Executing task queues")
            executor = QueueExecutor(openshift_client=get_openshift_client())
            executor.execute_task_queues(instantly=True, manager=manager)

            df, _, df_files, df_pods = extract_all_data()

            median_processing_speed = (
                scheduler._determine_median_processing_speed()
            )
            logger.info("Median processing speed: %s", median_processing_speed)

            iteration_dir_name = get_iteration_dir(
                base_dir=BASE_PROCESSING_SPEED_RESULTS_DIR
            )
            with open(
                f"{iteration_dir_name}/median_processing_speed.txt",
                "w",
                encoding="UTF-8",
            ) as file_obj:
                file_obj.write(str(median_processing_speed))

            df.to_csv(os.path.join(iteration_dir_name, "data.csv"))
            df_files.to_csv(os.path.join(iteration_dir_name, "data_files.csv"))
            df_pods.to_csv(os.path.join(iteration_dir_name, "data_pods.csv"))

            # Clean buckets
            s3_resource.delete_all_files_in_bucket(settings.processing_bucket)
            s3_resource.delete_all_files_in_bucket(settings.pending_bucket)

            File.objects.all().delete()
            Metric.objects.all().delete()
            Pod.objects.all().delete()
            scheduler.reset_queues()

            time.sleep(1)
