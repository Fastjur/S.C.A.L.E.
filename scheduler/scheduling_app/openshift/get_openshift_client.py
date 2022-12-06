import logging

from config import settings
from .docker_client import DockerClient
from .mock_client import MockOpenshiftClient
from .openshift_client import (
    OpenshiftClientInterface,
    OpenshiftClient,
)

logger = logging.getLogger(__name__)


def get_openshift_client() -> OpenshiftClientInterface:
    openshift_client: OpenshiftClientInterface
    if settings.mock_openshift:
        logger.warning(
            "Mocking OpenshiftClient, no calls will be made to Openshift!"
        )
        if settings.mock_openshift == "docker":
            openshift_client = DockerClient()
        else:
            openshift_client = MockOpenshiftClient()
    else:
        openshift_client = OpenshiftClient(settings.openshift_namespace)

    return openshift_client
