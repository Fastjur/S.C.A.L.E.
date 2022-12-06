import logging
import os
import random
import subprocess
import uuid
from typing import Optional
from zipfile import ZipFile

from django.http import HttpResponse

from config import settings
from scheduling_app.models import Pod
from scheduling_app.openshift import get_openshift_client
from utils.FileStates import PipelineProcessor
from utils.s3_utils import S3Resource

logger = logging.getLogger(__name__)

SMALLEST_FILES = [
    "bmkibler.pkl",
    "sacriel.pkl",
    "savjz.pkl",
    "p4wnyhof.pkl",
    "followgrubby.pkl",
    "kingrichard.pkl",
    "grimmmz.pkl",
    "tfue.pkl",
    "iwilldominate.pkl",
    "scarra.pkl",
    "kinggothalion.pkl",
    "tsm_viss.pkl",
    "c9sneaky.pkl",
]


def create_random_source_files(
    _, min_count: Optional[int], max_count: Optional[int]
):
    if min_count is None:
        min_count = 4
    if max_count is None:
        max_count = 10

    if min_count > max_count:
        raise ValueError("min_count must be less than or equal to max_count")

    if min_count < 0 or max_count < 0:
        raise ValueError("min_count and max_count must be positive")

    openshift_client = get_openshift_client()
    openshift_client.scale_pipeline_processor(
        PipelineProcessor.SYNTHETIC_GFC, 0
    )

    Pod.objects.all().delete()

    logger.debug("Current directory: %s", os.getcwd())
    # pickle_files = os.listdir(
    #     "synthetic/synth-data/ICWSM19_data"
    # )
    pickle_files = SMALLEST_FILES
    logger.debug("Pickle files: %s", pickle_files)

    # Create random number of new pending files
    s3_resource = S3Resource()
    rand_num_pending_files = random.randint(min_count, max_count)
    for pending_file_idx in range(rand_num_pending_files):
        logger.info(
            "Creating random file %i/%i",
            pending_file_idx + 1,
            rand_num_pending_files,
        )
        rand_num_pickles = random.randint(1, 3)
        pickle_files_sample = random.sample(pickle_files, rand_num_pickles)
        logger.info("Pickle files sample: %s", pickle_files_sample)

        random_name = uuid.uuid4()
        # subprocess.run("zip")
        with ZipFile(f"{random_name}.zip", "w") as zip_ref:
            for pickle_file in pickle_files_sample:
                logger.debug("Adding %s to zip", pickle_file)
                zip_ref.write(
                    f"synthetic/synth-data/ICWSM19_data/{pickle_file}",
                    f"/ICWSM19_data/{random_name}-{pickle_file}",
                )

        # Then create a .7z of the .zip file
        args = ["7z", "a", f"{random_name}.zip.7z", f"{random_name}.zip"]
        logger.info("Running %s", args)
        with subprocess.Popen(
            args=args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        ) as process:
            for line in process.stdout:
                print(line.decode("utf-8").strip())

        with open(f"{random_name}.zip.7z", "rb") as file_obj:
            s3_resource.upload_fileobj(
                file_obj,
                bucket=settings.pending_bucket,
                key=f"{random_name}.zip.7z",
            )

        # Remove the files
        os.remove(f"{random_name}.zip")
        os.remove(f"{random_name}.zip.7z")
        logger.info("Created random file and cleaned up")

    return HttpResponse("OK")
