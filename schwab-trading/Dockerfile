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

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

# ── development stage ──────────────────────────────────────────────────────────
FROM base AS development

COPY pyproject.toml poetry.lock* README.md ./
RUN poetry install --no-root

COPY src ./src
RUN poetry install

CMD ["poetry", "run", "python", "-m", "schwab_trader"]

# ── production stage ───────────────────────────────────────────────────────────
FROM base AS production

COPY pyproject.toml poetry.lock* README.md ./
RUN poetry install --no-root --without dev

COPY src ./src
RUN poetry install --without dev

CMD ["poetry", "run", "python", "-m", "schwab_trader"]
