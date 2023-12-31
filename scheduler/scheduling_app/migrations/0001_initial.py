# Generated by Django 4.2.5 on 2023-09-14 09:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="File",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file_path", models.TextField(unique=True)),
                ("created_date", models.DateTimeField(blank=True, null=True)),
                (
                    "state_code",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("0100", "File pending"),
                            ("0201", "File downloaded"),
                            ("0202", "File unzipped"),
                            ("unkn", "Unknown"),
                            ("err", "Error"),
                        ],
                        max_length=4,
                        null=True,
                    ),
                ),
                (
                    "process_step",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("new", "new file"),
                            (
                                "processing",
                                "check the file state for the progress",
                            ),
                            ("finished", "finished processing"),
                        ],
                        default="new",
                        max_length=50,
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Metric",
            fields=[
                (
                    "from_state_code",
                    models.CharField(
                        choices=[
                            ("0100", "File pending"),
                            ("0201", "File downloaded"),
                            ("0202", "File unzipped"),
                            ("unkn", "Unknown"),
                            ("err", "Error"),
                        ],
                        max_length=4,
                    ),
                ),
                (
                    "to_state_code",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("0100", "File pending"),
                            ("0201", "File downloaded"),
                            ("0202", "File unzipped"),
                            ("unkn", "Unknown"),
                            ("err", "Error"),
                        ],
                        max_length=4,
                        null=True,
                    ),
                ),
                ("start_time", models.DateTimeField()),
                ("end_time", models.DateTimeField(blank=True, null=True)),
                (
                    "file",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        primary_key=True,
                        serialize=False,
                        to="scheduling_app.file",
                    ),
                ),
                ("file_size", models.BigIntegerField()),
            ],
        ),
    ]
