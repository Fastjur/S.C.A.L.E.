from django.conf import settings as django_settings
from django.contrib import admin
from django.db import models


class MetricKwhMeasurement(models.Model):
    metric = models.ForeignKey(
        "scheduling_app.Metric",
        on_delete=models.CASCADE,
        related_name="kwh_measurements",
    )
    read_time = models.DateTimeField()
    kwh = models.FloatField()


class MetricKwhMeasurementAdmin(admin.ModelAdmin):
    list_display = ("metric", "read_time", "kwh")
    search_fields = ("metric__source_file__file_path", "read_time", "kwh")
    if not django_settings.DEBUG:
        readonly_fields = ("metric", "read_time", "kwh")
