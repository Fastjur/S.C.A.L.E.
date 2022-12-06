from arrow import Arrow

from entsoe_client.models import (
    DayAheadRenewablePercentageForecastData,
)
from entsoe_service import EntsoeServiceInterface


class MockEntsoeService(EntsoeServiceInterface):
    def __init__(self):
        self._mocked_renewable_percentage_forecast_until_last_available = None

    def set_mocked_renewable_percentage_forecast_until_last_available(
        self,
        renewable_percentage_forecast: DayAheadRenewablePercentageForecastData,
    ):
        self._mocked_renewable_percentage_forecast_until_last_available = (
            renewable_percentage_forecast
        )

    def get_renewable_percentage_forecast_until_last_available(
        self, start_date: Arrow
    ) -> DayAheadRenewablePercentageForecastData:
        return self._mocked_renewable_percentage_forecast_until_last_available
