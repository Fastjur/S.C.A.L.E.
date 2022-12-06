from dataclasses import dataclass

from arrow import Arrow


@dataclass(frozen=True)
class EmissionsPerKwhAtTime:
    datetime: Arrow
    carbon_intensity: float


@dataclass
class EmissionsData:
    emissions_per_kwh_at_time: list[EmissionsPerKwhAtTime]
