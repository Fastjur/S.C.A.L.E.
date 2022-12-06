FROM registry.access.redhat.com/ubi9/python-311:latest

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.6.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=0 \
    APP_WORKDIR=/app \
    NVM_DIR=/usr/local/nvm \
    LD_LIBRARY_PATH=/opt/oracle/instantclient_21_9

USER root

# Install oracle instant client
RUN ["dnf", "update", "-y"]
RUN ["dnf", "install", "-y", "libaio", "gcc"]
ADD lib/oracle-instantclient-basic-21.9.0.0.0-1.el8.x86_64.rpm ./oracle-instantclient-basic.rpm
#RUN ["rpm", "-i", "./oracle-instantclient-basic.rpm"]

# TODO: Below is just temporary, for debugging inside the container
RUN ["dnf", "install", "-y", "bind-utils", "iputils"]

RUN ["pip", "install", "--upgrade", "pip"]
RUN pip install poetry==${POETRY_VERSION}


# Install python dependencies
WORKDIR $APP_WORKDIR
COPY pyproject.toml poetry.lock ./
RUN ["poetry", "install", "--no-root", "--only", "main"]

# Install nvm
WORKDIR $APP_WORKDIR/frontend
COPY ./scheduler/frontend/.nvmrc ./
RUN mkdir -p "$NVM_DIR"
ADD https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh $NVM_DIR/install.sh
RUN chmod +x $NVM_DIR/install.sh \
    && /bin/bash -c "$NVM_DIR/install.sh"
RUN /bin/bash -c "source $NVM_DIR/nvm.sh --install && nvm use"

# Install frontend npm dependencies
WORKDIR $APP_WORKDIR/frontend
COPY ./scheduler/frontend/package.json ./scheduler/frontend/package-lock.json ./
RUN /bin/bash -c "source $NVM_DIR/nvm.sh && npm install"
# To avoid the "private key in docker image" security issue:
RUN ["rm", "node_modules/node-gyp/test/fixtures/server.key"]

COPY ./scheduler/frontend ./
RUN /bin/bash -c "source $NVM_DIR/nvm.sh && npm run build"

WORKDIR $APP_WORKDIR
COPY ./scheduler/ .

COPY ./entrypoint.sh ./entrypoint.sh
RUN ["chmod", "+x", "./entrypoint.sh"]

ARG ENV_FOR_DYNACONF=develop
ENV ENV_FOR_DYNACONF=${ENV_FOR_DYNACONF}

USER 1001

EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]

# Default command to run, can be overriden by providing a different command in the docker-compose.yml file
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--capture-output", "scheduler.wsgi"]
