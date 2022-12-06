import arrow
import pytest

from entsoe_client import MockEntsoeApiClient
from entsoe_client.consts import PsrType
from entsoe_service import EntsoeService


@pytest.mark.parametrize(
    "starting_day",
    [
        "2023-05-10T13:30Z",
        "2023-05-10T13:45Z",
        "2023-05-10T14:00Z",
        "2023-05-11T00:00Z",
        "2023-05-09T00:00Z",
    ],
)
def test_get_wind_solar_last_data_available(starting_day):
    service = EntsoeService(entsoe_api_client=MockEntsoeApiClient())

    # Beware, this is based on the example_response_forecast_solar_wind.xml
    # file, which is read by the MockEntsoeApiClient instead of an actual call
    # to the ENTSOE API
    data = service.get_wind_solar_last_data_available(
        start_date=arrow.get(starting_day),
    )

    for psr_type, time_series in data.forecasted_generation.items():
        assert psr_type in [
            PsrType.WIND_ONSHORE,
            PsrType.SOLAR,
            PsrType.WIND_OFFSHORE,
        ]
        for point in time_series.points:
            # Check that no data gets added before the first point in the xml
            assert arrow.get("2023-05-09T22:00Z") <= point.datetime

            # Check that no data points are before the starting time
            assert point.datetime >= arrow.get(starting_day)

            # Check that no data gets added after the last point in the xml
            assert point.datetime <= arrow.get("2023-05-10T22:00Z")


@pytest.mark.parametrize(
    "starting_day",
    [
        "2023-05-10T13:30Z",
        "2023-05-10T13:45Z",
        "2023-05-10T14:00Z",
        "2023-05-11T00:00Z",
        "2023-05-09T00:00Z",
    ],
)
def test_get_renewable_percentage_last_available(starting_day):
    service = EntsoeService(entsoe_api_client=MockEntsoeApiClient())

    # Beware, this is based on the example_response_forecast_total_load.xml
    # file, which is read by the MockEntsoeApiClient instead of an actual call
    # to the ENTSOE API
    data = service.get_renewable_percentage_forecast_until_last_available(
        start_date=arrow.get(starting_day),
    )

    for point in data.forecasted_renewable_percentage:
        # Check that no data gets added before the first point in the xml
        assert arrow.get("2023-05-09T22:00Z") <= point.datetime

        # Check that no data points are before the starting time
        assert point.datetime >= arrow.get(starting_day)

        # Check that no data gets added after the last point in the xml
        assert point.datetime <= arrow.get("2023-05-10T22:00Z")
