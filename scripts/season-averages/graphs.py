import math
import os

import pandas as pd
from PIL import Image
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator
from tqdm import tqdm

FIG_SIZE_H = 12

FIG_SIZE_W = 10

VALID_YEARS = range(2015, 2023)
VALID_DATA = [
    "solar",
    "wind_onshore",
    "wind_offshore",
    "forecasted_load",
    "actual_load",
]
VALID_DATA_NICE_NAMES = {
    "solar": "Day Ahead forecasted solar generation",
    "wind_onshore": "Day Ahead forecasted onshore wind generation",
    "wind_offshore": "Day Ahead forecasted offshore wind generation",
    "forecasted_load": "Day Ahead forecasted total load",
    "actual_load": "Actual total load",
}
Y_LIMITS = {
    "solar": 6000,
    "wind_onshore": 3000,
    "wind_offshore": 1500,
    "forecasted_load": 20000,
    "actual_load": 20000,
}
DATA_DIR = "data"
FIGURE_DIR = "figures"


def interactive_one_plot():
    # Ask user what year to show
    year_to_show = None
    while year_to_show not in VALID_YEARS:
        try:
            year_to_show = int(
                input(
                    f"Which year to show? ({VALID_YEARS[0]}-{VALID_YEARS[-1]}): "
                )
            )
        except ValueError:
            print("Invalid input. Please enter a valid year.")

    # Ask user what data to show
    data_to_show = None
    while data_to_show not in VALID_DATA:
        try:
            data_to_show = input(
                f"Which data to show? ({', '.join(VALID_DATA)}): "
            )
        except ValueError:
            print("Invalid input. Please enter a valid data type.")

    override_y_limits = ""
    while (
        not isinstance(override_y_limits, int)
        and override_y_limits is not None
        and override_y_limits != "auto"
    ):
        try:
            user_input = input(
                "Override y limits? If so, enter a number (MWh) "
                "or 'auto' for automatic, otherwise press enter: "
            )
            if user_input == "auto":
                override_y_limits = user_input
                break
            override_y_limits = int(user_input) if user_input != "" else None
        except ValueError:
            print("Invalid input. Please enter a valid number or nothing.")

    # Ask user what data to show
    show_title = None
    while show_title not in ["y", "n"]:
        try:
            show_title = input("Add plot title? (y/n): ")
        except ValueError:
            print("Invalid input. Please enter (y)es or (n)o.")
    show_title = show_title == "y"

    generate_plot(
        data_to_show,
        year_to_show,
        override_y_limits=override_y_limits,
        show_title=show_title,
    )


def generate_plot(
    data_to_show,
    year_to_show,
    save_figure=False,
    override_y_limits=None,
    show_title=True,
):
    seasons = [
        {
            "title": "Spring",
            "data": pd.read_csv(
                os.path.join(
                    DATA_DIR,
                    f"{year_to_show}_spring_{data_to_show}.csv",
                ),
            ),
        },
        {
            "title": "Summer",
            "data": pd.read_csv(
                os.path.join(
                    DATA_DIR,
                    f"{year_to_show}_summer_{data_to_show}.csv",
                ),
            ),
        },
        {
            "title": "Fall",
            "data": pd.read_csv(
                os.path.join(
                    DATA_DIR,
                    f"{year_to_show}_fall_{data_to_show}.csv",
                ),
            ),
        },
        {
            "title": "Winter",
            "data": pd.read_csv(
                os.path.join(
                    DATA_DIR,
                    f"{year_to_show}_winter_{data_to_show}.csv",
                ),
            ),
        },
    ]
    fig, axes = plt.subplots(
        4, figsize=(FIG_SIZE_W, FIG_SIZE_H), sharex="all", sharey="all"
    )
    fig.tight_layout(rect=(0.02, 0.03, 1, 0.95 if show_title else 0.99))
    for (i, season) in enumerate(seasons):
        data = season["data"]
        data["time"] = pd.to_datetime(
            data["hour"].astype(str) + ":" + data["minute"].astype(str),
            format="%H:%M",
        ).dt.time
        data.set_index("time")

        axes[i].plot(data.index, data["mean"].values, label="Mean")
        axes[i].plot(data.index, data["median"].values, label="Median")
        axes[i].fill_between(
            data.index,
            data["percentile_25"].values,
            data["percentile_75"].values,
            alpha=0.2,
            label="Inter-quartile range",
        )
        axes[i].set_xticks(
            data.index,
            data["time"].apply(lambda x: x.strftime("%H:%M")).values,
            rotation=90,
        )
        axes[i].xaxis.set_major_locator(MaxNLocator(nbins=21))
        axes[i].set_ylabel("MW")
        axes[i].title.set_text(f"{season['title']} {year_to_show}")
        axes[i].legend()
    if override_y_limits != "auto":
        for axes in fig.get_axes():
            axes.set_ylim(
                0,
                Y_LIMITS[data_to_show]
                if override_y_limits is None
                else override_y_limits,
            )
    plt.subplots_adjust(hspace=0.25)
    if show_title:
        fig.suptitle(
            f"Average {VALID_DATA_NICE_NAMES[data_to_show]} in {year_to_show}"
        )
    plt.xlabel("Time of day")

    if save_figure:
        # Create figure dir if not exists
        save_dir = os.path.join(FIGURE_DIR, data_to_show)
        os.makedirs(save_dir, exist_ok=True)

        plt.savefig(
            os.path.join(
                save_dir,
                f"{year_to_show}_{data_to_show}"
                f"{'' if show_title else '_no_title'}.png",
            ),
            bbox_inches="tight",
        )
        plt.close()
    else:
        plt.show()

    return fig


if __name__ == "__main__":
    # Ask user: Show just one plot of data, or generate all plots?
    # GENERATE_ALL = None
    GENERATE_ALL = None
    while GENERATE_ALL not in ["y", "n"]:
        try:
            GENERATE_ALL = input(
                "Generate all plots and save (y), or just show one plot (n)? (y/n): "
            )
        except ValueError:
            print("Invalid input. Please enter y or n.")
    GENERATE_ALL = GENERATE_ALL == "y"

    if GENERATE_ALL:
        for data in tqdm(VALID_DATA, desc="Data type"):
            for year in tqdm(VALID_YEARS, leave=False, desc="Year"):
                for show_title in tqdm(
                    [True, False], leave=False, desc="Title"
                ):
                    generate_plot(
                        data, year, save_figure=True, show_title=show_title
                    )

        # Put all figures of one data type next to each other in one figure
        for data in tqdm(VALID_DATA):
            img_paths = [
                os.path.join(FIGURE_DIR, data, f"{year}_{data}.png")
                for year in VALID_YEARS
            ]
            images = list(map(Image.open, img_paths))
            new_im = Image.new(
                "RGB", (images[0].width * 4, images[0].height * 2)
            )
            for i, im in enumerate(images):
                new_im.paste(
                    im, ((i % 4) * im.width, math.floor(i / 4) * im.height)
                )
            new_im.save(os.path.join(FIGURE_DIR, data, f"all_{data}.png"))
    else:
        interactive_one_plot()
