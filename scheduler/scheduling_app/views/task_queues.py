from django.http import JsonResponse
from rest_framework import serializers

from scheduling_app.models import TaskQueue, TaskQueueSourceFile


class TaskQueueSourceFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskQueueSourceFile
        fields = "__all__"


class TaskQueueSerializer(serializers.ModelSerializer):
    files = TaskQueueSourceFileSerializer(many=True)

    class Meta:
        model = TaskQueue
        fields = "__all__"


def task_queues(_):
    queues = TaskQueue.objects.all()
    serializer = TaskQueueSerializer(queues, many=True)
    return JsonResponse({"data": serializer.data})
