#!/bin/bash
# Mastodon Setup Helper Script
# This script helps generate the required secrets and set up the environment

set -e

echo "=================================="
echo "Mastodon Setup Helper"
echo "=================================="
echo ""

# Check if .env already exists
if [ -f .env ]; then
    echo "Warning: .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting. Please backup your .env file if needed."
        exit 1
    fi
fi

# Copy example file
cp .env.example .env

echo "Generating Mastodon secrets..."
echo ""
echo "Note: Using official Mastodon image to generate cryptographically secure secrets."
echo "This ensures compatibility with Mastodon's requirements."
echo ""

# Generate SECRET_KEY_BASE
# Using official Mastodon rake tasks ensures proper secret generation
echo "Generating SECRET_KEY_BASE..."
SECRET_KEY_BASE=$(docker run --rm -it tootsuite/mastodon:latest bundle exec rake secret | tr -d '\r')
sed -i "s|SECRET_KEY_BASE=.*|SECRET_KEY_BASE=${SECRET_KEY_BASE}|g" .env

# Generate OTP_SECRET
echo "Generating OTP_SECRET..."
OTP_SECRET=$(docker run --rm -it tootsuite/mastodon:latest bundle exec rake secret | tr -d '\r')
sed -i "s|OTP_SECRET=.*|OTP_SECRET=${OTP_SECRET}|g" .env

# Generate VAPID keys
echo "Generating VAPID keys..."
VAPID_OUTPUT=$(docker run --rm -it tootsuite/mastodon:latest bundle exec rake mastodon:webpush:generate_vapid_key)
VAPID_PRIVATE=$(echo "$VAPID_OUTPUT" | grep "VAPID_PRIVATE_KEY" | cut -d'=' -f2 | tr -d '\r')
VAPID_PUBLIC=$(echo "$VAPID_OUTPUT" | grep "VAPID_PUBLIC_KEY" | cut -d'=' -f2 | tr -d '\r')

sed -i "s|VAPID_PRIVATE_KEY=.*|VAPID_PRIVATE_KEY=${VAPID_PRIVATE}|g" .env
sed -i "s|VAPID_PUBLIC_KEY=.*|VAPID_PUBLIC_KEY=${VAPID_PUBLIC}|g" .env

echo ""
echo "✓ Secrets generated successfully!"
echo ""
echo "Now you need to configure the following manually in .env:"
echo "  - LOCAL_DOMAIN: Your domain name"
echo "  - DB_PASSWORD: A secure database password"
echo "  - TUNNEL_TOKEN: Your Cloudflare tunnel token"
echo ""

# Prompt for domain
read -p "Enter your domain name (e.g., mastodon.example.com): " domain
if [ ! -z "$domain" ]; then
    sed -i "s|LOCAL_DOMAIN=.*|LOCAL_DOMAIN=${domain}|g" .env
    echo "✓ Domain set to: $domain"
fi

# Prompt for database password
read -p "Enter a secure database password: " db_pass
if [ ! -z "$db_pass" ]; then
    sed -i "s|DB_PASSWORD=.*|DB_PASSWORD=${db_pass}|g" .env
    echo "✓ Database password set"
fi

# Prompt for tunnel token
echo ""
echo "To get your Cloudflare tunnel token:"
echo "  1. Go to https://one.dash.cloudflare.com/"
echo "  2. Navigate to Networks > Tunnels"
echo "  3. Create or select a tunnel"
echo "  4. Copy the tunnel token"
echo ""
read -p "Enter your Cloudflare tunnel token (press Enter to skip): " tunnel_token
if [ ! -z "$tunnel_token" ]; then
    sed -i "s|TUNNEL_TOKEN=.*|TUNNEL_TOKEN=${tunnel_token}|g" .env
    echo "✓ Tunnel token set"
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Create Docker resources:"
echo "     docker volume create mastodon-db"
echo "     docker volume create mastodon-redis"
echo "     docker volume create mastodon-public-system"
echo "     docker network create mastodon"
echo ""
echo "  2. Start the services:"
echo "     docker compose up -d"
echo ""
echo "  3. Create an admin user (after services are up):"
echo "     docker compose exec mastodon-web bash -c \"RAILS_ENV=production bin/tootctl accounts create admin --email admin@example.com --confirmed --role Owner\""
echo ""
