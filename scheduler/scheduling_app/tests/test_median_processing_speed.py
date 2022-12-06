import datetime

import pytest

from scheduling_app.models import File, Metric
from scheduling_app.tasks.create_schedule import Scheduler
from utils.FileStates import FileStateCode


@pytest.mark.django_db
def test_median_processing_speed_one_file():
    scheduler = Scheduler(
        entsoe_service=None, openshift_client=None, s3_resource=None
    )
    sliding_window_date = scheduler.SLIDING_WINDOW_DATE_START_DATE
    file_size = 100

    file = File.objects.create(
        file_size=file_size,
        created_date=sliding_window_date,
        process_step=FileStateCode.UNPICKLED.code,
    )

    metric = Metric.objects.create(source_file=file)
    metric.start_time = sliding_window_date + datetime.timedelta(seconds=1)
    metric.end_time = sliding_window_date + datetime.timedelta(seconds=5)
    metric.max_concurrency_at_execution_time = 1
    metric.save()

    expected_duration = datetime.timedelta(seconds=4)
    median_processing_speed = scheduler._determine_median_processing_speed()
    assert metric.duration == expected_duration
    assert median_processing_speed == 100 / 4  # 100 bytes / 4 seconds


@pytest.mark.django_db
def test_median_processing_speed_two_files():
    scheduler = Scheduler(
        entsoe_service=None, openshift_client=None, s3_resource=None
    )
    sliding_window_date = scheduler.SLIDING_WINDOW_DATE_START_DATE
    file_size = 100

    for i in range(2):
        file = File.objects.create(
            file_path=f"file_{i}",
            file_size=file_size,
            created_date=sliding_window_date,
            process_step=FileStateCode.DOWNLOADED.code,
        )

        metric = Metric.objects.create(source_file=file)
        metric.start_time = sliding_window_date + datetime.timedelta(seconds=1)
        metric.end_time = sliding_window_date + datetime.timedelta(
            seconds=i + 2
        )
        metric.max_concurrency_at_execution_time = 1
        metric.save()

        expected_duration = datetime.timedelta(seconds=i + 1)
        assert metric.duration == expected_duration

    median_processing_speed = scheduler._determine_median_processing_speed()
    # 100 B in 1s, and 100 B in 2s
    assert median_processing_speed == ((100 / 1) + (100 / 2)) / 2


@pytest.mark.django_db
def test_median_processing_speed_only_one_done():
    scheduler = Scheduler(
        entsoe_service=None, openshift_client=None, s3_resource=None
    )
    sliding_window_date = scheduler.SLIDING_WINDOW_DATE_START_DATE
    file_size = 100

    applicable_file = File.objects.create(
        file_path="applicable_file",
        file_size=file_size,
        created_date=sliding_window_date,
        process_step=FileStateCode.UNPICKLED.code,
    )

    applicable_metric = Metric.objects.create(source_file=applicable_file)
    applicable_metric.start_time = sliding_window_date + datetime.timedelta(
        seconds=1
    )
    applicable_metric.end_time = sliding_window_date + datetime.timedelta(
        seconds=5
    )
    applicable_metric.max_concurrency_at_execution_time = 1
    applicable_metric.save()

    unfinished_file = File.objects.create(
        file_path="unfinished_file",
        file_size=file_size,
        created_date=sliding_window_date,
        process_step=FileStateCode.DOWNLOADED.code,
    )

    unfinished_metric = Metric.objects.create(source_file=unfinished_file)
    unfinished_metric.start_time = sliding_window_date + datetime.timedelta(
        seconds=1
    )
    unfinished_metric.save()

    not_started_file = File.objects.create(
        file_path="not_started_file",
        file_size=file_size,
        created_date=sliding_window_date,
        process_step=FileStateCode.DOWNLOADED.code,
    )

    not_started_metric = Metric.objects.create(source_file=not_started_file)
    not_started_metric.save()

    too_old_file = File.objects.create(
        file_path="too_old_file",
        file_size=file_size,
        created_date=sliding_window_date - datetime.timedelta(days=1),
        process_step=FileStateCode.DOWNLOADED.code,
    )

    too_old_metric = Metric.objects.create(source_file=too_old_file)
    too_old_metric.start_time = sliding_window_date - datetime.timedelta(
        seconds=1
    )
    too_old_metric.end_time = sliding_window_date + datetime.timedelta(
        seconds=5
    )
    too_old_metric.save()

    # Only the applicable file processing speed should be taken into account
    expected_duration = datetime.timedelta(seconds=4)
    median_processing_speed = scheduler._determine_median_processing_speed()
    assert applicable_metric.duration == expected_duration
    assert median_processing_speed == 100 / 4  # 100 bytes / 4 seconds


@pytest.mark.django_db
def test_median_processing_speed_one_file_4_processors():
    scheduler = Scheduler(
        entsoe_service=None, openshift_client=None, s3_resource=None
    )
    sliding_window_date = scheduler.SLIDING_WINDOW_DATE_START_DATE
    file_size = 100

    file = File.objects.create(
        file_size=file_size,
        created_date=sliding_window_date,
        process_step=FileStateCode.UNPICKLED.code,
    )

    metric = Metric.objects.create(source_file=file)
    metric.start_time = sliding_window_date + datetime.timedelta(seconds=1)
    metric.end_time = sliding_window_date + datetime.timedelta(seconds=5)
    metric.max_concurrency_at_execution_time = 4
    metric.save()

    expected_duration = datetime.timedelta(seconds=4)
    median_processing_speed = scheduler._determine_median_processing_speed()
    assert metric.duration == expected_duration

    # 100 bytes / 4 seconds / 4 processors
    assert median_processing_speed == 100 / 4


@pytest.mark.django_db
def test_median_processing_speed_two_files_different_concurrency():
    scheduler = Scheduler(
        entsoe_service=None, openshift_client=None, s3_resource=None
    )
    sliding_window_date = scheduler.SLIDING_WINDOW_DATE_START_DATE
    file_size = 100

    file1 = File.objects.create(
        file_path="file1",
        file_size=file_size,
        created_date=sliding_window_date,
        process_step=FileStateCode.UNPICKLED.code,
    )

    file2 = File.objects.create(
        file_path="file2",
        file_size=file_size,
        created_date=sliding_window_date,
        process_step=FileStateCode.UNPICKLED.code,
    )

    metric1 = Metric.objects.create(source_file=file1)
    metric1.start_time = sliding_window_date + datetime.timedelta(seconds=1)
    metric1.end_time = sliding_window_date + datetime.timedelta(seconds=5)
    metric1.max_concurrency_at_execution_time = 2
    metric1.save()
    assert metric1.duration == datetime.timedelta(seconds=4)

    metric1_expected_processing_speed = 100 / 4

    metric2 = Metric.objects.create(source_file=file2)
    metric2.start_time = sliding_window_date + datetime.timedelta(seconds=1)
    metric2.end_time = sliding_window_date + datetime.timedelta(seconds=4)
    metric2.max_concurrency_at_execution_time = 4
    metric2.save()
    assert metric2.duration == datetime.timedelta(seconds=3)

    metric2_expected_processing_speed = 100 / 3

    median_processing_speed = scheduler._determine_median_processing_speed()

    assert (
        median_processing_speed
        == (
            metric1_expected_processing_speed
            + metric2_expected_processing_speed
        )
        / 2
    )
