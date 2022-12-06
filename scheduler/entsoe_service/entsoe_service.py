import logging
import math
from abc import abstractmethod
from dataclasses import replace
from datetime import timedelta
from typing import Dict, List, Tuple

import arrow
from arrow import Arrow
from django.utils.timezone import now

from config import settings
from entsoe_client import EntsoeApiClientInterface
from entsoe_client.consts import PsrType
from entsoe_client.models import (
    DayAheadWindAndSolarData,
    DayAheadRenewablePercentageForecastData,
    TimeSeries,
    RenewablePercentageDataPoint,
)

logger = logging.getLogger(__name__)


class EntsoeServiceInterface:
    @abstractmethod
    def __init__(self, entsoe_api_client: EntsoeApiClientInterface):
        raise NotImplementedError

    @abstractmethod
    def get_wind_solar_last_data_available(
        self, start_date: Arrow
    ) -> DayAheadWindAndSolarData:
        raise NotImplementedError

    @abstractmethod
    def get_renewable_percentage_forecast(
        self, start_date: Arrow, end_date: Arrow
    ) -> DayAheadRenewablePercentageForecastData:
        raise NotImplementedError

    @abstractmethod
    def get_renewable_percentage_forecast_until_last_available(
        self,
        start_date: Arrow,
    ) -> DayAheadRenewablePercentageForecastData:
        raise NotImplementedError


class EntsoeService(EntsoeServiceInterface):
    def __init__(
        self,
        entsoe_api_client: EntsoeApiClientInterface,
    ):
        self._client = entsoe_api_client
        # This is because the client filters starting from the next 15 minutes
        # However, with the squeezed client, we get starting from now upto
        # the timeframe end of the squeezed client (default 4 min).
        # It is thus used only for development and testing purposes.
        # TODO: This actually breaks some separation of concerns, if done
        #  properly, this service should not be aware of the
        #  'squeezed' api client
        self._using_squeezed_timeframe = (
            settings.get("MOCK_ENTSOE_API_CLIENT", False) == "squeezed"
        )

    @staticmethod
    def _ceil_arrow_dt(arrow_datetime: Arrow, delta: timedelta) -> Arrow:
        return (
            arrow_datetime.min
            + math.ceil((arrow_datetime - arrow_datetime.min) / delta) * delta
        )

    def get_wind_solar_last_data_available(
        self,
        start_date: Arrow,
    ) -> DayAheadWindAndSolarData:
        logger.info(
            "Getting wind and solar forecast from %s until last data available",
            start_date,
        )

        (
            next_15_min,
            last_data_available_time,
        ) = self._get_last_data_available_time_frame(start_date)

        res = self._client.get_wind_solar_day_ahead(
            next_15_min, last_data_available_time
        )

        if self._using_squeezed_timeframe:
            return res

        filtered_forecast: Dict[PsrType, TimeSeries] = {}

        for psr_type, time_series in res.forecasted_generation.items():
            filtered_forecast[psr_type] = time_series.filter_points(
                next_15_min, last_data_available_time
            )

        filtered = replace(
            res,
            forecasted_generation=filtered_forecast,
        )
        return filtered

    @staticmethod
    def _get_last_data_available_time_frame(start_date) -> Tuple[Arrow, Arrow]:
        next_15_min = EntsoeService._ceil_arrow_dt(
            start_date, timedelta(minutes=15)
        )
        last_data_available_time = EntsoeService._ceil_arrow_dt(
            arrow.get(now()).shift(days=2), timedelta(minutes=15)
        )
        logger.debug("starting_day: %s", start_date)
        logger.debug("next_15_min: %s", next_15_min)
        logger.debug("last_data_available_time: %s", last_data_available_time)
        return next_15_min, last_data_available_time

    def get_renewable_percentage_forecast(
        self, start_date: Arrow, end_date: Arrow
    ) -> DayAheadRenewablePercentageForecastData:
        if self._using_squeezed_timeframe:
            start_date = arrow.get(now())
            logger.warning(
                "Using now as start date for squeezed timeframe: %s",
                start_date,
            )

        total_load_forecast = self._client.get_total_load_forecast(
            start_date=start_date, end_date=end_date
        )
        renewable_forecast = self._client.get_wind_solar_day_ahead(
            start_date=start_date, end_date=end_date
        )
        sum_of_renewables = renewable_forecast.sum_renewables
        logger.debug("sum_of_renewables: %s", sum_of_renewables)

        points: List[RenewablePercentageDataPoint] = []
        for point_dt, value in sum_of_renewables.items():
            total_load = total_load_forecast.forecasted_load.total_load
            forecasted_load = total_load.get_point_at_date(point_dt)
            if total_load is None:
                continue
            points.append(
                RenewablePercentageDataPoint(
                    point_dt, value / forecasted_load.value * 100
                )
            )

        return DayAheadRenewablePercentageForecastData(
            forecasted_renewable_percentage=points
        )

    def get_renewable_percentage_forecast_until_last_available(
        self,
        start_date: Arrow,
    ) -> DayAheadRenewablePercentageForecastData:
        logger.info(
            "Getting renewable percentage forecast from %s until last data "
            "available",
            start_date,
        )

        (
            next_15_min,
            last_data_available_time,
        ) = self._get_last_data_available_time_frame(start_date)

        res = self.get_renewable_percentage_forecast(
            next_15_min, last_data_available_time
        )

        if self._using_squeezed_timeframe:
            return res

        filtered_forecast: List[RenewablePercentageDataPoint] = []
        for point in res.forecasted_renewable_percentage:
            if next_15_min <= point.datetime <= last_data_available_time:
                filtered_forecast.append(point)

        filtered = replace(
            res,
            forecasted_renewable_percentage=filtered_forecast,
        )
        return filtered
