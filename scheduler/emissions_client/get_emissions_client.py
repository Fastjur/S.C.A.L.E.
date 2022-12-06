import logging

from config import settings
from .emissions_client import (
    EmissionsClientInterface,
    SqueezedEmissionsClient,
    EmissionsClient,
)

logger = logging.getLogger(__name__)


def get_emissions_client() -> EmissionsClientInterface:
    emissions_client: EmissionsClientInterface
    mock_entsoe = settings.get("MOCK_ENTSOE_API_CLIENT", False)
    if mock_entsoe:
        logger.warning(
            "Mocking EmissionsClient, no calls will be made to ENTSOE, "
            "data is thus fake!"
        )
    if mock_entsoe == "squeezed":
        emissions_client = SqueezedEmissionsClient()
    else:
        emissions_client = EmissionsClient()

    return emissions_client
