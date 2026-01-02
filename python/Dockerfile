FROM python:3.14-alpine AS base

ARG YOUR_ENV

ENV YOUR_ENV=${YOUR_ENV} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # Poetry's configuration:
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION=2.2.1

# install poetry and start a virtual environment
RUN pip install "poetry==$POETRY_VERSION"
RUN python -m venv /venv

# copy pyproject.toml to work area
WORKDIR /app
COPY README.md /app/
COPY pyproject.toml code /app/
COPY .vscode/launch.json /app/.vscode/

# run project from pyproject.toml
RUN poetry install
RUN poetry run app
