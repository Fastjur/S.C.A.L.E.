from django.http import JsonResponse
from rest_framework import serializers

from scheduling_app.openshift import get_openshift_client


class OpenshiftPodSerializer(serializers.Serializer):
    pod_identifier = serializers.CharField()
    name = serializers.CharField()
    namespace = serializers.CharField()
    pod_id = serializers.CharField()
    ip = serializers.CharField()
    status = serializers.CharField()
    labels = serializers.DictField()


def openshift_pods(_):
    client = get_openshift_client()
    pods = client.get_pods()
    serializer = OpenshiftPodSerializer(pods, many=True)
    return JsonResponse({"data": serializer.data})
