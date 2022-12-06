from django.urls import path, include
from rest_framework import routers

from scheduling_app.views import (
    FilesView,
    FileView,
    MetricsView,
    MetricView,
    scale_pipeline_processor,
    buckets,
    gfc,
    unzip,
    unpickle,
    PodViewSet,
    openshift_pods,
    task_queues,
    create_random_source_files,
)
from scheduling_app.views.trigger import (
    trigger2,
    trigger3,
    trigger4,
    extract_all_data_view,
)

router = routers.DefaultRouter()
router.register(r"pods", PodViewSet)

app_name = "scheduling_app"
urlpatterns = [
    path("", include(router.urls)),
    path("files", FilesView.as_view()),
    path("files/<int:file_id>", FileView.as_view()),
    path("metrics", MetricsView.as_view()),
    path("metrics/<int:metric_id>", MetricView.as_view()),
    path("openshift-pods", openshift_pods),
    path(
        "scale/<str:processor_str>/<int:replicas>",
        scale_pipeline_processor,
    ),
    path("buckets", buckets, name="buckets"),
    path("task-queues", task_queues),
    path("gfc/<str:pod_identifier>", gfc, name="gfc"),
    path("unzip/<str:pod_identifier>", unzip, name="unzip"),
    path("unpickle/<str:pod_identifier>", unpickle, name="unpickle"),
    path("create-random-source-files", create_random_source_files),
    path(
        "create-random-source-files/<int:min_count>/<int:max_count>",
        create_random_source_files,
    ),
    path(
        "extract-all-data",
        extract_all_data_view,
    ),
    path("trigger2", trigger2),
    path("trigger3", trigger3),
    path("trigger4", trigger4),
]
