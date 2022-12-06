import logging
import os
import xml.etree.ElementTree as ET
from abc import abstractmethod
from datetime import timedelta
from typing import List

import pandas as pd
import requests_cache
from arrow import Arrow

from config import settings
from entsoe_client.consts import (
    BusinessType,
    DocumentType,
    ProcessType,
    PsrType,
    Resolution,
)
from entsoe_client.models import (
    ActualGenerationPerProductionTypeData,
    DayAheadTotalLoadForecastData,
    DayAheadWindAndSolarData,
    ActualTotalLoadRealisedData,
    ForecastedLoad,
    ActualLoad,
    TimeSeries,
    EnergyDataPoint,
)
from entsoe_client.xml_parser.actual_generation_per_type_xml_parser import (
    ActualGenerationPerTypeXMLParser,
)
from entsoe_client.xml_parser.actual_load_realised_xml_parser import (
    ActualLoadRealisedXMLParser,
)
from entsoe_client.xml_parser.day_ahead_load_xml_parser import (
    DayAheadLoadXMLParser,
)
from entsoe_client.xml_parser.day_ahead_solar_wind_xml_parser import (
    DayAheadSolarWindXMLParser,
)

BASE_URL = "https://web-api.tp.entsoe.eu/api"
IN_DOMAIN = "10YNL----------L"
ENTSOE_EXPECTED_PERIOD_FORMAT = "YYYYMMDDHHmm"

logger = logging.getLogger(__name__)


class EntsoeApiClientInterface:
    def _raise_not_implemented(self):
        raise NotImplementedError(
            "This is the interface EntsoeApiClientInterface, "
            "it should be implemented before use"
        )

    @abstractmethod
    def get_wind_solar_day_ahead(
        self, start_date: Arrow, end_date: Arrow
    ) -> DayAheadWindAndSolarData:
        raise self._raise_not_implemented()

    @abstractmethod
    def get_actual_generation_per_type(
        self, start_date: Arrow, end_date: Arrow
    ) -> ActualGenerationPerProductionTypeData:
        raise self._raise_not_implemented()

    @abstractmethod
    def get_total_load_forecast(
        self, start_date: Arrow, end_date: Arrow
    ) -> DayAheadTotalLoadForecastData:
        raise self._raise_not_implemented()

    @abstractmethod
    def get_actual_load_realised(
        self, start_date: Arrow, end_date: Arrow
    ) -> ActualTotalLoadRealisedData:
        raise self._raise_not_implemented()


