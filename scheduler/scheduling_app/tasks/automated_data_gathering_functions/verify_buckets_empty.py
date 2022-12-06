import logging
import sys

from config import settings
from utils.s3_utils import S3Resource

logger = logging.getLogger(__name__)


def verify_buckets_empty() -> bool:
    s3_resource = S3Resource()
    pending_files = list(s3_resource.list_all_files(settings.pending_bucket))
    if pending_files:
        logger.critical(f"Pending bucket is not empty! Files: {pending_files}")
        sys.exit(1)
    processing_files = list(
        s3_resource.list_all_files(settings.processing_bucket)
    )
    if processing_files:
        logger.critical(
            f"Processing bucket is not empty! Files: {processing_files}"
        )
        sys.exit(1)

    return True
