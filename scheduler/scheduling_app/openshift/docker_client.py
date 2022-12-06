import logging
import os
import uuid
from typing import List, Optional

import arrow
import docker
from docker.models.containers import Container

from energy_calculator import (
    EnergyCalculator,
    PodResourceConsumptionStat,
    KwhUsedAtReadTime,
)
from utils.FileStates import PipelineProcessor
from .openshift_client import OpenshiftClientInterface, OpenshiftPod

logger = logging.getLogger(__name__)


class DockerClient(OpenshiftClientInterface):
    NAME_PREFIX = "scheduler"

    def __init__(self):
        self._client = docker.from_env()

    @staticmethod
    def _get_pod_image_from_processor(processor):
        label = f"{DockerClient.NAME_PREFIX}-{processor.code}"
        return label

    @staticmethod
    def _container_to_openshift_pod(
        container: Container,
    ) -> OpenshiftPod:
        logger.debug(
            "Extracting container information to map to pod: %s", container
        )
        try:
            pod_identifier = next(
                x
                for x in container.attrs["Config"]["Env"]
                if x.startswith("POD_IDENTIFIER")
            )
            pod_identifier = pod_identifier.split("=")[1]
        except StopIteration:
            pod_identifier = container.id

        return OpenshiftPod(
            pod_identifier=pod_identifier,
            name=container.name,
            namespace="docker",
            pod_id=container.short_id,
            # TODO: Check below ip
            ip=container.attrs["NetworkSettings"]["IPAddress"],
            status=container.status,
            labels=container.labels,
        )

    def get_pods(
        self, processor: Optional[PipelineProcessor] = None
    ) -> List[OpenshiftPod]:
        logger.info("Getting pods for %s", processor)
        filters = {}
        if processor is not None:
            label = self._get_pod_image_from_processor(processor)
            filters["label"] = f"app={label}"
        containers = self._client.containers.list(
            filters=filters if filters else None,
        )
        logger.debug("Found containers: %s", containers)
        return [
            self._container_to_openshift_pod(container)
            for container in containers
        ]

    def add_pods_for_pipeline_processor(
        self, number: int, processor: PipelineProcessor
    ) -> List[OpenshiftPod]:
        logger.info("Scaling %s up by %s", processor, number)
        pods: List[OpenshiftPod] = []
        for i in range(number):
            logger.debug("Starting container %s", i)
            pod = self.run_pod_for_processor(processor, uuid.uuid4())
            pods.append(pod)
        return pods

    def remove_pods_for_pipeline_processor(
        self, number: int, processor: PipelineProcessor
    ):
        # TODO, try to remove ones first which are NOT assigned?
        #  OR: only use add method, make the scaler remove pods that are done?
        logger.info("Scaling %s down by %s", processor, number)
        label = self._get_pod_image_from_processor(processor)
        running_containers = self._client.containers.list(
            filters={"label": f"app={label}"},
        )
        for i in range(number):
            logger.debug("Stopping container %s", i)
            container = running_containers.pop()
            container.stop()
            container.remove()

    def scale_pipeline_processor(
        self, processor: PipelineProcessor, replicas
    ) -> List[OpenshiftPod]:
        logger.info("Scaling %s to %s", processor, replicas)
        label = self._get_pod_image_from_processor(processor)
        containers = self._client.containers.list(
            filters={"label": f"app={label}"},
        )
        diff = replicas - len(containers)
        if diff > 0:
            self.add_pods_for_pipeline_processor(diff, processor)
        elif diff < 0:
            self.remove_pods_for_pipeline_processor(-diff, processor)
        else:
            logger.info("No scaling needed")

        return self.get_pods(processor)

    def run_pod_for_processor(self, processor, pod_identifier) -> OpenshiftPod:
        image = self._get_pod_image_from_processor(processor)
        container = self._client.containers.run(
            image,
            detach=True,
            labels={"app": image},
            environment={
                "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID"),
                "AWS_SECRET_ACCESS_KEY": os.environ.get(
                    "AWS_SECRET_ACCESS_KEY"
                ),
                "ENV_FOR_DYNACONF": os.environ.get("ENV_FOR_DYNACONF"),
                "POD_IDENTIFIER": pod_identifier,
            },
            # network="scheduler_scheduler",
            network_mode="host",
            remove=True,
        )
        return self._container_to_openshift_pod(container)

    @staticmethod
    def _calculate_cpu_percent_unix(
        stat, system_memory: float
    ) -> PodResourceConsumptionStat:
        cpu_percent: float = 0.0

        previous_cpu = stat["precpu_stats"]["cpu_usage"]["total_usage"]
        previous_system = stat["precpu_stats"]["system_cpu_usage"]

        cpu_usage = stat["cpu_stats"]["cpu_usage"]["total_usage"]
        system_usage = stat["cpu_stats"]["system_cpu_usage"]

        cpu_delta = float(cpu_usage) - float(previous_cpu)
        system_delta = float(system_usage) - float(previous_system)

        if system_delta > 0.0 and cpu_delta > 0.0:
            cpu_percent = (cpu_delta / system_delta) * 100.0

        process_memory = stat["memory_stats"]["usage"]
        memory_percent = process_memory / system_memory

        return PodResourceConsumptionStat(
            previous_read_time=arrow.get(stat["preread"]),
            read_time=arrow.get(stat["read"]),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
        )

    def gather_pod_resource_consumption_statistics(
        self, pod: OpenshiftPod, metric_thread_result: list[KwhUsedAtReadTime]
    ):
        """
        Gather metrics for a pod until it is done running.

        **Note:** this method is blocking until the pod is deleted, and should be run
        in a separate thread!

        :param pod: The pod to gather metrics for
        :param metric_thread_result: Return variable for the thread, where the final kWh
        value will be stored at index 0 in the list.
        """
        logger.debug("Gathering metrics for pod %s", pod)
        container = self._client.containers.get(pod.pod_id)
        stats = container.stats(decode=True, stream=True)

        cpu_percent_stats = []
        system_memory = None
        for stat in stats:
            logger.debug("Stat: %s", stat)
            logger.debug("Container status: %s", container.status)
            try:
                if system_memory is None:
                    system_memory = stat["memory_stats"]["limit"]
                else:
                    if system_memory != stat["memory_stats"]["limit"]:
                        raise ValueError(
                            "System memory changed during pod execution?"
                        )
                cpu_percent = self._calculate_cpu_percent_unix(
                    stat, system_memory
                )
                logger.debug("CPU Percent: %s", cpu_percent)
                cpu_percent_stats.append(cpu_percent)
            except KeyError as err:
                logger.warning(err.__repr__())
                container = self._client.containers.get(pod.pod_id)
                if container.status == "exited":
                    logger.info("Container exited, stopping metric gathering")
                    break

        logger.debug("Calculation to kWh")
        energy_calculator = EnergyCalculator()
        kwh = energy_calculator.calculate_kwh(
            input_data=cpu_percent_stats, system_memory=system_memory
        )
        metric_thread_result[0] = kwh
        logger.info(
            "Pod %s consumed: %s kwh", pod.name, metric_thread_result[0]
        )

    def delete_pod(self, pod: OpenshiftPod, force: bool = False):
        logger.info("Deleting pod %s", pod)
        try:
            container = self._client.containers.get(pod.pod_id)
        except docker.errors.NotFound:
            logger.warning("Pod %s not found to delete", pod)
            return

        container.stop()
        container.remove(force=force)