class EntsoeApiClient(EntsoeApiClientInterface):
    # Setup cached session to avoid hitting API rate limits,
    # the data is only updated once per 15 minutes max anyway (for actual gen)
    # TODO: probably need to make this a dependency injection for tests and prod etc.
    session: requests_cache.CachedSession = requests_cache.CachedSession(
        "entsoe_cache",
        expire_after=60 * 15,
        stale_if_error=False,
        backend="memory",
    )

    def __init__(self):
        if (
            "ENTSOE_API_KEY" not in os.environ
            or os.environ.get("ENTSOE_API_KEY") is None
        ):
            raise ValueError("ENTSOE_API_KEY environment variable is not set")

        self.ENTSOE_API_KEY = os.environ.get("ENTSOE_API_KEY")

    def _make_entsoe_get_call(
        self,
        document_type: DocumentType,
        process_type: ProcessType,
        period_start: str,
        period_end: str,
    ):
        url = (
            f"{BASE_URL}"
            f"?documentType={document_type}"
            f"&processType={process_type}"
            f"&outBiddingZone_Domain={IN_DOMAIN}"
            f"&in_Domain={IN_DOMAIN}"
            f"&periodStart={period_start}"
            f"&periodEnd={period_end}"
            f"&securityToken={self.ENTSOE_API_KEY}"
        )
        logger.info("Calling Entsoe API with url: %s", url)
        logger.debug("Period start: %s", period_start)
        logger.debug("Period end: %s", period_end)
        payload = {}
        headers = {}
        response = EntsoeApiClient.session.request(
            "GET", url, headers=headers, data=payload
        )
        if response.from_cache:
            logger.info("Response from cache!")
        response_xml = ET.fromstring(response.content)
        if response.status_code != 200:
            raise ValueError(
                f"API returned status code {response.status_code}"
            ) from Exception(response.content)
        logger.debug(response_xml)
        return response_xml

    def get_wind_solar_day_ahead(
        self, start_date, end_date
    ) -> DayAheadWindAndSolarData:
        period_start, period_end = self.convert_date_to_entsoe_format(
            start_date, end_date, map_to_midday=True
        )
        response_xml = self._make_entsoe_get_call(
            document_type=DocumentType.WIND_AND_SOLAR_FORECAST.value,
            process_type=ProcessType.DAY_AHEAD.value,
            period_start=period_start,
            period_end=period_end,
        )

        xml_parser = DayAheadSolarWindXMLParser()
        entsoe_response = xml_parser.parse(response_xml)

        return DayAheadWindAndSolarData(
            process_type=entsoe_response.process_type,
            forecasted_generation=entsoe_response.time_series,
        )

    @staticmethod
    def convert_date_to_entsoe_format(
        start_date, end_date, map_to_midday=False
    ):
        if map_to_midday:
            start_date = start_date.floor("day").replace(hour=12)
            end_date = end_date.floor("day").replace(hour=12)
        period_start = start_date.to("UTC").format(
            ENTSOE_EXPECTED_PERIOD_FORMAT
        )
        period_end = end_date.to("UTC").format(ENTSOE_EXPECTED_PERIOD_FORMAT)
        return period_start, period_end

    def get_actual_generation_per_type(
        self, start_date, end_date
    ) -> ActualGenerationPerProductionTypeData:
        period_start, period_end = self.convert_date_to_entsoe_format(
            start_date, end_date
        )
        response_xml = self._make_entsoe_get_call(
            document_type=DocumentType.WIND_AND_SOLAR_GENERATION.value,
            process_type=ProcessType.REALISED.value,
            period_start=period_start,
            period_end=period_end,
        )

        xml_parser = ActualGenerationPerTypeXMLParser()
        entsoe_response = xml_parser.parse(response_xml)

        return ActualGenerationPerProductionTypeData(
            process_type=entsoe_response.process_type,
            generation_per_production_type=entsoe_response.time_series,
        )

    def get_total_load_forecast(
        self, start_date, end_date
    ) -> DayAheadTotalLoadForecastData:
        period_start, period_end = self.convert_date_to_entsoe_format(
            start_date, end_date, map_to_midday=True
        )
        response_xml = self._make_entsoe_get_call(
            document_type=DocumentType.SYSTEM_TOTAL_LOAD.value,
            process_type=ProcessType.DAY_AHEAD.value,
            period_start=period_start,
            period_end=period_end,
        )

        xml_parser = DayAheadLoadXMLParser()
        entsoe_response = xml_parser.parse(response_xml)

        return DayAheadTotalLoadForecastData(
            process_type=entsoe_response.process_type,
            forecasted_load=ForecastedLoad(
                total_load=entsoe_response.time_series[
                    BusinessType.CONSUMPTION
                ]
            ),
        )

    def get_actual_load_realised(
        self, start_date, end_date
    ) -> ActualTotalLoadRealisedData:
        period_start, period_end = self.convert_date_to_entsoe_format(
            start_date, end_date
        )
        response_xml = self._make_entsoe_get_call(
            document_type=DocumentType.SYSTEM_TOTAL_LOAD.value,
            process_type=ProcessType.REALISED.value,
            period_start=period_start,
            period_end=period_end,
        )

        xml_parser = ActualLoadRealisedXMLParser()
        entsoe_response = xml_parser.parse(response_xml)

        return ActualTotalLoadRealisedData(
            process_type=entsoe_response.process_type,
            actual_load=ActualLoad(
                total_load=entsoe_response.time_series[
                    BusinessType.CONSUMPTION
                ]
            ),
        )


class MockEntsoeApiClient(EntsoeApiClientInterface):
    def get_wind_solar_day_ahead(
        self, start_date, end_date
    ) -> DayAheadWindAndSolarData:
        # Log current dir
        logger.info("Current dir: %s", os.getcwd())
        with open(
            "entsoe_client/example_responses/example_response_forecast_solar_wind.xml",
            "r",
            encoding="utf-8",
        ) as example_xml:
            response_xml = ET.fromstring(example_xml.read())
            xml_parser = DayAheadSolarWindXMLParser()
            entsoe_response = xml_parser.parse(response_xml)

            return DayAheadWindAndSolarData(
                process_type=entsoe_response.process_type,
                forecasted_generation=entsoe_response.time_series,
            )

    def get_total_load_forecast(
        self, start_date: Arrow, end_date: Arrow
    ) -> DayAheadTotalLoadForecastData:
        # Log current dir
        logger.info("Current dir: %s", os.getcwd())
        with open(
            "entsoe_client/example_responses/example_response_forecast_total_load.xml",
            "r",
            encoding="utf-8",
        ) as example_xml:
            response_xml = ET.fromstring(example_xml.read())
            xml_parser = DayAheadLoadXMLParser()
            entsoe_response = xml_parser.parse(response_xml)

            return DayAheadTotalLoadForecastData(
                process_type=entsoe_response.process_type,
                forecasted_load=ForecastedLoad(
                    total_load=entsoe_response.time_series[
                        BusinessType.CONSUMPTION
                    ]
                ),
            )


