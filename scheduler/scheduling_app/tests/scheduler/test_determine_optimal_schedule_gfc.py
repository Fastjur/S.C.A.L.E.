# from datetime import timedelta
#
# import pytest
# from django.utils.timezone import now
#
# from entsoe_client.models import (
#     DayAheadRenewablePercentageForecastData,
#     RenewablePercentageDataPoint,
# )
# from entsoe_service.mocked_entsoe_service import MockEntsoeService
# from scheduling_app.models import ScheduledFile, File
# from scheduling_app.tasks.create_schedule import Scheduler
# from utils.FileStates import FileStateCode, FileProcessStep
# from utils.s3_utils.mocked_s3_resource import S3ResourceMocked
#
#
# @pytest.mark.django_db
# def test_no_files_to_schedule():
#     s3_resource = S3ResourceMocked()
#     s3_resource.set_mocked_result_list_all_files([])
#
#     scheduler = Scheduler(
#         entsoe_service=MockEntsoeService(),
#         openshift_client=None,
#         s3_resource=s3_resource,
#     )
#     scheduler.determine_optimal_schedule()
#
#     scheduled_files = ScheduledFile.objects.all()
#     assert not scheduled_files
#
#
# @pytest.mark.django_db
# def test_scheduled_at_highest_point():
#     s3_resource = S3ResourceMocked()
#     service = MockEntsoeService()
#     start_time = now()
#     data_points = [
#         (start_time, 1),
#         (start_time + timedelta(seconds=1), 10),  # expected
#         (start_time + timedelta(seconds=2), 5),
#     ]
#     service.set_mocked_renewable_percentage_forecast_until_last_available(
#         renewable_percentage_forecast=DayAheadRenewablePercentageForecastData(
#             forecasted_renewable_percentage=[
#                 RenewablePercentageDataPoint(datetime=point[0], value=point[1])
#                 for point in data_points
#             ]
#         )
#     )
#     scheduler = Scheduler(
#         entsoe_service=service, openshift_client=None, s3_resource=s3_resource
#     )
#
#     file = File.objects.create(
#         file_path="file_1",
#         file_size=100,
#         state_code=FileStateCode.PENDING.code,
#         process_step=FileProcessStep.NEW.code,
#         created_date=start_time,
#         deadline=start_time + timedelta(seconds=60),
#     )
#
#     scheduler.determine_optimal_schedule()
#
#     scheduled_files = ScheduledFile.objects.all()
#     assert len(scheduled_files) == 1
#     assert scheduled_files[0].file == file
#     assert scheduled_files[0].scheduled_date == start_time + timedelta(
#         seconds=1
#     )
#
#
# @pytest.mark.django_db
# def test_scheduled_at_highest_points_first_peak():
#     s3_resource = S3ResourceMocked()
#     service = MockEntsoeService()
#     start_time = now()
#     data_points = [
#         (start_time, 1),
#         (start_time + timedelta(seconds=1), 10),  # expected
#         (start_time + timedelta(seconds=2), 5),
#         (start_time + timedelta(seconds=3), 10),
#     ]
#     service.set_mocked_renewable_percentage_forecast_until_last_available(
#         renewable_percentage_forecast=DayAheadRenewablePercentageForecastData(
#             forecasted_renewable_percentage=[
#                 RenewablePercentageDataPoint(datetime=point[0], value=point[1])
#                 for point in data_points
#             ]
#         )
#     )
#     scheduler = Scheduler(
#         entsoe_service=service, openshift_client=None, s3_resource=s3_resource
#     )
#
#     file = File.objects.create(
#         file_path="file_1",
#         file_size=100,
#         state_code=FileStateCode.PENDING.code,
#         process_step=FileProcessStep.NEW.code,
#         created_date=start_time,
#         deadline=start_time + timedelta(seconds=60),
#     )
#
#     scheduler.determine_optimal_schedule()
#
#     scheduled_files = ScheduledFile.objects.all()
#     assert len(scheduled_files) == 1
#     assert scheduled_files[0].file == file
#     assert scheduled_files[0].scheduled_date == start_time + timedelta(
#         seconds=1
#     )
#
#
# @pytest.mark.django_db
# def test_scheduled_at_highest_points_two():
#     s3_resource = S3ResourceMocked()
#     service = MockEntsoeService()
#     start_time = now()
#     data_points = [
#         (start_time, 1),
#         (start_time + timedelta(seconds=1), 9),
#         (start_time + timedelta(seconds=2), 5),
#         (start_time + timedelta(seconds=3), 10),  # expected
#     ]
#     service.set_mocked_renewable_percentage_forecast_until_last_available(
#         renewable_percentage_forecast=DayAheadRenewablePercentageForecastData(
#             forecasted_renewable_percentage=[
#                 RenewablePercentageDataPoint(datetime=point[0], value=point[1])
#                 for point in data_points
#             ]
#         )
#     )
#     scheduler = Scheduler(
#         entsoe_service=service, openshift_client=None, s3_resource=s3_resource
#     )
#
#     file = File.objects.create(
#         file_path="file_1",
#         file_size=100,
#         state_code=FileStateCode.PENDING.code,
#         process_step=FileProcessStep.NEW.code,
#         created_date=start_time,
#         deadline=start_time + timedelta(seconds=60),
#     )
#
#     scheduler.determine_optimal_schedule()
#
#     scheduled_files = ScheduledFile.objects.all()
#     assert len(scheduled_files) == 1
#     assert scheduled_files[0].file == file
#     assert scheduled_files[0].scheduled_date == start_time + timedelta(
#         seconds=3
#     )
#
#
# @pytest.mark.django_db
# def test_schedule_deadline_before_now():
#     s3_resource = S3ResourceMocked()
#     service = MockEntsoeService()
#     start_time = now()
#     data_points = [
#         (start_time, 1),
#         (start_time + timedelta(seconds=1), 10),
#         (start_time + timedelta(seconds=2), 5),
#     ]
#     service.set_mocked_renewable_percentage_forecast_until_last_available(
#         renewable_percentage_forecast=DayAheadRenewablePercentageForecastData(
#             forecasted_renewable_percentage=[
#                 RenewablePercentageDataPoint(datetime=point[0], value=point[1])
#                 for point in data_points
#             ]
#         )
#     )
#     scheduler = Scheduler(
#         entsoe_service=service, openshift_client=None, s3_resource=s3_resource
#     )
#
#     file = File.objects.create(
#         file_path="file_1",
#         file_size=100,
#         state_code=FileStateCode.PENDING.code,
#         process_step=FileProcessStep.NEW.code,
#         created_date=start_time,
#         deadline=start_time - timedelta(seconds=60),
#     )
#
#     scheduler.determine_optimal_schedule()
#
#     scheduled_files = ScheduledFile.objects.all()
#     assert len(scheduled_files) == 1
#     assert scheduled_files[0].file == file
#     assert scheduled_files[0].scheduled_date == start_time - timedelta(
#         seconds=60
#     )
#
#
# @pytest.mark.django_db
# def test_scheduled_multiple_at_highest_point():
#     s3_resource = S3ResourceMocked()
#     service = MockEntsoeService()
#     start_time = now()
#     data_points = [
#         (start_time, 1),
#         (start_time + timedelta(seconds=1), 10),  # expected
#         (start_time + timedelta(seconds=2), 5),
#     ]
#     service.set_mocked_renewable_percentage_forecast_until_last_available(
#         renewable_percentage_forecast=DayAheadRenewablePercentageForecastData(
#             forecasted_renewable_percentage=[
#                 RenewablePercentageDataPoint(datetime=point[0], value=point[1])
#                 for point in data_points
#             ]
#         )
#     )
#     scheduler = Scheduler(
#         entsoe_service=service, openshift_client=None, s3_resource=s3_resource
#     )
#
#     file1 = File.objects.create(
#         file_path="file_1",
#         file_size=100,
#         state_code=FileStateCode.PENDING.code,
#         process_step=FileProcessStep.NEW.code,
#         created_date=start_time,
#         deadline=start_time + timedelta(seconds=60),
#     )
#
#     file2 = File.objects.create(
#         file_path="file_2",
#         file_size=100,
#         state_code=FileStateCode.PENDING.code,
#         process_step=FileProcessStep.NEW.code,
#         created_date=start_time,
#         deadline=start_time + timedelta(seconds=60),
#     )
#
#     scheduler.determine_optimal_schedule()
#
#     scheduled_files = ScheduledFile.objects.all()
#     assert len(scheduled_files) == 2
#     assert scheduled_files[0].file == file1
#     assert scheduled_files[0].scheduled_date == start_time + timedelta(
#         seconds=1
#     )
#     assert scheduled_files[1].file == file2
#     assert scheduled_files[1].scheduled_date == start_time + timedelta(
#         seconds=1
#     )
#
#
# @pytest.mark.django_db
# def test_scheduled_at_highest_between_now_and_latest_feasible_time():
#     s3_resource = S3ResourceMocked()
#     service = MockEntsoeService()
#     start_time = now()
#     data_points = [
#         (start_time, 1),
#         (start_time + timedelta(seconds=39), 8),
#         (start_time + timedelta(seconds=40), 10),
#         (start_time + timedelta(seconds=41), 7),
#         (start_time + timedelta(seconds=60), 100),
#         (start_time + timedelta(seconds=80), 5),
#     ]
#     service.set_mocked_renewable_percentage_forecast_until_last_available(
#         renewable_percentage_forecast=DayAheadRenewablePercentageForecastData(
#             forecasted_renewable_percentage=[
#                 RenewablePercentageDataPoint(datetime=point[0], value=point[1])
#                 for point in data_points
#             ]
#         )
#     )
#     scheduler = Scheduler(
#         entsoe_service=service, openshift_client=None, s3_resource=s3_resource
#     )
#
#     # Adding one metric, such that the median processing speed is 20 MiB/s
#     # Therefore, the above file needs 5 seconds to process, and thus should
#     # start at or before +42s.
#     file_finished = File.objects.create(
#         file_path="file_finished",
#         file_size=20,
#         state_code=FileStateCode.DOWNLOADED.code,
#         process_step=FileProcessStep.FINISHED.code,
#         created_date=start_time,
#         deadline=start_time + timedelta(seconds=60),
#     )
#     file_finished.metric.start_time = start_time
#     file_finished.metric.end_time = start_time + timedelta(seconds=1)
#     file_finished.metric.from_state_code = FileStateCode.PENDING.code
#     file_finished.metric.to_state_code = FileStateCode.DOWNLOADED.code
#     file_finished.metric.save()
#
#     median = scheduler._determine_median_processing_speed()
#     assert median == 20
#
#     # File with deadline in 5 seconds
#     file = File.objects.create(
#         file_path="file_1",
#         file_size=100,
#         state_code=FileStateCode.PENDING.code,
#         process_step=FileProcessStep.NEW.code,
#         created_date=start_time,
#         # Deadline at 47s, thus should start processing at or before +42s
#         deadline=start_time + timedelta(seconds=47),
#     )
#
#     scheduler.determine_optimal_schedule()
#
#     # As the file should start at 42 the latest, it should be scheduled at 40s,
#     # which is the highest peak between start_time and the latest feasible time
#     # (42s).
#     scheduled_files = ScheduledFile.objects.all()
#     assert len(scheduled_files) == 1
#     assert scheduled_files[0].file == file
#     assert scheduled_files[0].scheduled_date == start_time + timedelta(
#         seconds=40
#     )
#
#     file_2 = File.objects.create(
#         file_path="file_2",
#         file_size=100,
#         state_code=FileStateCode.PENDING.code,
#         process_step=FileProcessStep.NEW.code,
#         created_date=start_time,
#         # Deadline at 53s, thus should start processing at or before +48s
#         deadline=start_time + timedelta(seconds=53),
#     )
#
#     scheduler.determine_optimal_schedule()
#
#     # New scheduled file should be added, old one should still exist.
#     # Checking that the first file is not a fluke
#     # As the file should start at 48 the latest, it should be scheduled at 40s,
#     # which is the highest peak between start_time and the latest feasible time
#     # (48s).
#     scheduled_files = ScheduledFile.objects.all()
#     assert len(scheduled_files) == 2
#     assert scheduled_files[1].file == file_2
#     assert scheduled_files[1].scheduled_date == start_time + timedelta(
#         seconds=40
#     )
#
#     file_3 = File.objects.create(
#         file_path="file_3",
#         file_size=100,
#         state_code=FileStateCode.PENDING.code,
#         process_step=FileProcessStep.NEW.code,
#         created_date=start_time,
#         # Deadline at 66s, thus should start processing at 60s, the
#         # highest peak just before the latest feasible time to start.
#         deadline=start_time + timedelta(seconds=66),
#     )
#
#     scheduler.determine_optimal_schedule()
#
#     scheduled_files = ScheduledFile.objects.all()
#     assert len(scheduled_files) == 3
#     assert scheduled_files[2].file == file_3
#     assert scheduled_files[2].scheduled_date == start_time + timedelta(
#         seconds=60
#     )
