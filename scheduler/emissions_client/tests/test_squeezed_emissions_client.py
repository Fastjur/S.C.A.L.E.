from datetime import timedelta

from django.utils.timezone import now

from emissions_client.emissions_client import SqueezedEmissionsClient
from emissions_client.models import EmissionsPerKwhAtTime


def test_get_emissions_squeezed():
    client = SqueezedEmissionsClient(timeframe=timedelta(seconds=60 * 4))

    start = now()

    data = client.get_emissions_per_kwh(start_date=start)

    points = data.emissions_per_kwh_at_time
    assert len(points) == 96

    for i in range(0, 96):
        assert points[i].datetime == start + timedelta(
            seconds=(60 * 4) / 96 * i
        )

    assert points[0] == EmissionsPerKwhAtTime(
        datetime=start + timedelta(seconds=(60 * 4) / 96 * 0),
        carbon_intensity=441,
    )

    assert points[27] == EmissionsPerKwhAtTime(
        datetime=start + timedelta(seconds=(60 * 4) / 96 * 27),
        carbon_intensity=390,
    )

    assert points[56] == EmissionsPerKwhAtTime(
        datetime=start + timedelta(seconds=(60 * 4) / 96 * 56),
        carbon_intensity=299,
    )

    assert points[59] == EmissionsPerKwhAtTime(
        datetime=start + timedelta(seconds=(60 * 4) / 96 * 59),
        carbon_intensity=302,
    )

    assert points[95] == EmissionsPerKwhAtTime(
        datetime=start + timedelta(seconds=(60 * 4) / 96 * 95),
        carbon_intensity=446,
    )
