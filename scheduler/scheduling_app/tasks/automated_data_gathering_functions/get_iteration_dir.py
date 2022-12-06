import os

import pandas as pd


def get_iteration_dir(base_dir: str):
    now = pd.Timestamp.now()
    iteration_dir_name = os.path.join(
        base_dir, now.strftime("%Y-%m-%d_%H-%M-%S")
    )
    os.makedirs(iteration_dir_name, exist_ok=True)
    return iteration_dir_name
