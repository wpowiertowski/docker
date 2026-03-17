IMAGE   := schwab-trader
TAG     := dev
COMPOSE := docker compose

.PHONY: build up down logs shell jupyter test lint format

build:
	docker build --pull --rm --target development -t $(IMAGE):$(TAG) .

up:
	$(COMPOSE) up -d trader

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f trader

shell:
	$(COMPOSE) exec trader poetry run python

jupyter:
	$(COMPOSE) --profile jupyter up -d jupyter
	@echo "Jupyter Lab → http://localhost:8888"

test:
	$(COMPOSE) exec trader poetry run pytest tests/ -v

lint:
	$(COMPOSE) exec trader poetry run ruff check src/
	$(COMPOSE) exec trader poetry run mypy src/

format:
	$(COMPOSE) exec trader poetry run black src/
	$(COMPOSE) exec trader poetry run ruff check --fix src/
