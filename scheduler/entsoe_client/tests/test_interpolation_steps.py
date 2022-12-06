import arrow

from entsoe_client.models import EnergyDataPoint, TimeSeries


def test_timeseries_interpolation():
    time_series = TimeSeries(
        psr_type=None,
        business_type=None,
        resolution=None,
        points=[
            EnergyDataPoint(
                arrow.get(point[0]),
                point[1],
            )
            for point in [
                ["2023-05-20 10:00", 10],
                ["2023-05-20 11:00", 22],
                ["2023-05-20 12:00", 46],
            ]
        ],
    )

    interpolated_ts = time_series.interpolate_points(
        start_datetime=arrow.get("2023-05-20 10:00"),
        end_datetime=arrow.get("2023-05-20 12:00"),
        step_size_minutes=5,
    )

    expected = [
        EnergyDataPoint(
            arrow.get(point[0]),
            point[1],
        )
        for point in [
            ["2023-05-20 10:00", 10],
            ["2023-05-20 10:05", 11],
            ["2023-05-20 10:10", 12],
            ["2023-05-20 10:15", 13],
            ["2023-05-20 10:20", 14],
            ["2023-05-20 10:25", 15],
            ["2023-05-20 10:30", 16],
            ["2023-05-20 10:35", 17],
            ["2023-05-20 10:40", 18],
            ["2023-05-20 10:45", 19],
            ["2023-05-20 10:50", 20],
            ["2023-05-20 10:55", 21],
            ["2023-05-20 11:00", 22],
            ["2023-05-20 11:05", 24],
            ["2023-05-20 11:10", 26],
            ["2023-05-20 11:15", 28],
            ["2023-05-20 11:20", 30],
            ["2023-05-20 11:25", 32],
            ["2023-05-20 11:30", 34],
            ["2023-05-20 11:35", 36],
            ["2023-05-20 11:40", 38],
            ["2023-05-20 11:45", 40],
            ["2023-05-20 11:50", 42],
            ["2023-05-20 11:55", 44],
            ["2023-05-20 12:00", 46],
        ]
    ]
    assert interpolated_ts.points == expected
