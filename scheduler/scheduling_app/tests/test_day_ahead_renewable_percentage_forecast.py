import arrow
import pytest

from entsoe_client.models import (
    DayAheadRenewablePercentageForecastData,
    RenewablePercentageDataPoint,
)

START_TIME_TESTS = "2023-01-01T00:00:00+00:00"


@pytest.mark.parametrize(
    "values, expected_highest_value, expected_highest_value_date",
    [
        ([10, 20, 30], 30, arrow.get(START_TIME_TESTS).shift(hours=2)),
        ([10, 30, 20], 30, arrow.get(START_TIME_TESTS).shift(hours=1)),
        (
            [10, 20, 21, 500, 22, 23, 499],
            500,
            arrow.get(START_TIME_TESTS).shift(hours=3),
        ),
        ([10, 30, 30, 30, 20], 30, arrow.get(START_TIME_TESTS).shift(hours=1)),
        (
            [10, 30, 30, 30, 20, 40, 40, 40, 40],
            40,
            arrow.get(START_TIME_TESTS).shift(hours=5),
        ),
    ],
)
def test_day_ahead_renewable_percentage_forecast_highest_value(
    values, expected_highest_value, expected_highest_value_date
):

    data = DayAheadRenewablePercentageForecastData(
        forecasted_renewable_percentage=[
            RenewablePercentageDataPoint(
                datetime=arrow.get(START_TIME_TESTS).shift(hours=idx),
                value=val,
            )
            for idx, val in enumerate(values)
        ]
    )
    highest_value = data.get_highest_renewable_percentage()
    assert highest_value.value == expected_highest_value
    assert highest_value.datetime == expected_highest_value_date


@pytest.mark.parametrize(
    "values, clamp_time, expected_highest_value, expected_highest_value_date",
    [
        (
            [10, 20, 30, 40, 50, 60, 70],
            arrow.get(START_TIME_TESTS).shift(hours=3),
            40,
            arrow.get(START_TIME_TESTS).shift(hours=3),
        ),
        (
            [10, 20, 30, 40, 50, 60, 70],
            arrow.get(START_TIME_TESTS).shift(hours=5),
            60,
            arrow.get(START_TIME_TESTS).shift(hours=5),
        ),
    ],
)
def test_day_ahead_renewable_percentage_forecast_highest_value_clamped(
    values, clamp_time, expected_highest_value, expected_highest_value_date
):

    data = DayAheadRenewablePercentageForecastData(
        forecasted_renewable_percentage=[
            RenewablePercentageDataPoint(
                datetime=arrow.get(START_TIME_TESTS).shift(hours=idx),
                value=val,
            )
            for idx, val in enumerate(values)
        ]
    )
    highest_value = data.get_highest_renewable_percentage(
        clamp_time_end=clamp_time
    )
    assert highest_value.value == expected_highest_value
    assert highest_value.datetime == expected_highest_value_date
