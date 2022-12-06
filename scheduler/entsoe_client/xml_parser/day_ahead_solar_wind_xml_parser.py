import xml.etree.ElementTree as ET

import arrow

from .entsoe_response import EntsoePsrTypeTimeSeriesResponse
from ..consts import ProcessType, Resolution, BusinessType, PsrType
from ..models import EnergyDataPoint, TimeSeries


class DayAheadSolarWindXMLParser:
    @staticmethod
    def parse(
        response_xml: ET.Element,
    ) -> EntsoePsrTypeTimeSeriesResponse:
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
            out_domain = time_series_el.find(
                "gen_load_doc:outBiddingZone_Domain.mRID", namespaces
            )
            if out_domain is not None:
                continue
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
            psr_type_el = time_series_el.find(
                "gen_load_doc:MktPSRType/gen_load_doc:psrType", namespaces
            )
            psr_type = (
                PsrType(psr_type_el.text) if psr_type_el is not None else None
            )
            if psr_type not in ts_per_type:
                ts_per_type[psr_type] = TimeSeries(
                    psr_type=psr_type,
                    business_type=business_type,
                    resolution=resolution,
                    points=points,
                )
            else:
                existing_ts = ts_per_type[psr_type]
                existing_ts.points.extend(points)
        return EntsoePsrTypeTimeSeriesResponse(
            process_type=process_type,
            time_series=ts_per_type,
        )
