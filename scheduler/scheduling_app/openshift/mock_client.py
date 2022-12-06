import logging
from typing import List

from utils.FileStates import PipelineProcessor
from .openshift_client import OpenshiftClientInterface, OpenshiftPod

logger = logging.getLogger(__name__)


class MockOpenshiftClient(OpenshiftClientInterface):
    def __init__(self, namespace="mocked-namespace"):
        super().__init__(namespace)
        self.pods = {}

    def get_pods(
        self, processor: PipelineProcessor = None
    ) -> List[OpenshiftPod]:
        logger.warning("[MOCKED] getting pods")
        pod_list: List[OpenshiftPod] = []
        for pod_name in self.pods:
            # TODO Check below condition
            if processor is not None and pod_name != processor.code:
                for i in range(self.pods[pod_name]):
                    labels = {"app": processor.code} if processor else {}
                    pod_list.append(
                        OpenshiftPod(
                            name=f"{pod_name}-{i}",
                            namespace="mocked-namespace",
                            pod_id="mocked-id",
                            ip="mocked-ip",
                            status="mocked-status",
                            labels=labels,
                        )
                    )
        return pod_list

    def scale_pipeline_processor(
        self, processor: PipelineProcessor, replicas
    ) -> List[OpenshiftPod]:
        logger.warning(
            "[MOCKED] scaling %s to %i replicas", processor, replicas
        )
        self.pods[processor.code] = replicas
        return self.get_pods(None)
