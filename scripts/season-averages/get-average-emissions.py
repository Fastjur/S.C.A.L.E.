import os

import pandas as pd
from tqdm import tqdm

YEAR = 2021
START_SPRING = "0301"
START_SUMMER = "0601"
START_FALL = "0901"
START_WINTER = "1201"

TIMEZONE = "Europe/Amsterdam"
DATA_DIR = "emissions_data"
os.makedirs(DATA_DIR, exist_ok=True)

SEASONS = []
SEASONS.append(
    (
        f"{YEAR}_spring",
        (
            pd.Timestamp(f"{YEAR}{START_SPRING}", tz=TIMEZONE),
            pd.Timestamp(f"{YEAR}{START_SUMMER}", tz=TIMEZONE),
        ),
    )
)
SEASONS.append(
    (
        f"{YEAR}_summer",
        (
            pd.Timestamp(f"{YEAR}{START_SUMMER}", tz=TIMEZONE),
            pd.Timestamp(f"{YEAR}{START_FALL}", tz=TIMEZONE),
        ),
    )
)
SEASONS.append(
    (
        f"{YEAR}_fall",
        (
            pd.Timestamp(f"{YEAR}{START_FALL}", tz=TIMEZONE),
            pd.Timestamp(f"{YEAR}{START_WINTER}", tz=TIMEZONE),
        ),
    )
)
SEASONS.append(
    (
        f"{YEAR}_winter",
        (
            pd.Timestamp(f"{YEAR}{START_WINTER}", tz=TIMEZONE),
            pd.Timestamp(f"{YEAR+1}{START_SPRING}", tz=TIMEZONE),
        ),
    )
)

emissions_2021 = pd.read_csv(
    "NL_2021_hourly_emissions.csv", parse_dates=["Datetime (UTC)"]
)
emissions_2022 = pd.read_csv(
    "NL_2022_hourly_emissions.csv", parse_dates=["Datetime (UTC)"]
)
emissions = pd.concat([emissions_2021, emissions_2022])
emissions.drop(
    columns=[
        "Country",
        "Zone Name",
        "Zone Id",
        "Data Source",
        "Data Estimated",
        "Data Estimation Method",
    ],
    inplace=True,
)
emissions.set_index("Datetime (UTC)", inplace=True)
emissions.index = emissions.index.tz_localize("UTC").tz_convert(TIMEZONE)

emissions = emissions.resample("15min").mean().interpolate(method="linear")


def percentile(n):
    def percentile_(x):
        return x.quantile(n)

    percentile_.__name__ = "percentile_{:02.0f}".format(n * 100)
    return percentile_


for season in tqdm(SEASONS, desc="Season", position=0, ncols=80):
    season_name = season[0]
    start_date = season[1][0]
    end_date = season[1][1]

    season_emissions = emissions[
        (emissions.index >= start_date) & (emissions.index < end_date)
    ]

    by_hour_minute = season_emissions.groupby(
        [
            season_emissions.index.hour,
            season_emissions.index.minute,
        ]
    )
    df = by_hour_minute.agg(
        ["median", "mean", percentile(0.25), percentile(0.75)]
    )

    df.columns = df.columns.to_flat_index().map(" ".join)
    df.index = df.index.set_names(["hour", "minute"])
    df.reset_index(inplace=True)
    df.to_csv(os.path.join(DATA_DIR, f"{season_name}_emissions.csv"))
