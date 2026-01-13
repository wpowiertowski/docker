.PHONY: build run stop clean test help

# Default model name (can be overridden)
MODEL_NAME ?= llama-3.2-11b-vision-instruct-q4_k_m.gguf

help:
	@echo "Llama Vision Docker - Available targets:"
	@echo ""
	@echo "  make build       - Build the Docker image"
	@echo "  make run         - Run the container with models volume"
	@echo "  make stop        - Stop the running container"
	@echo "  make clean       - Stop and remove the container"
	@echo "  make logs        - Show container logs"
	@echo "  make test        - Run API tests"
	@echo "  make shell       - Open shell in running container"
	@echo "  make health      - Check service health"
	@echo ""
	@echo "Environment variables:"
	@echo "  MODEL_NAME       - Model filename (default: $(MODEL_NAME))"

build:
	docker build --pull --rm -t llama-vision:latest .

run:
	docker run -d \
		-p 5000:5000 \
		-v $$(pwd)/models:/models \
		-e MODEL_NAME=$(MODEL_NAME) \
		--name llama-vision \
		llama-vision:latest

stop:
	docker stop llama-vision || true

clean: stop
	docker rm llama-vision || true

logs:
	docker logs -f llama-vision

shell:
	docker exec -it llama-vision /bin/bash

health:
	@echo "Checking health..."
	@curl -s http://localhost:5000/health | python -m json.tool

test:
	python test_api.py

# Docker compose targets
compose-up:
	docker compose up -d

compose-down:
	docker compose down

compose-logs:
	docker compose logs -f

compose-build:
	docker compose build
