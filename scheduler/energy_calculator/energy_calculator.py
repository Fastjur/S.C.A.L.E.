from dataclasses import dataclass

from arrow import Arrow


@dataclass
class HardwareSpecification:
    name: str
    v_cpu: int
    memory: int
    storage_os: int
    storage_data: int
    network: int
    hardware_type: str


@dataclass
class Platform:
    average_min_watts: float
    average_max_watts: float


@dataclass
class PodResourceConsumptionStat:
    previous_read_time: Arrow
    read_time: Arrow
    cpu_percent: float
    memory_percent: float


@dataclass
class KwhUsedAtReadTime:
    read_time: Arrow
    kwh_used: float


class EnergyCalculator:
    def __init__(self):
        self.hardware = HardwareSpecification(
            name="Bastian nodes",
            v_cpu=2,
            memory=16,
            storage_os=250,
            storage_data=0,
            network=10,
            hardware_type="virtual",
        )
        self.cloud_platform = Platform(0.74, 3.84)

    def calculate_kwh(
        self,
        input_data: list[PodResourceConsumptionStat],
        system_memory: float,
    ) -> list[KwhUsedAtReadTime]:
        """
        Calculate the energy consumption in kWh based on the input data.
        :param input_data: list of EnergyCalculatorInput
        :return: float energy consumption in kWh
        """
        kwh_used_list = []
        for data_point in input_data:
            timeslot_delta = (
                data_point.read_time - data_point.previous_read_time
            )
            total_seconds = timeslot_delta.total_seconds()
            platform_watts_range = (
                self.cloud_platform.average_max_watts
                - self.cloud_platform.average_min_watts
            )
            cpu_watts_used = (
                self.cloud_platform.average_min_watts
                + data_point.cpu_percent * platform_watts_range
            )
            cpu_kwh = (
                total_seconds
                * cpu_watts_used
                * self.hardware.v_cpu
                / (3600 * 1000)
            )
            memory_watts_used = system_memory * data_point.memory_percent / 1e9
            memory_kwh = total_seconds * memory_watts_used * 0.000392 / 3600
            kwh_used = cpu_kwh + memory_kwh
            kwh_used_list.append(
                KwhUsedAtReadTime(
                    read_time=data_point.read_time,
                    kwh_used=kwh_used,
                )
            )

        return kwh_used_list
