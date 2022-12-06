# Generated by Django 4.2.5 on 2023-09-24 16:05

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "scheduling_app",
            "0002_alter_file_state_code_alter_metric_from_state_code_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="metric",
            name="file_size",
        ),
        migrations.AddField(
            model_name="file",
            name="file_size",
            field=models.BigIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="file",
            name="created_date",
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="file",
            name="process_step",
            field=models.CharField(
                choices=[
                    ("new", "new file"),
                    ("processing", "check the file state for the progress"),
                    ("finished", "finished processing"),
                ],
                default="new",
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="file",
            name="state_code",
            field=models.CharField(
                choices=[
                    ("0100", "File pending"),
                    ("0201", "File downloaded"),
                    ("0202", "File unzipped"),
                    ("0203", "File unpickled"),
                    ("unkn", "Unknown"),
                    ("err", "Error"),
                ],
                max_length=4,
            ),
        ),
    ]
