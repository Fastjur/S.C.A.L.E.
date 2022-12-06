import pytest
from django.utils.timezone import now, timedelta

from scheduling_app.models import File
from scheduling_app.tasks.create_schedule import Scheduler
from utils.FileStates import FileStateCode, FileProcessStep


@pytest.mark.django_db
def test_get_pending_source_files_one():
    file = File.objects.create(
        file_path="file_path",
        file_size=1,
        created_date=now(),
        state_code=FileStateCode.PENDING.code,
        process_step=FileProcessStep.NEW.code,
    )

    pending_files = Scheduler._get_pending_source_files()

    assert len(pending_files) == 1
    assert pending_files[0] == file


@pytest.mark.django_db
def test_get_pending_source_files_multiple():
    expected_files = []
    for i in range(0, 10):
        expected_files.append(
            File.objects.create(
                file_path=f"file_path_{i}",
                file_size=i,
                created_date=now(),
                state_code=FileStateCode.PENDING.code,
                process_step=FileProcessStep.NEW.code,
            )
        )

    pending_files = Scheduler._get_pending_source_files()

    assert len(pending_files) == 10
    for i in range(len(expected_files)):
        assert pending_files[i] == expected_files[i]


@pytest.mark.django_db
def test_get_only_applicable_files():
    applicable_file = File.objects.create(
        file_path="file_path",
        file_size=1,
        created_date=now(),
        state_code=FileStateCode.PENDING.code,
        process_step=FileProcessStep.NEW.code,
    )

    File.objects.create(
        file_path="file_path_2",
        file_size=1,
        created_date=now(),
        state_code=FileStateCode.DOWNLOADED.code,
        process_step=FileProcessStep.NEW.code,
    )

    File.objects.create(
        file_path="file_path_3",
        file_size=1,
        created_date=now(),
        state_code=FileStateCode.UNZIPPED.code,
        process_step=FileProcessStep.NEW.code,
    )

    File.objects.create(
        file_path="file_path_4",
        file_size=1,
        created_date=now(),
        state_code=FileStateCode.UNPICKLED.code,
        process_step=FileProcessStep.NEW.code,
    )

    File.objects.create(
        file_path="file_path_5",
        file_size=1,
        created_date=now(),
        state_code=FileStateCode.PENDING.code,
        process_step=FileProcessStep.PROCESSING.code,
    )

    pending_files = Scheduler._get_pending_source_files()

    assert len(pending_files) == 1
    assert pending_files[0] == applicable_file


@pytest.mark.django_db
def test_get_only_files_that_are_not_scheduled_yet():
    applicable_file = File.objects.create(
        file_path="file_path",
        file_size=1,
        created_date=now(),
        state_code=FileStateCode.PENDING.code,
        process_step=FileProcessStep.NEW.code,
    )

    already_scheduled_file = File.objects.create(
        file_path="file_path_2",
        file_size=1,
        created_date=now(),
        state_code=FileStateCode.PENDING.code,
        process_step=FileProcessStep.NEW.code,
    )

    ScheduledFile.objects.create(
        file=already_scheduled_file, scheduled_date=now() + timedelta(days=1)
    )

    pending_files = Scheduler._get_pending_source_files()

    assert len(pending_files) == 1
    assert pending_files[0] == applicable_file