class SqueezedEntsoeApiClient(EntsoeApiClientInterface):
    def __init__(
        self,
        timeframe: timedelta = None,
    ):
        super().__init__()
        if timeframe is None:
            timeframe = timedelta(
                seconds=settings.default_file_deadline_seconds
            )
        self.timeframe = timeframe
        logger.info("SqueezedEntsoeApiClient timeframe: %s", self.timeframe)

    def get_wind_solar_day_ahead(
        self,
        start_date,
        end_date,
    ) -> DayAheadWindAndSolarData:
        season = settings.get("AUTOMATED_DATA_GATHERING_USE_SEASON_AVERAGE")
        year = settings.get("AUTOMATED_DATA_GATHERING_USE_YEAR_AVERAGE")

        # Log current dir
        logger.info("Current dir: %s", os.getcwd())
        base_dir = os.path.join("entsoe_client", "season_averages")

        # Solar
        solar_df = pd.read_csv(
            os.path.join(base_dir, f"{year}_{season}_solar.csv"),
            index_col=["hour", "minute"],
        )
        solar_median_points = self._get_median_points_over_timeframe(
            solar_df["median"], start_date
        )

        # Wind offshore
        wind_offshore_df = pd.read_csv(
            os.path.join(base_dir, f"{year}_{season}_wind_offshore.csv"),
            index_col=["hour", "minute"],
        )
        wind_offshore_median_points = self._get_median_points_over_timeframe(
            wind_offshore_df["median"], start_date
        )

        # Wind onshore
        wind_onshore_df = pd.read_csv(
            os.path.join(base_dir, f"{year}_{season}_wind_onshore.csv"),
            index_col=["hour", "minute"],
        )
        wind_onshore_median_points = self._get_median_points_over_timeframe(
            wind_onshore_df["median"], start_date
        )

        return DayAheadWindAndSolarData(
            process_type=ProcessType.DAY_AHEAD,
            forecasted_generation={
                PsrType.SOLAR: TimeSeries(
                    psr_type=PsrType.SOLAR,
                    business_type=BusinessType.SOLAR_GENERATION,
                    resolution=Resolution.FifteenMinutes,
                    points=solar_median_points,
                ),
                PsrType.WIND_OFFSHORE: TimeSeries(
                    psr_type=PsrType.WIND_OFFSHORE,
                    business_type=BusinessType.WIND_GENERATION,
                    resolution=Resolution.FifteenMinutes,
                    points=wind_offshore_median_points,
                ),
                PsrType.WIND_ONSHORE: TimeSeries(
                    psr_type=PsrType.WIND_ONSHORE,
                    business_type=BusinessType.WIND_GENERATION,
                    resolution=Resolution.FifteenMinutes,
                    points=wind_onshore_median_points,
                ),
            },
        )

    def get_total_load_forecast(
        self,
        start_date: Arrow,
        end_date: Arrow,
    ) -> DayAheadTotalLoadForecastData:
        season = settings.get("AUTOMATED_DATA_GATHERING_USE_SEASON_AVERAGE")
        year = settings.get("AUTOMATED_DATA_GATHERING_USE_YEAR_AVERAGE")

        # Log current dir
        logger.info("Current dir: %s", os.getcwd())
        base_dir = os.path.join("entsoe_client", "season_averages")

        # Total load forecast
        total_load_df = pd.read_csv(
            os.path.join(base_dir, f"{year}_{season}_forecasted_load.csv"),
            index_col=["hour", "minute"],
        )
        total_load_median_points = self._get_median_points_over_timeframe(
            total_load_df["median"], start_date
        )

        return DayAheadTotalLoadForecastData(
            process_type=ProcessType.DAY_AHEAD,
            forecasted_load=ForecastedLoad(
                total_load=TimeSeries(
                    psr_type=None,
                    business_type=BusinessType.CONSUMPTION,
                    resolution=Resolution.FifteenMinutes,
                    points=total_load_median_points,
                )
            ),
        )

    def get_actual_load_realised(
        self,
        start_date: Arrow,
        end_date: Arrow,
    ) -> ActualTotalLoadRealisedData:
        season = settings.get("AUTOMATED_DATA_GATHERING_USE_SEASON_AVERAGE")
        year = settings.get("AUTOMATED_DATA_GATHERING_USE_YEAR_AVERAGE")

        # Log current dir
        logger.info("Current dir: %s", os.getcwd())
        base_dir = os.path.join("entsoe_client", "season_averages")

        # Actual load realised
        actual_load_df = pd.read_csv(
            os.path.join(base_dir, f"{year}_{season}_actual_load.csv"),
            index_col=["hour", "minute"],
        )
        actual_load_median_points = self._get_median_points_over_timeframe(
            actual_load_df["median"], start_date
        )

        return ActualTotalLoadRealisedData(
            process_type=ProcessType.REALISED,
            actual_load=ActualLoad(
                total_load=TimeSeries(
                    psr_type=None,
                    business_type=BusinessType.CONSUMPTION,
                    resolution=Resolution.FifteenMinutes,
                    points=actual_load_median_points,
                )
            ),
        )

    def _get_median_points_over_timeframe(
        self, median_df, timeframe_start
    ) -> List[EnergyDataPoint]:
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
                EnergyDataPoint(
                    datetime=timeframe_start + i * step_size,
                    value=int(median),
                )
            )

        assert len(points) == len(median_df)
        assert points[0].datetime == timeframe_start
        assert points[-1].datetime == timeframe_end - step_size

        return points
