import pytest
from django.utils.timezone import now, timedelta

from config import settings
from scheduling_app.models import File
from scheduling_app.tasks.create_schedule import Scheduler
from utils.FileStates import FileStateCode, FileProcessStep
from utils.s3_utils.mocked_s3_resource import S3ResourceMocked
from utils.s3_utils.s3_resource import S3File


@pytest.mark.django_db
def test_get_pending_files_and_update_db_one():
    s3_resource = S3ResourceMocked()
    s3_resource.set_mocked_result_list_all_files(
        [
            S3File(settings.pending_bucket, "key1", 100),
        ]
    )

    scheduler = Scheduler(
        entsoe_service=None, openshift_client=None, s3_resource=s3_resource
    )

    scheduler.get_pending_files_and_update_db()

    files = File.objects.all()
    assert len(files) == 1
    assert files[0].file_path == f"{settings.pending_bucket}/key1"
    assert files[0].file_size == 100
    assert files[0].state_code == FileStateCode.PENDING.code
    assert files[0].process_step == FileProcessStep.NEW.code

    # test if created date is recent
    time_diff = abs(now() - files[0].created_date)
    assert time_diff < timedelta(seconds=10)


@pytest.mark.django_db
def test_get_pending_files_and_update_db_multiple():
    s3_resource = S3ResourceMocked()
    mocked_s3_files = [
        S3File(settings.pending_bucket, f"key{i}", 100 * i)
        for i in range(0, 10)
    ]
    s3_resource.set_mocked_result_list_all_files(mocked_s3_files)

    scheduler = Scheduler(
        entsoe_service=None, openshift_client=None, s3_resource=s3_resource
    )

    scheduler.get_pending_files_and_update_db()

    files = File.objects.all()
    assert len(files) == len(mocked_s3_files)
    for i in range(len(mocked_s3_files)):
        assert files[i].file_path == f"{settings.pending_bucket}/key{i}"
        assert files[i].file_size == 100 * i
        assert files[i].state_code == FileStateCode.PENDING.code
        assert files[i].process_step == FileProcessStep.NEW.code

        # test if created date is recent
        time_diff = abs(now() - files[i].created_date)
        assert time_diff < timedelta(seconds=10)


@pytest.mark.django_db
def test_already_exists():
    s3_resource = S3ResourceMocked()
    s3_resource.set_mocked_result_list_all_files(
        [
            S3File(settings.pending_bucket, "key1", 100),
        ]
    )

    scheduler = Scheduler(
        entsoe_service=None, openshift_client=None, s3_resource=s3_resource
    )

    scheduler.get_pending_files_and_update_db()

    files = File.objects.all()
    assert len(files) == 1
    assert files[0].file_path == f"{settings.pending_bucket}/key1"
    assert files[0].file_size == 100
    assert files[0].state_code == FileStateCode.PENDING.code
    assert files[0].process_step == FileProcessStep.NEW.code

    # test if created date is recent
    time_diff = abs(now() - files[0].created_date)
    assert time_diff < timedelta(seconds=10)

    # Run again, file "is still in s3 list", as that mocked list is not updated
    # but a new file should not be created in the DB.
    scheduler.get_pending_files_and_update_db()

    files = File.objects.all()
    assert len(files) == 1
    assert files[0].file_path == f"{settings.pending_bucket}/key1"
    assert files[0].file_size == 100
    assert files[0].state_code == FileStateCode.PENDING.code
    assert files[0].process_step == FileProcessStep.NEW.code

    # test if created date is recent
    time_diff = abs(now() - files[0].created_date)
    assert time_diff < timedelta(seconds=10)


@pytest.mark.django_db
def test_adds_metric():
    raise NotImplementedError


@pytest.mark.django_db
def test_does_not_add_metric_if_exists():
    raise NotImplementedError
