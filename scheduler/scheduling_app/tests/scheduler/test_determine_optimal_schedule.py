import pytest
from django.utils.timezone import now, timedelta

from entsoe_client.models import (
    DayAheadRenewablePercentageForecastData,
    RenewablePercentageDataPoint,
)
from entsoe_service.mocked_entsoe_service import MockEntsoeService
from scheduling_app.models import File, Metric, TaskQueueSourceFile
from scheduling_app.tasks import Scheduler
from scheduling_app.tasks.create_schedule import TaskQueue
from utils.FileStates import FileStateCode, FileProcessStep
from utils.s3_utils.mocked_s3_resource import S3ResourceMocked


@pytest.fixture(autouse=True)
def reset_queues():
    Scheduler.reset_queues()


@pytest.mark.django_db
def test_no_files():
    s3_resource = S3ResourceMocked()
    s3_resource.set_mocked_result_list_all_files([])

    scheduler = Scheduler(
        entsoe_service=MockEntsoeService(),
        openshift_client=None,
        s3_resource=s3_resource,
    )
    scheduler.determine_optimal_schedule()

    assert len(Scheduler.get_queues()) == 0


@pytest.mark.django_db
def test_one_file():
    s3_resource = S3ResourceMocked()
    service = MockEntsoeService()
    start_time = now()
    data_points = [
        (start_time, 1),
        (start_time + timedelta(seconds=10), 100),  # Highest point at +10s
        (start_time + timedelta(seconds=15), 5),
    ]
    service.set_mocked_renewable_percentage_forecast_until_last_available(
        renewable_percentage_forecast=DayAheadRenewablePercentageForecastData(
            forecasted_renewable_percentage=[
                RenewablePercentageDataPoint(datetime=point[0], value=point[1])
                for point in data_points
            ]
        )
    )
    scheduler = Scheduler(
        entsoe_service=service, openshift_client=None, s3_resource=s3_resource
    )

    file = File.objects.create(
        file_path="file_1",
        file_size=100,
        state_code=FileStateCode.PENDING.code,
        process_step=FileProcessStep.NEW.code,
        created_date=start_time,
        deadline=start_time + timedelta(seconds=60),
    )

    # Adding one metric, such that the median processing speed is 25 B/s
    # Therefore, the above file needs 4 seconds to process, and thus should
    # be the first in the queue at start_time + 8 seconds (10 - 2)
    file_finished = File.objects.create(
        file_path="file_finished",
        file_size=25,
        state_code=FileStateCode.UNPICKLED.code,
        process_step=FileProcessStep.FINISHED.code,
        created_date=start_time,
        deadline=start_time + timedelta(seconds=60),
    )
    metric = Metric.objects.create(source_file=file_finished)
    metric.start_time = start_time
    metric.end_time = start_time + timedelta(seconds=1)
    metric.save()

    scheduler.determine_optimal_schedule()

    queues = Scheduler.get_queues()
    assert len(queues) == 1
    queue = Scheduler.get_queue_by_start_time(
        start_time=start_time + timedelta(seconds=8)
    )
    assert isinstance(queue, TaskQueue)
    first_file = queue.pop()
    assert first_file.source_file == file
    assert first_file.expected_duration == timedelta(seconds=4)
    assert (
        # The last feasible start time is 4 seconds before the deadline,
        # plus the buffer calculated for last feasible start time
        first_file.latest_feasible_start_time
        == start_time
        + timedelta(seconds=60)
        - timedelta(seconds=4) * TaskQueueSourceFile.DEADLINE_BUFFER_PERCENTAGE
    )


@pytest.mark.django_db
def test_two_files_earlier_deadline_first():
    s3_resource = S3ResourceMocked()
    service = MockEntsoeService()
    start_time = now()
    data_points = [
        (start_time, 1),
        (start_time + timedelta(seconds=10), 100),  # Highest point at +10s
        (start_time + timedelta(seconds=15), 5),
    ]
    service.set_mocked_renewable_percentage_forecast_until_last_available(
        renewable_percentage_forecast=DayAheadRenewablePercentageForecastData(
            forecasted_renewable_percentage=[
                RenewablePercentageDataPoint(datetime=point[0], value=point[1])
                for point in data_points
            ]
        )
    )
    scheduler = Scheduler(
        entsoe_service=service, openshift_client=None, s3_resource=s3_resource
    )

    file_1 = File.objects.create(
        file_path="file_1",
        file_size=100,
        state_code=FileStateCode.PENDING.code,
        process_step=FileProcessStep.NEW.code,
        created_date=start_time,
        deadline=start_time + timedelta(seconds=60),
    )

    file_2 = File.objects.create(
        file_path="file_2",
        file_size=100,
        state_code=FileStateCode.PENDING.code,
        process_step=FileProcessStep.NEW.code,
        created_date=start_time,
        deadline=start_time + timedelta(seconds=30),
    )

    # Adding one metric, such that the median processing speed is 25 B/s
    # Therefore, the above file_1 needs 4 seconds to process, and the second
    # file_2 needs 4 seconds to process.
    file_finished = File.objects.create(
        file_path="file_finished",
        file_size=25,
        state_code=FileStateCode.UNPICKLED.code,
        process_step=FileProcessStep.FINISHED.code,
        created_date=start_time,
        deadline=start_time + timedelta(seconds=60),
    )
    metric = Metric.objects.create(source_file=file_finished)
    metric.start_time = start_time
    metric.end_time = start_time + timedelta(seconds=1)
    metric.save()

    scheduler.determine_optimal_schedule()

    queues = Scheduler.get_queues()
    assert len(queues) == 1

    # We expect the queue to start at start_time + 6 seconds (10-4), since the
    # first file needs 4 seconds to process, and the second needs 4 seconds.
    queue = Scheduler.get_queue_by_start_time(
        start_time=start_time + timedelta(seconds=6)
    )
    assert isinstance(queue, TaskQueue)

    first_file = queue.pop()
    second_file = queue.pop()

    # Expect the second file to be scheduled first,
    # as it has an earlier deadline
    assert first_file.source_file == file_2
    assert second_file.source_file == file_1

    # Test the expected durations
    assert first_file.expected_duration == timedelta(seconds=4)
    assert second_file.expected_duration == timedelta(seconds=4)

    # Test the expected latest feasible start times
    assert (
        first_file.latest_feasible_start_time
        == start_time
        + timedelta(seconds=30)
        - timedelta(seconds=4) * TaskQueueSourceFile.DEADLINE_BUFFER_PERCENTAGE
    )
    assert (
        second_file.latest_feasible_start_time
        == start_time
        + timedelta(seconds=60)
        - timedelta(seconds=4) * TaskQueueSourceFile.DEADLINE_BUFFER_PERCENTAGE
    )
