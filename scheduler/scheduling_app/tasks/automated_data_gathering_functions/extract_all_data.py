import pandas as pd

from scheduling_app.models import Metric, Pod, File


def extract_all_data() -> (
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
):
    metrics = Metric.objects.all().select_related("source_file")

    durations = {metric.source_file_id: metric.duration for metric in metrics}
    processing_speeds = {
        metric.source_file_id: metric.processing_speed for metric in metrics
    }
    percentage_errors = {
        metric.source_file_id: metric.percentage_error for metric in metrics
    }
    difference_with_deadlines = {
        metric.source_file_id: metric.difference_with_deadline
        for metric in metrics
    }
    file_paths = {
        metric.source_file_id: metric.source_file.file_path
        for metric in metrics
    }
    file_sizes = {
        metric.source_file_id: metric.source_file.file_size
        for metric in metrics
    }
    total_kwh_used = {
        metric.source_file_id: metric.total_kwh_used for metric in metrics
    }

    df = pd.DataFrame.from_records(metrics.values(), index="source_file_id")
    df["duration"] = durations
    df["processing_speed"] = processing_speeds
    df["percentage_error"] = percentage_errors
    df["difference_with_deadline"] = difference_with_deadlines
    df["file_path"] = file_paths
    df["file_size"] = file_sizes
    df["total_kwh_used"] = total_kwh_used

    df["start_time"] = pd.to_datetime(df["start_time"])
    df["end_time"] = pd.to_datetime(df["end_time"])
    df["expected_duration_at_schedule_time"] = pd.to_timedelta(
        df["expected_duration_at_schedule_time"]
    )
    df["duration"] = pd.to_timedelta(df["duration"])
    df["difference_with_deadline"] = pd.to_timedelta(
        df["difference_with_deadline"]
    )
    df["file_path"] = df["file_path"].astype("string")

    kwh_measurements = []
    for metric in metrics:
        metric_kwh_measurements = metric.kwh_measurements.all()
        for measurement in metric_kwh_measurements:
            kwh_measurements.append(
                {
                    "metric": metric.source_file_id,
                    "read_time": measurement.read_time,
                    "kwh": measurement.kwh,
                }
            )

    kwh_df = pd.DataFrame.from_records(kwh_measurements, index="metric")

    files = File.objects.all().select_related("pod")
    files_df = pd.DataFrame.from_records(files.values(), index="id")

    pods = Pod.objects.all()
    pods_df = pd.DataFrame.from_records(pods.values(), index="pod_identifier")
    pods_df.drop(columns=["labels"], inplace=True)

    return df, kwh_df, files_df, pods_df
