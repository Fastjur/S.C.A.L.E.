from datetime import timedelta

import arrow
import pytest

from entsoe_service import EntsoeService


@pytest.mark.parametrize(
    "time, expected",
    [
        (
            arrow.get("2023-01-01T00:00:00+00:00"),
            arrow.get("2023-01-01T00:00:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:01:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:02:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:03:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:04:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:05:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:06:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:10:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:14:59+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:15:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:30:00+00:00"),
            arrow.get("2023-01-01T00:30:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:45:00+00:00"),
            arrow.get("2023-01-01T00:45:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:45:01+00:00"),
            arrow.get("2023-01-01T01:00:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:55:00+00:00"),
            arrow.get("2023-01-01T01:00:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:01:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:06:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:10:00+00:00"),
            arrow.get("2023-01-01T00:15:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:46:00+00:00"),
            arrow.get("2023-01-01T01:00:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:49:00+00:00"),
            arrow.get("2023-01-01T01:00:00+00:00"),
        ),
        (
            arrow.get("2023-01-01T00:53:00+00:00"),
            arrow.get("2023-01-01T01:00:00+00:00"),
        ),
    ],
)
def test_entsoe_api_client_time_rounding(time, expected):
    service = EntsoeService(entsoe_api_client=None)
    assert (
        service._ceil_arrow_dt(time, delta=timedelta(minutes=15)) == expected
    )
