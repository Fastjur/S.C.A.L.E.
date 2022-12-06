from datetime import timedelta
from typing import Optional

from django.conf import settings as django_settings
from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.utils.timezone import localtime
from humanize import naturalsize, naturaldelta, scientific


class Metric(models.Model):
    source_file = models.OneToOneField(
        "scheduling_app.File",
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="metric",
    )
    start_time = models.DateTimeField(
        blank=True,
        null=True,
    )
    end_time = models.DateTimeField(
        blank=True,
        null=True,
    )
    expected_duration_at_schedule_time = models.DurationField(
        blank=True,
        null=True,
    )
    max_concurrency_at_execution_time = models.IntegerField(
        blank=True,
        null=True,
    )

    @property
    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    def get_duration_human(self):
        if not self.start_time:
            return "not started yet"
        if not self.end_time:
            started_ago = naturaldelta(localtime() - self.start_time)
            return f"started {started_ago} ago, not finished yet"
        duration = self.duration
        return f"processed in {naturaldelta(duration)}" if duration else "N/A"

    @property
    def processing_speed(self) -> Optional[float]:
        """
        Returns the processing speed in B/s, or None if the metric is not
        complete yet.
        :return: float processing speed in B/s
        """
        if self.duration and self.source_file.file_size:
            return self.source_file.file_size / self.duration.total_seconds()
        return None

    @property
    def percentage_error(self) -> Optional[float]:
        """
        Returns the percentage error of the model, or None if the metric is not
        complete yet.
        :return: float percentage error of the prediction
        """
        if self.duration and self.expected_duration_at_schedule_time:
            return round(
                100
                * (self.expected_duration_at_schedule_time - self.duration)
                / self.duration,
                2,
            )
        return None

    @property
    def difference_with_deadline(self) -> Optional[timedelta]:
        """
        Returns the difference between the deadline and the actual end time, or
        None if the metric is not complete yet.
        :return: timedelta difference between the deadline and actual end time
        """
        if self.end_time:
            return self.end_time - self.source_file.deadline
        return None

    @property
    def total_kwh_used(self) -> Optional[float]:
        """
        Returns a sum of all the kWh measurements for a total of this metric.
        :return: float, total kWh used
        """
        kwh_measurements = self.kwh_measurements.all()
        if kwh_measurements:
            return sum(
                kwh_measurement.kwh for kwh_measurement in kwh_measurements
            )
        return None

    def __str__(self):
        return (
            f"{naturalsize(self.source_file.file_size, binary=True)} "
            f"{self.get_duration_human()}"
        )


class MetricAdmin(admin.ModelAdmin):
    list_display = [
        "__str__",
        "duration",
        "expected_duration_at_schedule_time",
        "percentage_error_human",
        "end_time",
        "source_file_deadline",
        "difference_with_deadline_human",
        "file_size_human",
        "processing_speed_human",
        "total_kwh_used_human",
        "source_file",
    ]

    search_fields = ["source_file__file_path"]

    if not django_settings.DEBUG:
        readonly_fields = (
            "source_file",
            "start_time",
            "end_time",
            "expected_duration_at_schedule_time",
            "total_kwh_used",
        )

    def percentage_error_human(self, metric: Metric):
        percentage_error = metric.percentage_error
        if percentage_error:
            return f"{percentage_error}% {'overestimated' if percentage_error > 0 else 'underestimated'}"
        return "N/A"

    percentage_error_human.short_description = "Percentage error"

    def source_file_deadline(self, metric: Metric):
        return metric.source_file.deadline

    def difference_with_deadline_human(self, metric: Metric):
        difference = metric.difference_with_deadline
        html_wrapper = '<span style="color: {}">{}</span>'
        if difference:
            if difference > timedelta():
                return format_html(
                    html_wrapper.format(
                        "red", f"{naturaldelta(difference)} late"
                    )
                )
            return format_html(
                html_wrapper.format(
                    "green", f"{naturaldelta(abs(difference))} early"
                )
            )

    difference_with_deadline_human.short_description = "Diff. with deadline"

    def file_size_human(self, metric: Metric):
        return naturalsize(metric.source_file.file_size, binary=True)

    file_size_human.short_description = "File size"

    def processing_speed_human(self, metric: Metric):
        processing_speed = metric.processing_speed
        if processing_speed:
            return naturalsize(processing_speed, binary=True) + "/s"
        return "N/A"

    processing_speed_human.short_description = "Processing speed"

    def total_kwh_used_human(self, metric: Metric):
        if metric.total_kwh_used:
            return f"{scientific(metric.total_kwh_used)} kWh"
        return "N/A"

    total_kwh_used_human.short_description = "Total kWh used"
