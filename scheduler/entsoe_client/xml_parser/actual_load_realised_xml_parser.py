import xml.etree.ElementTree as ET

import arrow

from .entsoe_response import (
    EntsoeBusinessTypeTimeSeriesResponse,
)
from ..consts import ProcessType, Resolution, BusinessType
from ..models import EnergyDataPoint, TimeSeries


class ActualLoadRealisedXMLParser:
    @staticmethod
    def parse(
        response_xml: ET.Element,
    ) -> EntsoeBusinessTypeTimeSeriesResponse:
        namespaces = {
            "gen_load_doc": "urn:iec62325.351:tc57wg16:451-6:"
            "generationloaddocument:3:0"
        }
        process_type = ProcessType(
            response_xml.find(
                "gen_load_doc:process.processType", namespaces
            ).text
        )
        time_series = response_xml.findall(
            "gen_load_doc:TimeSeries", namespaces
        )
        ts_per_type = {}
        for time_series_el in time_series:
            period = time_series_el.find("gen_load_doc:Period", namespaces)
            interval_start = arrow.get(
                period.find(
                    "gen_load_doc:timeInterval/gen_load_doc:start", namespaces
                ).text
            )
            resolution = Resolution(
                period.find("gen_load_doc:resolution", namespaces).text
            )
            points = [
                EnergyDataPoint(
                    interval_start.shift(minutes=i * resolution.get_minutes()),
                    int(point.find("gen_load_doc:quantity", namespaces).text),
                )
                for (i, point) in enumerate(
                    period.findall("gen_load_doc:Point", namespaces)
                )
            ]
            business_type = BusinessType(
                time_series_el.find(
                    "gen_load_doc:businessType", namespaces
                ).text
            )
            if business_type not in ts_per_type:
                ts_per_type[business_type] = TimeSeries(
                    psr_type=None,
                    business_type=business_type,
                    resolution=resolution,
                    points=points,
                )
            else:
                existing_ts = ts_per_type[business_type]
                existing_ts.points.extend(points)
        return EntsoeBusinessTypeTimeSeriesResponse(
            process_type=process_type,
            time_series=ts_per_type,
        )
