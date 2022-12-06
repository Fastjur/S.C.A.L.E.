import logging
import os
from abc import abstractmethod
from datetime import timedelta

import pandas as pd
from arrow import Arrow

from config import settings
from .models import EmissionsPerKwhAtTime, EmissionsData

logger = logging.getLogger(__name__)


class EmissionsClientInterface:
    CARBON_INTENSITY_COL_NAME = "Carbon Intensity gCO₂eq/kWh (LCA) median"

    @abstractmethod
    def get_emissions_per_kwh(self, start_date: Arrow) -> EmissionsData:
        raise NotImplementedError()


class SqueezedEmissionsClient(EmissionsClientInterface):
    def __init__(self, timeframe: timedelta = None):
        if timeframe is None:
            timeframe = timedelta(
                seconds=settings.default_file_deadline_seconds
            )
        self.timeframe = timeframe
        logger.info(
            "Squeezed emissions client initialized, timeframe: %s", timeframe
        )

    def get_emissions_per_kwh(
        self, start_date: Arrow, override_season: str = None
    ) -> EmissionsData:
        logger.warning("Using squeezed emissions client")

        if override_season:
            season = override_season
        else:
            season = settings.get(
                "AUTOMATED_DATA_GATHERING_USE_SEASON_AVERAGE"
            )
        year = settings.get("AUTOMATED_DATA_GATHERING_USE_YEAR_AVERAGE")

        # Log current dir
        logger.info("Current dir: %s", os.getcwd())
        base_dir = os.path.join("emissions_client", "season_averages")

        emissions_df = pd.read_csv(
            os.path.join(base_dir, f"{year}_{season}_emissions.csv"),
            index_col=["hour", "minute"],
        )

        median_df = emissions_df[self.CARBON_INTENSITY_COL_NAME]
        median_points = self._get_median_points_over_timeframe(
            median_df, start_date
        )

        return EmissionsData(
            emissions_per_kwh_at_time=median_points,
        )

    def _get_median_points_over_timeframe(
        self, median_df, timeframe_start
    ) -> list[EmissionsPerKwhAtTime]:
        timeframe_end = timeframe_start + self.timeframe
        logger.warning(
            "Will be returning squeezed data from %s to %s",
            timeframe_start,
            timeframe_end,
        )

        step_size = self.timeframe / len(median_df)
        points = []
        for i, median in enumerate(median_df):
            points.append(
                EmissionsPerKwhAtTime(
                    datetime=timeframe_start + i * step_size,
                    carbon_intensity=int(median),
                )
            )

        assert len(points) == len(median_df)
        assert points[0].datetime == timeframe_start
        assert points[-1].datetime == timeframe_end - step_size

        return points


class EmissionsClient(EmissionsClientInterface):
    def get_emissions_per_kwh(
        self, start_date: Arrow, end_date: Arrow
    ) -> EmissionsData:
        # TODO: this would be the place where we got real data if running in real systems
        raise NotImplementedError()
