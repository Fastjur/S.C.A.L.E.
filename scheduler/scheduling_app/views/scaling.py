import logging

from scheduling_app.openshift import get_openshift_client
from scheduling_app.tasks import update_pod_status
from scheduling_app.views import PodViewSet
from utils.FileStates import PipelineProcessor

logger = logging.getLogger(__name__)


def scale_pipeline_processor(request, processor_str: str, replicas: int):
    logger.info(
        "Received request to scale %s to: %i",
        processor_str,
        replicas,
    )
    processor = PipelineProcessor.from_code(processor_str)

    openshift_client = get_openshift_client()
    openshift_client.scale_pipeline_processor(
        processor=processor, replicas=replicas
    )
    update_pod_status.apply()
    # Redirect to pods view
    return PodViewSet.as_view({"get": "list"})(request)
