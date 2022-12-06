FROM registry.access.redhat.com/ubi9/python-311:latest

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=.:./scheduler \
    POETRY_VERSION=1.6.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    APP_WORKDIR=/app

USER root

# TODO: Below is just temporary, for debugging inside the container
RUN ["dnf", "install", "-y", "bind-utils", "iputils"]

RUN ["pip", "install", "--upgrade", "pip"]
RUN pip install poetry==${POETRY_VERSION}


# Install python dependencies
WORKDIR $APP_WORKDIR
COPY pyproject.toml poetry.lock ./
RUN ["poetry", "install", "--only", "main,synthetics", "--no-root"]

USER 1001

WORKDIR $APP_WORKDIR
COPY scheduler ./scheduler

CMD ["python3.11", "scheduler/synthetic/synthetic-gfc/src/main.py"]
