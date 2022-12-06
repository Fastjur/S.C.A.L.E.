from datetime import timedelta

from django.utils.timezone import now

from entsoe_client.consts import PsrType
from entsoe_client.entsoe_api_client import SqueezedEntsoeApiClient
from entsoe_client.models import EnergyDataPoint


def test_get_wind_solar_day_ahead_squeezed():
    # Use squeezed client with a timeframe of 4 minutes to test the mapping to
    # the correct time series points
    client = SqueezedEntsoeApiClient(timeframe=timedelta(seconds=60 * 4))

    start = now()

    data = client.get_wind_solar_day_ahead(
        # End date not used in squeezed client
        start_date=start,
        end_date=None,
    )
    solar_points = data.forecasted_generation[PsrType.SOLAR].points

    assert len(solar_points) == 96

    for i in range(0, 96):
        assert solar_points[i].datetime == start + timedelta(
            seconds=(60 * 4) / 96 * i
        )

    assert solar_points[0] == EnergyDataPoint(
        datetime=start + timedelta(seconds=(60 * 4) / 96 * 0), value=0
    )

    assert solar_points[27] == EnergyDataPoint(
        datetime=start + timedelta(seconds=(60 * 4) / 96 * 27), value=966
    )

    assert solar_points[56] == EnergyDataPoint(
        datetime=start + timedelta(seconds=(60 * 4) / 96 * 56), value=3413
    )

    assert solar_points[59] == EnergyDataPoint(
        datetime=start + timedelta(seconds=(60 * 4) / 96 * 59), value=3120
    )

    assert solar_points[95] == EnergyDataPoint(
        datetime=start + timedelta(seconds=(60 * 4) / 96 * 95), value=0
    )


def test_get_wind_solar_day_ahead_squeezed_shorter_timeframe():
    # Use squeezed client with a timeframe of 4 minutes to test the mapping to
    # the correct time series points
    client = SqueezedEntsoeApiClient(timeframe=timedelta(seconds=60 * 2))

    start = now()

    data = client.get_wind_solar_day_ahead(
        # Start and end date not used in squeezed client
        start_date=start,
        end_date=None,
    )
    solar_points = data.forecasted_generation[PsrType.SOLAR].points

    assert len(solar_points) == 96

    for i in range(0, 96):
        assert solar_points[i].datetime == start + timedelta(
            seconds=(60 * 2) / 96 * i
        )

    assert solar_points[0] == EnergyDataPoint(
        datetime=start + timedelta(seconds=(60 * 2) / 96 * 0), value=0
    )

    assert solar_points[27] == EnergyDataPoint(
        datetime=start + timedelta(seconds=(60 * 2) / 96 * 27), value=966
    )

    assert solar_points[56] == EnergyDataPoint(
        datetime=start + timedelta(seconds=(60 * 2) / 96 * 56), value=3413
    )

    assert solar_points[59] == EnergyDataPoint(
        datetime=start + timedelta(seconds=(60 * 2) / 96 * 59), value=3120
    )

    assert solar_points[95] == EnergyDataPoint(
        datetime=start + timedelta(seconds=(60 * 2) / 96 * 95), value=0
    )
