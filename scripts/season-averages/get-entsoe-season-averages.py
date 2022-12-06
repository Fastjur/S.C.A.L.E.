import os
from itertools import islice
from typing import List, Dict

import arrow
import pandas as pd
from entsoe import EntsoePandasClient
from tqdm import tqdm

from entsoe_client.models import EnergyDataPoint

POINTS_PER_DAY_FOR_CHUNKING = 96

entsoe_client = EntsoePandasClient(api_key=os.environ.get("ENTSOE_API_KEY"))
COUNTRY_CODE = "NL"
TIMEZONE = "Europe/Amsterdam"
DATA_DIR = "data"
RAW_DATA_DIR = "raw_data"

YEARS = range(2015, 2023)

# Start and end dates for all the meteorological seasons in MMDD
START_SPRING = "0301"
START_SUMMER = "0601"
START_FALL = "0901"
START_WINTER = "1201"

SEASONS = []
for year in YEARS:
    SEASONS.append(
        (
            f"{year}_spring",
            (
                pd.Timestamp(f"{year}{START_SPRING}", tz=TIMEZONE),
                pd.Timestamp(f"{year}{START_SUMMER}", tz=TIMEZONE),
            ),
        )
    )
    SEASONS.append(
        (
            f"{year}_summer",
            (
                pd.Timestamp(f"{year}{START_SUMMER}", tz=TIMEZONE),
                pd.Timestamp(f"{year}{START_FALL}", tz=TIMEZONE),
            ),
        )
    )
    SEASONS.append(
        (
            f"{year}_fall",
            (
                pd.Timestamp(f"{year}{START_FALL}", tz=TIMEZONE),
                pd.Timestamp(f"{year}{START_WINTER}", tz=TIMEZONE),
            ),
        )
    )
    SEASONS.append(
        (
            f"{year}_winter",
            (
                pd.Timestamp(f"{year}{START_WINTER}", tz=TIMEZONE),
                pd.Timestamp(f"{year+1}{START_SPRING}", tz=TIMEZONE),
            ),
        )
    )


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def get_entsoe_datestring(date_string):
    return (
        arrow.get(date_string, "YYYYMMDDHHmm", tzinfo=TIMEZONE)
        .to("UTC")
        .format("YYYYMMDDHHmm")
    )


def get_formatted_day_data(points: List[EnergyDataPoint]) -> Dict[str, int]:
    day_data = {}
    for point in points:
        day_data[point.datetime.to(TIMEZONE).format("HHmm")] = point.value
    return day_data


def percentile(n):
    def percentile_(x):
        return x.quantile(n)

    percentile_.__name__ = "percentile_{:02.0f}".format(n * 100)
    return percentile_


# Ask user what data to show
RAW_DATA_ONLY = None
while RAW_DATA_ONLY not in ["y", "n"]:
    try:
        RAW_DATA_ONLY = input("Only save raw data? [y/n]: ")
    except ValueError:
        print("Invalid input. Please enter (y)es or (n)o.")
RAW_DATA_ONLY = RAW_DATA_ONLY == "y"


for season in tqdm(SEASONS, desc="Season", position=0, ncols=80):
    season_name = season[0]
    start_date = season[1][0]
    end_date = season[1][1]

    renewable_forecast = entsoe_client.query_wind_and_solar_forecast(
        country_code=COUNTRY_CODE,
        start=start_date,
        end=end_date,
    )

    load_forecast = entsoe_client.query_load_forecast(
        country_code=COUNTRY_CODE,
        start=start_date,
        end=end_date,
    )

    load_actual = entsoe_client.query_load(
        country_code=COUNTRY_CODE,
        start=start_date,
        end=end_date,
    )

    if RAW_DATA_ONLY:
        raw_data = pd.concat(
            [renewable_forecast, load_forecast, load_actual], axis=1
        )
        raw_data.to_csv(f"{RAW_DATA_DIR}/{season_name}_raw_data.csv")
        continue

    renewable_forecast_by_hour_minute = renewable_forecast.groupby(
        [
            renewable_forecast.index.hour,
            renewable_forecast.index.minute,
        ]
    )
    for renewable_tuple in tqdm(
        [
            ("solar", "Solar"),
            ("wind_onshore", "Wind Onshore"),
            ("wind_offshore", "Wind Offshore"),
        ],
        desc="Renewable",
        position=1,
        leave=False,
        ncols=80,
    ):
        renewable_name = renewable_tuple[1]
        renewable_save_path = (
            f"{DATA_DIR}/{season_name}_{renewable_tuple[0]}.csv"
        )
        renewable_df = renewable_forecast_by_hour_minute[renewable_name]
        renewable_agg = renewable_df.agg(
            ["median", "mean", percentile(0.25), percentile(0.75)]
        )
        renewable_agg.to_csv(
            renewable_save_path,
            index_label=["hour", "minute"],
        )

    load_forecast_by_hour_minute = load_forecast.groupby(
        [
            load_forecast.index.hour,
            load_forecast.index.minute,
        ]
    )
    load_forecast_df = load_forecast_by_hour_minute["Forecasted Load"]
    load_forecast_agg = load_forecast_df.agg(
        ["median", "mean", percentile(0.25), percentile(0.75)]
    )
    load_forecast_agg.to_csv(
        f"{DATA_DIR}/{season_name}_forecasted_load.csv",
        index_label=["hour", "minute"],
    )

    load_actual_by_hour_minute = load_actual.groupby(
        [
            load_actual.index.hour,
            load_actual.index.minute,
        ]
    )
    load_actual_df = load_actual_by_hour_minute["Actual Load"]
    load_actual_agg = load_actual_df.agg(
        ["median", "mean", percentile(0.25), percentile(0.75)]
    )
    load_actual_agg.to_csv(
        f"{DATA_DIR}/{season_name}_actual_load.csv",
        index_label=["hour", "minute"],
    )
