FROM python:3.12-slim AS base

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION=2.2.1

# Install par2cmdline-turbo and Poetry
RUN apt-get update \
    && apt-get install -y --no-install-recommends par2 \
    && rm -rf /var/lib/apt/lists/* \
    && pip install "poetry==$POETRY_VERSION"

WORKDIR /app
COPY README.md pyproject.toml /app/
COPY code /app/

RUN poetry install --only main

# Catalog persisted via mounted volume
VOLUME ["/root/.photovault"]

ENTRYPOINT ["poetry", "run", "photovault"]
CMD ["--help"]
