import logging

from rest_framework import serializers, viewsets

from scheduling_app.models.pod import Pod

logger = logging.getLogger(__name__)


class PodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pod
        fields = "__all__"


class PodViewSet(viewsets.ModelViewSet):
    queryset = Pod.objects.all()
    serializer_class = PodSerializer
