import logging

from django.http import JsonResponse

from config import settings
from utils.s3_utils import S3Error, S3Resource

logger = logging.getLogger(__name__)


def buckets(_):
    s3_resource = S3Resource()
    try:
        s3_resource.create_bucket(settings.pending_bucket)
        s3_resource.create_bucket(settings.processing_bucket)
    except S3Error as err:
        logger.error(err)
    bucket_list = s3_resource.list_buckets()

    return JsonResponse({"buckets": bucket_list})
