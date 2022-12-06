import logging

from config import settings
from .entsoe_api_client import (
    EntsoeApiClientInterface,
    MockEntsoeApiClient,
    EntsoeApiClient,
    SqueezedEntsoeApiClient,
)

logger = logging.getLogger(__name__)


def get_entsoe_api_client() -> EntsoeApiClientInterface:
    entsoe_api_client: EntsoeApiClientInterface
    mock_entsoe = settings.get("MOCK_ENTSOE_API_CLIENT", False)
    if mock_entsoe:
        logger.warning(
            "Mocking EntsoeApiClient, no calls will be made to ENTSOE, "
            "data is thus fake!"
        )
        if mock_entsoe == "squeezed":
            entsoe_api_client = SqueezedEntsoeApiClient()
        else:
            entsoe_api_client = MockEntsoeApiClient()
    else:
        entsoe_api_client = EntsoeApiClient()

    return entsoe_api_client
