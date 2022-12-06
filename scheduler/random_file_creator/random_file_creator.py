import logging
import os
import random
import subprocess
import tempfile
import threading
import uuid
from zipfile import ZipFile

import enlighten
import pandas as pd

logger = logging.getLogger(__name__)

PKL_DIR = "synthetic/synth-data/ICWSM19_data"

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


class RandomFileCreator:
    def __init__(self, save_dir: str):
        self._save_dir = save_dir

    def create_random_file(
        self,
        min_num_pickles,
        max_num_pickles,
        smallest_only: bool = True,
    ) -> str:
        rand_num_pickles = random.randint(min_num_pickles, max_num_pickles)

        if smallest_only:
            pickle_files_sample = random.sample(
                SMALLEST_FILES, rand_num_pickles
            )
        else:
            pickle_files_sample = random.sample(
                os.listdir(PKL_DIR), rand_num_pickles
            )
        logger.info("Pickle files sample: %s", pickle_files_sample)

        random_name = uuid.uuid4()
        logger.info("Random name: %s", random_name)

        return self.create_7z_file(pickle_files_sample, random_name.__str__())

    def create_7z_file(self, pickle_files_to_add: list[str], file_name: str):
        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_file_path = os.path.join(tmp_dir, f"{file_name}.zip")
            with ZipFile(zip_file_path, "w") as zip_ref:
                for pickle_file in pickle_files_to_add:
                    zip_ref.write(
                        f"{PKL_DIR}/{pickle_file}",
                        f"/ICWSM19_data/{file_name}-{pickle_file}",
                    )
            args = [
                "7z",
                "a",
                os.path.join(
                    tmp_dir, self._save_dir, "files", f"{file_name}.zip.7z"
                ),
                zip_file_path,
            ]
            with subprocess.Popen(
                args=args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            ) as process:
                for line in process.stdout:
                    logger.debug(line.decode("utf-8").strip())
            df = pd.DataFrame(
                data={
                    "file_name": f"{file_name}.zip.7z",
                    "num_pickles": len(pickle_files_to_add),
                    "pickle_files": pickle_files_to_add,
                    "file_size": os.path.getsize(
                        f"{self._save_dir}/files/{file_name}.zip.7z"
                    ),
                }
            )
            with open(
                os.path.join(self._save_dir, "files.csv"),
                "a",
                encoding="UTF-8",
            ) as file_obj:
                df.to_csv(file_obj, index=False, header=file_obj.tell() == 0)
            logger.info("Created random file %s.zip.7z", file_name)
            return os.path.join(self._save_dir, "files", f"{file_name}.zip.7z")

    def create_file_with_given_pickle_names(
        self,
        pickle_file_names: list[str],
    ) -> str:
        return self.create_7z_file(pickle_file_names, uuid.uuid4().__str__())


class RandomFileCreatorToCertainFileSizeThread(threading.Thread):
    def __init__(
        self,
        lock: threading.Lock,
        save_dir: str,
        total_file_size_required: int,
        p_bar: enlighten.Counter,
        min_num_pickles: int,
        max_num_pickles: int,
    ):
        super().__init__()

        self.lock = lock
        self.save_dir = save_dir
        self.random_file_creator = RandomFileCreator(save_dir=save_dir)
        self.total_file_size_required = total_file_size_required
        self.p_bar = p_bar
        self.min_num_pickles = min_num_pickles
        self.max_num_pickles = max_num_pickles

    def _sum_file_sizes(self) -> int:
        if not os.path.exists(os.path.join(self.save_dir, "files")):
            return 0
        file_size_sum = sum(
            os.path.getsize(os.path.join(self.save_dir, "files", file))
            for file in os.listdir(os.path.join(self.save_dir, "files"))
        )
        logger.debug("Sum of file sizes: %s", file_size_sum)
        return int(file_size_sum)

    def _check_tmp_dir_file_size(self) -> bool:
        with self.lock:
            return self._sum_file_sizes() < self.total_file_size_required

    def run(self) -> None:
        while self._check_tmp_dir_file_size():
            new_file = self.random_file_creator.create_random_file(
                self.min_num_pickles, self.max_num_pickles
            )
            file_size = int(os.path.getsize(new_file) / 1024**2)
            with self.lock:
                self.p_bar.update(incr=file_size)


class RandomFileCreatorToNumberOfFilesThread(threading.Thread):
    def __init__(
        self,
        lock: threading.Lock,
        save_dir: str,
        number_of_files_required: int,
        p_bar: enlighten.Counter,
        min_num_pickles: int,
        max_num_pickles: int,
    ):
        super().__init__()

        self.lock = lock
        self.save_dir = save_dir
        self.number_of_files_required = number_of_files_required
        self.p_bar = p_bar
        self.random_file_creator = RandomFileCreator(save_dir=save_dir)
        self._number_of_files_created = 0
        self.min_num_pickles = min_num_pickles
        self.max_num_pickles = max_num_pickles

    def _check_number_of_files(self) -> bool:
        with self.lock:
            logger.debug(
                f"Number of files created: {self._number_of_files_created}, "
                f"Number of files required: {self.number_of_files_required}"
            )
            return (
                self._number_of_files_created < self.number_of_files_required
            )

    def run(self) -> None:
        while self._check_number_of_files():
            self.random_file_creator.create_random_file(
                self.min_num_pickles, self.max_num_pickles
            )
            with self.lock:
                self._number_of_files_created += 1
                self.p_bar.update()
