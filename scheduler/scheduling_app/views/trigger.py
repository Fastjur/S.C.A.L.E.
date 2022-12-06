import logging

from django.http import HttpResponse
from django.utils.timezone import now

from config import settings
from entsoe_client import get_entsoe_api_client
from entsoe_service import EntsoeService
from scheduling_app.models import File, Pod, TaskQueue
from scheduling_app.openshift import get_openshift_client
from scheduling_app.tasks import Scheduler, update_pod_status
from scheduling_app.tasks.automated_data_gathering_functions.extract_all_data import (
    extract_all_data,
)
from scheduling_app.tasks.execute_task_queues import (
    QueueExecutor,
)
from scheduling_app.views import task_queues
from utils.FileStates import FileStateCode, FileProcessStep, PipelineProcessor
from utils.s3_utils import S3Resource

logger = logging.getLogger(__name__)


def trigger2(_):
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
    # Remove all files not in pending
    File.objects.exclude(state_code=FileStateCode.PENDING).delete()

    # Cleanup all pods
    Pod.objects.all().delete()

    # Clean processing bucket
    s3_resource = S3Resource()
    s3_resource.delete_all_files_in_bucket(settings.pending_bucket)
    s3_resource.delete_all_files_in_bucket(settings.processing_bucket)

    # Reset all pending files to new
    for file in File.objects.filter(state_code=FileStateCode.PENDING):
        file.process_step = FileProcessStep.NEW.code
        file.created_at = now()
        file.deadline = None
        file.save()

    scheduler = Scheduler(
        entsoe_service=EntsoeService(get_entsoe_api_client()),
        openshift_client=openshift_client,
        s3_resource=S3Resource(),
    )
    scheduler.reset_queues()

    TaskQueue.objects.all().delete()

    return task_queues(_)


def trigger3(_):
    update_pod_status()
    scheduler = Scheduler(
        entsoe_service=EntsoeService(get_entsoe_api_client()),
        openshift_client=get_openshift_client(),
        s3_resource=S3Resource(),
    )
    scheduler.determine_optimal_schedule()

    return task_queues(_)


def trigger4(_):
    executor = QueueExecutor(openshift_client=get_openshift_client())
    executor.execute_task_queues(instantly=True)

    return task_queues(_)


def extract_all_data_view(_):
    df, df2, df3, df4 = extract_all_data()
    now_string = now().strftime("%Y-%m-%d_%H-%M-%S")
    df.to_csv(f"{now_string}-data.csv")
    df2.to_csv(f"{now_string}-data_kwh.csv")
    df3.to_csv(f"{now_string}-data_files.csv")
    df4.to_csv(f"{now_string}-data_pods.csv")

    return HttpResponse("Done")
