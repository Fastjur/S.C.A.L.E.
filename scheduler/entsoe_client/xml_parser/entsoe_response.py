from dataclasses import dataclass
from typing import Dict

from ..consts import ProcessType, PsrType, BusinessType
from ..models import TimeSeries


@dataclass(frozen=True)
class EntsoePsrTypeTimeSeriesResponse:
    process_type: ProcessType
    time_series: Dict[PsrType, TimeSeries]


@dataclass(frozen=True)
class EntsoeBusinessTypeTimeSeriesResponse:
    process_type: ProcessType
    time_series: Dict[BusinessType, TimeSeries]
