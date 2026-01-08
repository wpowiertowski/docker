# Quick Start Guide

This is a condensed guide to get your Mastodon test server up and running quickly.

## Prerequisites

- Docker and Docker Compose installed
- A Cloudflare account with Tunnel configured
- A domain name

## Quick Setup (5 minutes)

### 1. Run the setup script

```bash
cd mastodon
./setup.sh
```

This will:
- Generate all required secrets
- Create a `.env` file
- Prompt you for domain, database password, and tunnel token

### 2. Create Docker resources

```bash
docker volume create mastodon-db
docker volume create mastodon-redis
docker volume create mastodon-public-system
docker network create mastodon
```

### 3. Start the services

```bash
# Standard mode (accessible via Cloudflare tunnel only)
docker compose up -d

# OR for local testing with exposed ports
docker compose -f compose.yml -f compose.test.yml up -d
```

### 4. Wait for services to be ready

Check status:
```bash
docker compose ps
```

Wait for all services to show as "healthy" (may take 3-5 minutes on first run).

### 5. Create an admin user

```bash
docker compose exec mastodon-web bash -c "RAILS_ENV=production bin/tootctl accounts create admin --email admin@example.com --confirmed --role Owner"
```

Save the generated password!

### 6. Test the API

```bash
./test-api.sh
```

## You're Done! 🎉

Your Mastodon instance is now running at `https://your-domain.com`

## For Integration Testing

1. Log in to your instance
2. Go to Settings > Development
3. Create a new application
4. Copy the access token
5. Use it in your integration tests:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://your-domain.com/api/v1/accounts/verify_credentials
```

## Useful Commands

```bash
# View logs
docker compose logs -f

# Restart all services
docker compose restart

# Stop all services
docker compose down

# Access Rails console
docker compose exec mastodon-web bash -c "RAILS_ENV=production bin/rails console"

# Run tootctl commands
docker compose exec mastodon-web bash -c "RAILS_ENV=production bin/tootctl help"
```

## Troubleshooting

If something goes wrong:

1. Check the logs: `docker compose logs -f mastodon-web`
2. Ensure all environment variables are set in `.env`
3. Verify Cloudflare tunnel is configured correctly
4. Try restarting: `docker compose restart`

For more detailed information, see the main README.md file.
