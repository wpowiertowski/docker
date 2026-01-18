.PHONY: build run stop clean logs shell help

help:
	@echo "VCMI Docker - Available targets:"
	@echo ""
	@echo "  make build       - Build the Docker image (may take 15-30 minutes)"
	@echo "  make run         - Run the container with vcmi-data volume"
	@echo "  make stop        - Stop the running container"
	@echo "  make clean       - Stop and remove the container"
	@echo "  make logs        - Show container logs"
	@echo "  make shell       - Open shell in running container"
	@echo "  make start-game  - Start the VCMI launcher via supervisor"
	@echo ""
	@echo "Access the web GUI at: http://localhost:6080"

build:
	docker build --pull --rm -t vcmi:latest .

# Build for ARM64 specifically
build-arm64:
	docker buildx build --platform linux/arm64 --pull --rm -t vcmi:arm64 .

# Build for AMD64
build-amd64:
	docker buildx build --platform linux/amd64 --pull --rm -t vcmi:amd64 .

run:
	@mkdir -p vcmi-data
	docker run -d \
		-p 6080:6080 \
		-v $$(pwd)/vcmi-data:/home/vcmi/.local/share/vcmi \
		--name vcmi \
		vcmi:latest

stop:
	docker stop vcmi || true

clean: stop
	docker rm vcmi || true

logs:
	docker logs -f vcmi

shell:
	docker exec -it vcmi bash

# Start the VCMI launcher via supervisorctl
start-game:
	docker exec -it vcmi supervisorctl start vcmilauncher

# Show supervisor status
supervisor-status:
	docker exec -it vcmi supervisorctl status
