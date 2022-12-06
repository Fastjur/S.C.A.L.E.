from django.contrib import admin

# Register your models here.
from .models import (
    File,
    FileAdmin,
    Metric,
    MetricAdmin,
    Pod,
    PodAdmin,
    TaskQueue,
    TaskQueueAdmin,
    TaskQueueSourceFile,
    TaskQueueSourceFileAdmin,
    MetricKwhMeasurement,
    MetricKwhMeasurementAdmin,
)

admin.site.register(File, FileAdmin)
admin.site.register(Metric, MetricAdmin)
admin.site.register(Pod, PodAdmin)
admin.site.register(TaskQueue, TaskQueueAdmin)
admin.site.register(TaskQueueSourceFile, TaskQueueSourceFileAdmin)
admin.site.register(MetricKwhMeasurement, MetricKwhMeasurementAdmin)
