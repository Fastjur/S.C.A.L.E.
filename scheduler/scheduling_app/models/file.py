from __future__ import annotations

import datetime
from copy import copy

import django.utils.timezone
from django.conf import settings as django_settings
from django.contrib import admin
from django.db import models
from django.utils.formats import localize
from django.utils.html import format_html
from django.utils.timezone import localtime
from humanize import naturalsize

from config import settings
from utils.FileStates import FileStateCode, FileProcessStep


class File(models.Model):
    DEFAULT_DEADLINE = datetime.timedelta(
        seconds=settings.default_file_deadline_seconds
    )

    # Fields
    file_path = models.TextField(unique=True)
    file_size = models.BigIntegerField()
    created_date = models.DateTimeField()
    deadline = models.DateTimeField(blank=True, null=True)
    state_code = models.CharField(
        max_length=4,
        choices=FileStateCode.choices(),
    )
    process_step = models.CharField(
        max_length=50,
        choices=FileProcessStep.choices(),
        default=FileProcessStep.NEW.code,
    )
    source_file = models.ForeignKey(
        "self", on_delete=models.CASCADE, blank=True, null=True
    )
    pod = models.ForeignKey(
        "Pod",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="files",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create a cached copy of the instance
        self.cached_instance = copy(self)

    def __str__(self) -> str:
        return self.file_path

    def save(self, *args, **kwargs):
        if not self.deadline:
            self.deadline = self.created_date + self.DEFAULT_DEADLINE

        # Save file
        super().save(*args, **kwargs)


class FileAdmin(admin.ModelAdmin):
    if not django_settings.DEBUG:
        readonly_fields = ("created_date", "pod")
    list_display = [
        "file_path",
        "state_code",
        "process_step",
        "file_size_human",
        "deadline_colored",
        "metric",
    ]

    list_editable = ["state_code", "process_step"]

    search_fields = ["file_path", "state_code", "process_step"]

    def file_size_human(self, file: File):
        return naturalsize(file.file_size, binary=True)

    file_size_human.short_description = "File size"

    def deadline_colored(self, file: File):
        localized_deadline = localize(localtime(file.deadline))
        if (
            file.process_step != FileProcessStep.FINISHED.code
            and django.utils.timezone.now() > file.deadline
        ):
            return format_html(
                "<span style='color: red; font-weight: bold'>{}</span>",
                localized_deadline,
            )
        return localized_deadline

    deadline_colored.short_description = "Deadline"
