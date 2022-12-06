from .base_views import BaseSingleModelView, BaseQueryPostView
from ..models import File, Metric
from ..serializers import FileSerializer, MetricSerializer


class FileView(BaseSingleModelView):
    url_key = "file_id"
    model = File

    get_serializer = FileSerializer
    patch_serializer = FileSerializer


class FilesView(BaseQueryPostView):
    model = File

    get_serializer = FileSerializer
    post_serializer = FileSerializer


class MetricsView(BaseQueryPostView):
    model = Metric

    get_serializer = MetricSerializer
    post_serializer = MetricSerializer


class MetricView(BaseSingleModelView):
    url_key = "metric_id"
    model = Metric

    get_serializer = MetricSerializer
    patch_serializer = MetricSerializer
