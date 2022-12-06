from datetime import timedelta

from arrow import Arrow
from django.conf import settings as django_settings
from django.contrib import admin
from django.db import models

from scheduling_app.models import File
from utils.FileStates import FileProcessStep


class TaskQueueSourceFile(models.Model):
    DEADLINE_BUFFER_PERCENTAGE = 1.1  # 10% buffer

    task_queue = models.ForeignKey(
        "TaskQueue", on_delete=models.CASCADE, related_name="files"
    )
    source_file = models.ForeignKey(File, on_delete=models.CASCADE)
    expected_duration = models.DurationField()
    is_popped = models.BooleanField(default=False)

    @property
    def latest_feasible_start_time(self) -> Arrow:
        """
        Returns the latest feasible start time for this file, based on the
        deadline of the file and the expected duration of the file.
        Includes a buffer of 10% as defined by
        :const:`Scheduler.DEADLINE_BUFFER_PERCENTAGE`
        :returns: The latest feasible start time for this file
        """
        return (
            self.source_file.deadline
            - self.expected_duration * self.DEADLINE_BUFFER_PERCENTAGE
        )


class TaskQueueSourceFileAdmin(admin.ModelAdmin):
    if not django_settings.DEBUG:
        readonly_fields = (
            "task_queue",
            "source_file",
            "expected_duration",
            "is_popped",
        )
    list_display = [
        "source_file",
        "expected_duration",
        "task_queue",
        "is_popped",
    ]


class TaskQueue(models.Model):
    start_time = models.DateTimeField()
    has_started = models.BooleanField(default=False)

    def get_all_files(self) -> list[File]:
        source_files = [file.source_file for file in self.files.all()]
        related_to_source_files = File.objects.filter(
            source_file__in=source_files
        )
        combined = list(source_files) + list(related_to_source_files)
        return combined

    def get_all_unfinished_files(self) -> list[File]:
        return [
            file
            for file in self.get_all_files()
            if file.process_step not in [FileProcessStep.FINISHED.code]
        ]

    @property
    def has_finished(self):
        unfinished_files = self.get_all_unfinished_files()
        return not unfinished_files

    @property
    def has_unpopped_source_files(self):
        return any(not file.is_popped for file in self.files.all())

    def __str__(self):
        finished_string = (
            ", finished"
            if self.has_finished
            else f", {len(self.get_all_unfinished_files())} files left"
        )
        return (
            f"TaskQueue {self.start_time}"
            f", has {'' if self.has_started else 'not '}started"
            f"{finished_string}"
        )

    def extend(self, files: list[TaskQueueSourceFile]):
        """
        Extends the queue with the given files
        :param files: list of files to add to the queue
        :return:
        """
        for file in files:
            file.task_queue = self
            file.is_popped = False
            file.save()

    def pop(self) -> TaskQueueSourceFile:
        """
        Pops the first file from the queue and returns it
        :return:
        """
        unpopped_files = list(self.files.filter(is_popped=False))
        if not unpopped_files:
            raise IndexError("No unpopped files in queue")
        unpopped_files.sort(key=lambda file: file.latest_feasible_start_time)
        popped_file = unpopped_files[0]
        popped_file.is_popped = True
        popped_file.save()
        return popped_file

    def get_expected_duration(self):
        return sum(
            (file.expected_duration for file in self.files), timedelta()
        )

    def get_expected_end_time(self):
        return self.start_time + self.get_expected_duration()


class TaskQueueAdmin(admin.ModelAdmin):
    if not django_settings.DEBUG:
        readonly_fields = ("start_time", "has_started")
