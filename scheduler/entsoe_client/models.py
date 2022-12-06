import logging
from dataclasses import dataclass, replace
from typing import List, Optional, Dict

import numpy as np
from arrow import Arrow
from rest_framework import serializers
from scipy.interpolate import interp1d

from .consts import (
    BusinessType,
    BusinessTypeSerializer,
    ProcessType,
    ProcessTypeSerializer,
    PsrType,
    PsrTypeSerializer,
    Resolution,
    ResolutionSerializer,
)

logger = logging.getLogger(__name__)


class ReadOnlySerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.read_only = True


def psr_type_ts_serializer(items):
    res_dict = {}
    for psr_type, ts in items:
        res_dict[
            PsrTypeSerializer().to_representation(psr_type)
        ] = TimeSeriesSerializer(ts).data
    return res_dict


@dataclass(frozen=True)
class TimeInterval:
    start_time: Arrow
    end_time: Arrow


class TimeIntervalSerializer(ReadOnlySerializer):
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()


@dataclass(frozen=True)
class EnergyDataPoint:
    datetime: Arrow
    value: int


class EnergyDataPointSerializer(ReadOnlySerializer):
    datetime = serializers.DateTimeField()
    value = serializers.IntegerField()


@dataclass(frozen=True)
class TimeSeries:
    psr_type: Optional[PsrType]
    business_type: BusinessType
    resolution: Resolution
    points: List[EnergyDataPoint]

    def interpolate_points(
        self,
        start_datetime: Arrow,
        end_datetime: Arrow,
        step_size_minutes: int = 1,
    ) -> "TimeSeries":
        datetimes = np.array(
            [point.datetime.timestamp() for point in self.points]
        )
        values = np.array([point.value for point in self.points])

        interpolation_func = interp1d(datetimes, values, kind="linear")

        step_size_seconds = step_size_minutes * 60
        interpolated_datetimes = np.arange(
            start_datetime.timestamp(),
            end_datetime.timestamp() + step_size_seconds,
            step_size_seconds,
        )
        interpolated_values = interpolation_func(interpolated_datetimes)
        new_points = [
            EnergyDataPoint(
                datetime=Arrow.fromtimestamp(ts),
                value=int(value),
            )
            for (ts, value) in zip(interpolated_datetimes, interpolated_values)
        ]
        return replace(self, points=new_points)

    def filter_points(
        self, start_datetime: Arrow, end_datetime: Arrow
    ) -> "TimeSeries":
        filtered_points = [
            point
            for point in self.points
            if start_datetime <= point.datetime <= end_datetime
        ]
        return replace(
            self,
            points=filtered_points,
        )

    def get_point_at_date(self, date: Arrow) -> Optional[EnergyDataPoint]:
        for point in self.points:
            if point.datetime.date() == date.date():
                return point
        return None


class TimeSeriesSerializer(ReadOnlySerializer):
    psr_type = PsrTypeSerializer()
    psr_type_human_readable = serializers.SerializerMethodField()
    business_type = BusinessTypeSerializer()
    business_type_human_readable = serializers.SerializerMethodField()
    resolution = ResolutionSerializer()
    points = EnergyDataPointSerializer(many=True)

    @staticmethod
    def get_psr_type_human_readable(obj):
        return str(obj.psr_type) if obj.psr_type is not None else None

    @staticmethod
    def get_business_type_human_readable(obj):
        return (
            str(obj.business_type) if obj.business_type is not None else None
        )


@dataclass(frozen=True)
class DayAheadWindAndSolarData:
    process_type: ProcessType
    forecasted_generation: Dict[PsrType, TimeSeries]

    @property
    def sum_renewables(self) -> Dict[Arrow, int]:
        sum_of_forecasted_generation: Dict[Arrow, int] = {}
        for time_series in self.forecasted_generation.values():
            for point in time_series.points:
                sum_of_forecasted_generation[point.datetime] = (
                    sum_of_forecasted_generation.get(point.datetime, 0)
                    + point.value
                )
        return sum_of_forecasted_generation


class DayAheadWindAndSolarDataSerializer(ReadOnlySerializer):
    process_type = ProcessTypeSerializer()
    forecasted_generation = serializers.SerializerMethodField()

    def get_forecasted_generation(self, obj):
        items = obj.forecasted_generation.items()
        return psr_type_ts_serializer(items)


@dataclass(frozen=True)
class ActualGenerationPerProductionTypeData:
    process_type: ProcessType
    generation_per_production_type: Dict[PsrType, TimeSeries]


class ActualGenerationPerProductionTypeDataSerializer(ReadOnlySerializer):
    process_type = ProcessTypeSerializer()
    generation_per_production_type = serializers.SerializerMethodField()

    def get_generation_per_production_type(self, obj):
        items = obj.generation_per_production_type.items()
        return psr_type_ts_serializer(items)


@dataclass(frozen=True)
class ForecastedLoad:
    total_load: TimeSeries


@dataclass(frozen=True)
class DayAheadTotalLoadForecastData:
    process_type: ProcessType
    forecasted_load: ForecastedLoad


class ForecastedLoadSerializer(ReadOnlySerializer):
    total_load = TimeSeriesSerializer()


class DayAheadTotalLoadForecastDataSerializer(ReadOnlySerializer):
    process_type = ProcessTypeSerializer()
    forecasted_load = ForecastedLoadSerializer()


@dataclass(frozen=True)
class ActualLoad:
    total_load: TimeSeries


@dataclass(frozen=True)
class ActualTotalLoadRealisedData:
    process_type: ProcessType
    actual_load: ActualLoad


class ActualLoadSerializer(ReadOnlySerializer):
    total_load = TimeSeriesSerializer()


class ActualTotalLoadDataSerializer(ReadOnlySerializer):
    process_type = ProcessTypeSerializer()
    actual_load = ActualLoadSerializer()


@dataclass(frozen=True)
class RenewablePercentageDataPoint:
    datetime: Arrow
    value: float


@dataclass(frozen=True)
class DayAheadRenewablePercentageForecastData:
    forecasted_renewable_percentage: List[RenewablePercentageDataPoint]

    def get_highest_renewable_percentage(
        self, clamp_time_end: Optional[Arrow] = None
    ) -> RenewablePercentageDataPoint:
        filtered = [
            point
            for point in self.forecasted_renewable_percentage
            if clamp_time_end is None or point.datetime <= clamp_time_end
        ]
        return max(
            filtered,
            key=lambda point: point.value,
        )


class RenewablePercentageDataPointSerializer(ReadOnlySerializer):
    datetime = serializers.DateTimeField()
    value = serializers.FloatField()


class DayAheadRenewablePercentageForecastDataSerializer(ReadOnlySerializer):
    forecasted_renewable_percentage = serializers.ListSerializer(
        child=RenewablePercentageDataPointSerializer(read_only=True)
    )
