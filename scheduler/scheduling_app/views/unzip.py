import logging

from django.http import JsonResponse

from scheduling_app.models import Pod
from scheduling_app.serializers import FileSerializer
from utils import time_function

logger = logging.getLogger(__name__)


@time_function
def unzip(request, pod_identifier: str):
    if request.method == "GET":
        pod = Pod.objects.get(pod_identifier=pod_identifier)
        serializer = FileSerializer(pod.files, many=True)

        return JsonResponse({"data": serializer.data})
