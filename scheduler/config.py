import os

from dynaconf import Dynaconf

current_directory = os.path.dirname(os.path.realpath(__file__))

# add here more folders and settings / secrets per
# whatever environment you need

settings = Dynaconf(
    root_path=current_directory,
    envvar_prefix="DYNACONF",
    env_switcher="ENV_FOR_DYNACONF",
    settings_files=["settings.toml", "secrets.toml"],
    environments=True,
)

# check dynaconf settings for any other variables and or
# configurations for your own project
