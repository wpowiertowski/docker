FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==2.4.0 \
    && poetry config virtualenvs.create false

WORKDIR /app

COPY pyproject.toml ./
# poetry lock generates poetry.lock on first build; install then follows it
RUN poetry lock && poetry install --only main --no-root

COPY app/ ./app/

EXPOSE 8080

CMD ["python", "-m", "app.main"]
