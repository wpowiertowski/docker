# Mastodon Test Server

A Mastodon server Docker Compose setup configured as a test target for running unit tests of Mastodon integration applications. The server is exposed to the internet using Cloudflare Tunnel.

## Purpose

This setup provides a fully functional Mastodon instance that can be used for:
- Testing Mastodon API integrations
- Running unit tests against a real Mastodon server
- Development and testing of Mastodon client applications
- Integration testing for POSSE (Publish on your Own Site, Syndicate Elsewhere) workflows

## Architecture

The setup includes the following services:

- **mastodon-web**: Main Mastodon web application (Rails)
- **mastodon-streaming**: Streaming API server (Node.js)
- **mastodon-sidekiq**: Background job processor
- **mastodon-db**: PostgreSQL database
- **mastodon-redis**: Redis for caching and queues
- **mastodon-tunnel**: Cloudflare tunnel for internet exposure

## Prerequisites

1. Docker and Docker Compose installed
2. A Cloudflare account with a tunnel configured
3. A domain name configured to use the Cloudflare tunnel

## Setup Instructions

### 1. Generate Mastodon Secrets

Generate the required secrets using the official Mastodon image:

```bash
# Generate SECRET_KEY_BASE and OTP_SECRET
docker run --rm -it tootsuite/mastodon:latest bundle exec rake secret
# Run this twice to get both SECRET_KEY_BASE and OTP_SECRET

# Generate VAPID keys
docker run --rm -it tootsuite/mastodon:latest bundle exec rake mastodon:webpush:generate_vapid_key
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` and set:
- `LOCAL_DOMAIN`: Your domain name (e.g., mastodon.example.com)
- `DB_PASSWORD`: A secure password for PostgreSQL
- `SECRET_KEY_BASE`: First secret generated above
- `OTP_SECRET`: Second secret generated above
- `VAPID_PRIVATE_KEY`: From VAPID generation
- `VAPID_PUBLIC_KEY`: From VAPID generation
- `TUNNEL_TOKEN`: Your Cloudflare tunnel token

### 3. Create Docker Resources

Create the required Docker volumes and network:

```bash
docker volume create mastodon-db
docker volume create mastodon-redis
docker volume create mastodon-public-system
docker network create mastodon
```

### 4. Configure Cloudflare Tunnel

1. Go to https://one.dash.cloudflare.com/
2. Navigate to Networks > Tunnels
3. Create a new tunnel or use an existing one
4. Configure a public hostname:
   - Public hostname: Your domain (e.g., mastodon.example.com)
   - Service: http://mastodon-web:3000
5. Copy the tunnel token to your `.env` file

### 5. Start the Services

```bash
docker compose up -d
```

Wait for all services to be healthy (this may take a few minutes on first run):

```bash
docker compose ps
```

### 6. Create Admin User

Once all services are running, create an admin user:

```bash
docker compose exec mastodon-web bash -c "RAILS_ENV=production bin/tootctl accounts create \
  admin \
  --email admin@example.com \
  --confirmed \
  --role Owner"
```

This will output a password. Save it securely.

### 7. Access Your Instance

Visit your configured domain (e.g., https://mastodon.example.com) and log in with the admin credentials.

## Test Configuration

This setup is optimized for testing:

- Email verification is disabled
- Open registration is enabled (can be changed in settings)
- Federation is enabled but not restricted
- Database migrations run automatically on startup
- The instance seeds with default data

## API Testing

You can test the Mastodon API at:
- REST API: `https://your-domain.com/api/v1/`
- Streaming API: `https://your-domain.com/api/v1/streaming/`

Example API test:

```bash
# Get instance information
curl https://your-domain.com/api/v1/instance

# Get public timeline
curl https://your-domain.com/api/v1/timelines/public
```

## Obtaining API Credentials for Testing

To create an API application for testing:

1. Log in to your Mastodon instance
2. Go to Settings > Development
3. Click "New Application"
4. Fill in the details:
   - Application name: Your test app name
   - Scopes: Select the permissions you need
5. Save and copy the access token for your tests

## Maintenance

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f mastodon-web
```

### Restart Services

```bash
docker compose restart
```

### Stop Services

```bash
docker compose down
```

### Update Mastodon

```bash
docker compose pull
docker compose up -d
```

## Troubleshooting

### Services won't start

Check logs for specific errors:
```bash
docker compose logs mastodon-web
docker compose logs mastodon-db
```

### Database migration errors

Reset and rebuild the database:
```bash
docker compose down
docker volume rm mastodon-db
docker volume create mastodon-db
docker compose up -d
```

### Can't access via domain

1. Check Cloudflare tunnel status:
   ```bash
   docker compose logs mastodon-tunnel
   ```
2. Verify tunnel configuration in Cloudflare dashboard
3. Ensure `LOCAL_DOMAIN` in `.env` matches your configured domain

## Security Notes

This setup is designed for testing purposes. For production use:

1. Enable email verification (configure SMTP settings)
2. Consider enabling `SINGLE_USER_MODE` or limiting registrations
3. Configure `AUTHORIZED_FETCH` for privacy
4. Use strong, unique passwords and secrets
5. Regularly update the Mastodon image
6. Consider using `LIMITED_FEDERATION_MODE` for isolated testing

## Resources

- [Mastodon Documentation](https://docs.joinmastodon.org/)
- [Mastodon API Documentation](https://docs.joinmastodon.org/api/)
- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
