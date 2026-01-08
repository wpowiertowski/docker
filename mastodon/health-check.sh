# Mastodon Health Check Script
# This script checks if all Mastodon services are healthy and ready

#!/bin/bash

set -e

echo "Checking Mastodon service health..."
echo ""

# Check if services are running
echo "Service Status:"
docker compose ps

echo ""
echo "Checking health status..."

# Check each service
services=("mastodon-db" "mastodon-redis" "mastodon-web" "mastodon-streaming" "mastodon-sidekiq" "mastodon-tunnel")

all_healthy=true

for service in "${services[@]}"; do
    status=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "no healthcheck")
    
    if [ "$status" = "healthy" ]; then
        echo "✓ $service: healthy"
    elif [ "$status" = "no healthcheck" ]; then
        # Check if it's running at least
        running=$(docker inspect --format='{{.State.Running}}' "$service" 2>/dev/null || echo "false")
        if [ "$running" = "true" ]; then
            echo "○ $service: running (no healthcheck)"
        else
            echo "✗ $service: not running"
            all_healthy=false
        fi
    else
        echo "✗ $service: $status"
        all_healthy=false
    fi
done

echo ""

if [ "$all_healthy" = true ]; then
    echo "All services are healthy! ✓"
    echo ""
    echo "You can now:"
    echo "  - Access the web UI (if tunnel is configured)"
    echo "  - Run test-api.sh to test the API"
    echo "  - Create an admin user if not done yet"
    exit 0
else
    echo "Some services are not healthy yet. Please wait or check logs."
    echo "Run: docker compose logs -f"
    exit 1
fi
