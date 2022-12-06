import logging

from config import settings
from entsoe_client import get_entsoe_api_client
from entsoe_service import EntsoeService
from scheduler.celery import app as celery_app
from utils.s3_utils import S3Resource
from .automated_data_gathering_functions import (
    get_system_base_processing_speed,
    increasing_file_size,
    full_system_data_gathering,
    get_processing_speed_converging,
    run_all_synth_data_with_concurrency,
)
from .automated_data_gathering_functions.get_pretty_banner import (
    get_pretty_banner,
)
from ..models import File, Metric, Pod
from ..openshift import get_openshift_client

logger = logging.getLogger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **__):
    if settings.AUTOMATED_DATA_GATHERING:
        logger.warning(
            get_pretty_banner("Automated data gathering is enabled")
        )
        sender.add_periodic_task(
            settings.default_file_deadline_seconds,
            automated_data_gathering,
            name="automated_data_gathering_task",
        )
        automated_data_gathering.delay()


@celery_app.task(queue="automated_data_gathering_queue")
def automated_data_gathering():
    if not settings.default_file_deadline_seconds:
        logger.error(
            get_pretty_banner(
                "Skipping automated data gathering task "
                "as squeezed timeframe is not set (default_file_deadline_seconds)"
            )
        )
        return
    logger.info(get_pretty_banner("Running new automated data gathering set"))

    try:
        step = settings.AUTOMATED_DATA_GATHERING_STEP
        if step == "get-system-base-processing-speed":
            return get_system_base_processing_speed()

        if step == "increasing-file-size":
            return increasing_file_size()

        if step == "full-system-data-gathering":
            return full_system_data_gathering()

        if step == "get-processing-speed-converging":
            return get_processing_speed_converging()

        if step == "run-all-synth-data-with-concurrency":
            return run_all_synth_data_with_concurrency()
    except Exception as e:
        logger.exception(
            get_pretty_banner(
                f"Automated data gathering failed with exception {e}"
            )
        )

        s3_resource = S3Resource()
        s3_resource.delete_all_files_in_bucket(settings.pending_bucket)
        s3_resource.delete_all_files_in_bucket(settings.processing_bucket)

        File.objects.all().delete()
        Metric.objects.all().delete()
        Pod.objects.all().delete()

        from . import Scheduler

        scheduler = Scheduler(
            entsoe_service=EntsoeService(get_entsoe_api_client()),
            openshift_client=get_openshift_client(),
            s3_resource=S3Resource(),
        )
        scheduler.reset_queues()

        raise e

    raise ValueError("Invalid AUTOMATED_DATA_GATHERING_STEP: " f"{step}")
