import datetime
import io
import logging
import os
import signal
import tempfile
from contextlib import ExitStack
from zipfile import ZipFile

from config import settings
from utils import (
    get_trcs_data,
    post_trcs,
    time_function,
    patch_trcs,
)
from utils.FileStates import FileProcessStep, FileStateCode
from utils.s3_utils import S3Resource

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s -- %(message)s",
)
logging.getLogger("botocore").setLevel(logging.INFO)
logging.getLogger("s3transfer").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

UNZIP_DIRECTORY_NAME = "unzipped"
TWITCH_DATASET_DIRECTORY_NAME = "ICWSM19_data"


@time_function
def run_once():
    logger.info("Starting synthetic-unzip")

    pod_identifier = os.environ.get("POD_IDENTIFIER")
    file_list = get_trcs_data(endpoint=f"unzip/{pod_identifier}")["data"]

    if not file_list:
        logger.error(
            "No files found to process, this container should not be running"
        )
        return

    for file in file_list:
        # Process the file
        _process_file(file)

    logger.info("Finished synthetic-decrypt")


def _process_file(file):
    logger.info("Processing file: %s", file)
    # Mark file as processing, to be downloaded
    patch_trcs(
        "files",
        file["id"],
        data={
            "process_step": FileProcessStep.PROCESSING.code,
            "state_code": FileStateCode.DOWNLOADED.code,
        },
    )

    s3_resource = S3Resource()
    with ExitStack() as stack:
        file_obj = stack.enter_context(io.BytesIO())
        bucket = file["file_path"].split("/")[0]
        key = file["file_path"].split("/")[1]
        s3_resource.download_fileobj(file_obj, bucket, key)
        file_obj.seek(0)
        logger.info("Downloaded file: %s", key)

        tmp_dir = stack.enter_context(tempfile.TemporaryDirectory())

        zip_file = stack.enter_context(ZipFile(file_obj))
        logger.debug(
            "Unzipping %s to %s/%s",
            zip_file,
            tmp_dir,
            UNZIP_DIRECTORY_NAME,
        )
        zip_file.extractall(path=os.path.join(tmp_dir, UNZIP_DIRECTORY_NAME))

        for filename in os.scandir(
            os.path.join(
                tmp_dir,
                UNZIP_DIRECTORY_NAME,
            )
        ):
            if not filename.is_file():
                continue
            logger.debug("Unzipped file: %s", filename.path)
            unzipped_file = stack.enter_context(
                open(filename.path, "r", encoding="utf-8")
            )
            tsv_filename = f"{key.split('.')[0]}-{filename.name}"
            s3_resource.upload_fileobj(
                io.BytesIO(unzipped_file.buffer.read()),
                settings.processing_bucket,
                tsv_filename,
            )

            logger.info(
                "Uploaded file: %s to %s bucket",
                filename,
                settings.processing_bucket,
            )
            file_attributes = {
                "file_path": f"{settings.processing_bucket}/{tsv_filename}",
                "file_size": unzipped_file.buffer.seek(0, 2),
                "created_date": datetime.datetime.utcnow().strftime(
                    "%Y-%m-%dT%H:%M:%S.%fZ"
                ),
                "deadline": file["deadline"],
                "state_code": FileStateCode.UNZIPPED.code,
                "process_step": FileProcessStep.NEW.code,
                "source_file_id": file["source_file"],
            }

            post_trcs("files", data=file_attributes)

    # Remove, just to save space during big tests TODO: remove for final
    s3_resource.delete_file_in_bucket(bucket, key)
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
