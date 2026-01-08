# Makefile for Mastodon Docker Compose Setup

.PHONY: help setup volumes network up down restart logs health test clean

help:
	@echo "Mastodon Docker Compose Management"
	@echo ""
	@echo "Available targets:"
	@echo "  setup      - Run setup wizard to generate secrets and .env file"
	@echo "  volumes    - Create required Docker volumes"
	@echo "  network    - Create required Docker network"
	@echo "  up         - Start all services (standard mode)"
	@echo "  up-test    - Start all services with exposed ports for local testing"
	@echo "  down       - Stop all services"
	@echo "  restart    - Restart all services"
	@echo "  logs       - View logs from all services"
	@echo "  health     - Check health status of all services"
	@echo "  test       - Run API tests"
	@echo "  clean      - Stop services and remove volumes (WARNING: deletes data!)"
	@echo "  admin      - Create an admin user"

setup:
	./setup.sh

volumes:
	docker volume create mastodon-db
	docker volume create mastodon-redis
	docker volume create mastodon-public-system
	@echo "✓ Volumes created"

network:
	docker network create mastodon
	@echo "✓ Network created"

up:
	docker compose up -d

up-test:
	docker compose -f compose.yml -f compose.test.yml up -d

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

health:
	./health-check.sh

test:
	./test-api.sh

admin:
	@echo "Creating admin user..."
	@read -p "Enter username: " username; \
	read -p "Enter email: " email; \
	docker compose exec mastodon-web bash -c "RAILS_ENV=production bin/tootctl accounts create $$username --email $$email --confirmed --role Owner"

clean:
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (yes/NO): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker compose down -v; \
		docker volume rm mastodon-db mastodon-redis mastodon-public-system || true; \
		docker network rm mastodon || true; \
		echo "✓ Cleaned up"; \
	else \
		echo "Cancelled"; \
	fi
