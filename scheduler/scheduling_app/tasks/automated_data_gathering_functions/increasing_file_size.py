import logging
import os
import tempfile
import time

import enlighten
from django.db import close_old_connections
from enlighten import Manager, StatusBar

from config import settings
from entsoe_client import get_entsoe_api_client
from entsoe_service import EntsoeService
from random_file_creator import RandomFileCreator
from scheduling_app.models import File, Pod, Metric
from utils.FileStates import PipelineProcessor
from utils.s3_utils import S3Resource
from .extract_all_data import extract_all_data
from .get_iteration_dir import get_iteration_dir
from .get_pretty_banner import get_pretty_banner
from .verify_buckets_empty import verify_buckets_empty
from .verify_db_empty import verify_db_empty
from ..execute_task_queues import QueueExecutor
from ...openshift import get_openshift_client

logger = logging.getLogger(__name__)

INCREASING_FILE_SIZE_RESULTS_DIR = os.path.join(
    "synthetic", "results", "increasing-file-size"
)

PICKLES_IN_ORDER_OF_INCREASING_SIZE = [
    "bmkibler.pkl",
    "sacriel.pkl",
    "savjz.pkl",
    "p4wnyhof.pkl",
    "followgrubby.pkl",
    "kingrichard.pkl",
    "grimmmz.pkl",
    "tfue.pkl",
    "iwilldominate.pkl",
    "scarra.pkl",
    "kinggothalion.pkl",
    "tsm_viss.pkl",
    "c9sneaky.pkl",
    "chocotaco.pkl",
    "aimbotcalvin.pkl",
    "cryaotic.pkl",
    "xchocobars.pkl",
    "voyboy.pkl",
    "shiphtur.pkl",
    "highdistortion.pkl",
    "dakotaz.pkl",
    "tsm_myth.pkl",
    "quin69.pkl",
    "goldglove.pkl",
    "drlupo.pkl",
    "thijshs.pkl",
    "timthetatman.pkl",
    "joshog.pkl",
    "giantwaffle.pkl",
    "tsm_hamlinz.pkl",
    "summit1g.pkl",
    "disguisedtoasths.pkl",
    "sypherpk.pkl",
    "imaqtpie.pkl",
    "dafran.pkl",
    "nickmercs.pkl",
    "b0aty.pkl",
    "admiralbulldog.pkl",
    "dansgaming.pkl",
    "cohhcarnage.pkl",
    "maximilian_dood.pkl",
    "singsing.pkl",
    "loltyler1.pkl",
    "xqcow.pkl",
    "nl_kripp.pkl",
    "admiralbahroo.pkl",
    "forsen.pkl",
    "ninja.pkl",
    "moonmoon_ow.pkl",
    "lirik.pkl",
    "shroud.pkl",
    # Below is probably too heavy for a 32Gb system
    # "sodapoppin.pkl",
]

TESTS_PER_NUM_PICKLES = 12


def increasing_file_size():
    logger.info(
        get_pretty_banner(
            "Running files through pipeline with ever more pickle files added"
        )
    )

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

    with enlighten.get_manager() as manager:
        status = manager.status_bar(
            status_format="Running tests with increasing file sizes.{fill}"
            "Stage: {stage}{fill}"
            "{elapsed}",
            justify=enlighten.Justify.CENTER,
            autorefresh=True,
            stage="Initial",
        )
        pickle_bar = manager.counter(
            total=len(PICKLES_IN_ORDER_OF_INCREASING_SIZE),
            unit="pickle files",
        )
        for pickle_file_name in PICKLES_IN_ORDER_OF_INCREASING_SIZE:
            _run_test(
                scheduler, s3_resource, manager, status, pickle_file_name
            )
            pickle_bar.update()
        pickle_bar.close()

    df, _ = extract_all_data()
    iteration_dir_name = get_iteration_dir(
        base_dir=INCREASING_FILE_SIZE_RESULTS_DIR
    )

    df.to_csv(os.path.join(iteration_dir_name, "data.csv"))

    # Clean buckets
    s3_resource.delete_all_files_in_bucket(settings.processing_bucket)
    s3_resource.delete_all_files_in_bucket(settings.pending_bucket)

    File.objects.all().delete()
    Metric.objects.all().delete()
    Pod.objects.all().delete()
    scheduler.reset_queues()

    time.sleep(1)


def _run_test(
    scheduler,
    s3_resource,
    manager: Manager,
    status: StatusBar,
    pickle_file_name: str,
):
    with tempfile.TemporaryDirectory() as tmp_dir:
        logger.debug("Temporary directory: %s", tmp_dir)
        random_file_creator = RandomFileCreator(save_dir=tmp_dir)

        status.update(stage="Creating random files")
        random_file_bar = manager.counter(
            total=TESTS_PER_NUM_PICKLES,
            unit="random files",
            leave=False,
        )
        for _ in range(TESTS_PER_NUM_PICKLES):
            random_file_creator.create_file_with_given_pickle_names(
                pickle_file_names=[pickle_file_name]
            )
            random_file_bar.update()
        random_file_bar.close()

        random_files = os.listdir(os.path.join(tmp_dir, "files"))

        if not random_files:
            raise ValueError(
                "No random files found! Either rewrite code to use pre-created files "
                "or validate that random files are being created correctly"
            )

        logger.info("Random files: %s", random_files)

        # Upload random files to pending bucket
        status.update(stage="Uploading files to pending bucket")
        upload_bar = manager.counter(
            total=len(random_files),
            unit="upload files",
            leave=False,
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

        status.update(stage="Determining optimal schedule")
        scheduler.determine_optimal_schedule()

        status.update(stage="Executing task queues")
        executor = QueueExecutor(openshift_client=get_openshift_client())
        executor.execute_task_queues(instantly=True)

        s3_resource.delete_all_files_in_bucket(settings.processing_bucket)
        s3_resource.delete_all_files_in_bucket(settings.pending_bucket)

        close_old_connections()
