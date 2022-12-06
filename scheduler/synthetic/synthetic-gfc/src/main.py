import datetime
import logging
import os
import signal

from config import settings
from utils import time_function
from utils.FileStates import FileStateCode, FileProcessStep
from utils.s3_utils import S3Resource
from utils.trcs import post_trcs, get_trcs_data, patch_trcs

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s -- %(message)s",
)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("s3transfer").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


@time_function
def run_once():
    pod_identifier = os.environ.get("POD_IDENTIFIER")
    files = get_trcs_data(endpoint=f"gfc/{pod_identifier}")["data"]

    if not files:
        logger.error(
            "No files found to process, this container should not be running"
        )
        return

    for file in files:
        # Process the file
        _process_file(file)


def _process_file(file):
    logger.info("Processing file: %s", file)
    # Mark file as processing
    patch_trcs(
        "files",
        file["id"],
        data={"process_step": FileProcessStep.PROCESSING.code},
    )

    s3_resource = S3Resource()
    file_key = file["file_path"].split("/")[1]

    # Move file from pending to processing bucket
    s3_resource.move_file_between_buckets(
        settings.pending_bucket,
        settings.processing_bucket,
        file_key,
        file_key,
    )

    # Register new file to TRCS
    new_file_attributes = {
        "file_path": f"{settings.processing_bucket}/{file_key}",
        "file_size": file["file_size"],
        "created_date": datetime.datetime.utcnow().strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        ),
        "deadline": file["deadline"],
        "state_code": FileStateCode.DOWNLOADED.code,
        "process_step": FileProcessStep.NEW.code,
        "source_file_id": file["id"],
    }
    post_trcs("files", data=new_file_attributes)

    # Mark old file as finished
    patch_trcs(
        "files",
        file["id"],
        data={
            "process_step": FileProcessStep.FINISHED.code,
        },
    )


def sigterm_handler(signo, _stack_frame):
    logger.info("Received signal to terminate: %s, exiting", signo)
    raise SystemExit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, sigterm_handler)
    signal.signal(signal.SIGINT, sigterm_handler)

    run_once()
