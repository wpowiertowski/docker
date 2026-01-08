# Integration Testing Guide

This guide explains how to use the Mastodon test server for integration testing of Mastodon client applications.

## Overview

This Mastodon instance is specifically configured for testing:

- **Accessible via HTTPS** through Cloudflare tunnel
- **Open API access** for testing without restrictions
- **Persistent storage** for consistent testing
- **Full Mastodon API** support (REST and Streaming)
- **OAuth2 support** for authentication testing

## Testing Workflow

### 1. Initial Setup

Ensure your Mastodon instance is running:

```bash
./health-check.sh
```

### 2. Create a Test Application

#### Via Web UI:

1. Log in to your Mastodon instance
2. Go to Settings → Development
3. Click "New Application"
4. Fill in:
   - **Application name**: Your test app name
   - **Redirect URI**: `urn:ietf:wg:oauth:2.0:oob` (for token-based auth)
   - **Scopes**: Select the permissions you need (e.g., `read`, `write`, `follow`)
5. Save and copy:
   - Client Key (client_id)
   - Client Secret (client_secret)
   - Your access token

#### Via API:

```bash
curl -X POST \
  -F 'client_name=Test App' \
  -F 'redirect_uris=urn:ietf:wg:oauth:2.0:oob' \
  -F 'scopes=read write follow' \
  -F 'website=https://example.com' \
  https://your-domain.com/api/v1/apps
```

Save the response JSON containing `client_id` and `client_secret`.

### 3. Create Test Users

Create additional test users for multi-user testing:

```bash
# Create a regular test user
docker compose exec mastodon-web bash -c "RAILS_ENV=production bin/tootctl accounts create testuser --email test@example.com --confirmed"

# Create another test user
docker compose exec mastodon-web bash -c "RAILS_ENV=production bin/tootctl accounts create testuser2 --email test2@example.com --confirmed"
```

### 4. Test API Endpoints

#### Get Instance Info

```bash
curl https://your-domain.com/api/v1/instance
```

#### Verify Credentials (Authenticated)

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://your-domain.com/api/v1/accounts/verify_credentials
```

#### Post a Status

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F 'status=Hello from test!' \
  https://your-domain.com/api/v1/statuses
```

#### Get Home Timeline

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://your-domain.com/api/v1/timelines/home
```

### 5. Testing Streaming API

The streaming API allows real-time updates.

#### Test with curl:

```bash
curl -N -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://your-domain.com/api/v1/streaming/user
```

This will keep the connection open and stream events in real-time.

### 6. Testing OAuth Flow

For applications that need the full OAuth flow:

#### Step 1: Get Authorization Code

Direct users to:
```
https://your-domain.com/oauth/authorize?client_id=YOUR_CLIENT_ID&scope=read+write+follow&redirect_uri=urn:ietf:wg:oauth:2.0:oob&response_type=code
```

#### Step 2: Exchange Code for Token

```bash
curl -X POST \
  -F 'client_id=YOUR_CLIENT_ID' \
  -F 'client_secret=YOUR_CLIENT_SECRET' \
  -F 'redirect_uri=urn:ietf:wg:oauth:2.0:oob' \
  -F 'grant_type=authorization_code' \
  -F 'code=AUTHORIZATION_CODE' \
  https://your-domain.com/oauth/token
```

## Common Test Scenarios

### Testing Post Creation

```python
import requests

# Configuration
INSTANCE_URL = "https://your-domain.com"
ACCESS_TOKEN = "your_access_token"

# Headers
headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

# Create a post
response = requests.post(
    f"{INSTANCE_URL}/api/v1/statuses",
    headers=headers,
    data={"status": "Test post from integration test"}
)

print(response.json())
```

### Testing Follow/Unfollow

```python
# Follow a user
account_id = "1"  # ID of account to follow
response = requests.post(
    f"{INSTANCE_URL}/api/v1/accounts/{account_id}/follow",
    headers=headers
)

# Unfollow
response = requests.post(
    f"{INSTANCE_URL}/api/v1/accounts/{account_id}/unfollow",
    headers=headers
)
```

### Testing Media Upload

```python
# Upload media
with open("image.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post(
        f"{INSTANCE_URL}/api/v1/media",
        headers=headers,
        files=files
    )
    media_id = response.json()["id"]

# Create post with media
response = requests.post(
    f"{INSTANCE_URL}/api/v1/statuses",
    headers=headers,
    data={
        "status": "Post with image",
        "media_ids[]": media_id
    }
)
```

## Unit Test Example

Here's a simple unit test example using Python and pytest:

```python
import pytest
import requests

BASE_URL = "https://your-domain.com"
ACCESS_TOKEN = "your_access_token"

@pytest.fixture
def api_client():
    """Create an API client with authentication"""
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    })
    return session

def test_instance_accessible():
    """Test that instance is accessible"""
    response = requests.get(f"{BASE_URL}/api/v1/instance")
    assert response.status_code == 200
    assert "uri" in response.json()

def test_verify_credentials(api_client):
    """Test authentication works"""
    response = api_client.get(f"{BASE_URL}/api/v1/accounts/verify_credentials")
    assert response.status_code == 200
    data = response.json()
    assert "username" in data

def test_post_status(api_client):
    """Test posting a status"""
    response = api_client.post(
        f"{BASE_URL}/api/v1/statuses",
        data={"status": "Test post"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "<p>Test post</p>"
    
    # Clean up
    status_id = data["id"]
    api_client.delete(f"{BASE_URL}/api/v1/statuses/{status_id}")

def test_get_timeline(api_client):
    """Test getting home timeline"""
    response = api_client.get(f"{BASE_URL}/api/v1/timelines/home")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## Environment Variables for Testing

For your test suite, you can use environment variables:

```bash
export MASTODON_INSTANCE_URL="https://your-domain.com"
export MASTODON_ACCESS_TOKEN="your_access_token"
export MASTODON_CLIENT_ID="your_client_id"
export MASTODON_CLIENT_SECRET="your_client_secret"
```

Then in your tests:

```python
import os

INSTANCE_URL = os.getenv("MASTODON_INSTANCE_URL")
ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN")
```

## Troubleshooting Tests

### API Returns 401 Unauthorized

- Check that your access token is valid
- Verify the token has the required scopes
- Ensure the token is included in the Authorization header

### API Returns 422 Unprocessable Entity

- Check that all required parameters are included
- Verify parameter formats (e.g., media_ids must be an array)
- Check error message in response for specific issue

### Connection Timeouts

- Verify the instance is running: `./health-check.sh`
- Check if Cloudflare tunnel is active: `docker compose logs mastodon-tunnel`
- Test with curl first to isolate the issue

### Streaming API Not Working

- Ensure you're using the streaming endpoint, not the REST API
- Check that the connection stays open (use `-N` flag with curl)
- Verify the access token has the required scopes

## Best Practices

1. **Use separate test accounts** - Don't test with your admin account
2. **Clean up after tests** - Delete test posts, unfollows, etc.
3. **Use unique identifiers** - Include timestamps or UUIDs in test data
4. **Test error cases** - Not just happy paths
5. **Respect rate limits** - Even though this is a test server
6. **Mock external services** - If your app integrates with other services
7. **Use fixtures** - For consistent test data setup

## Resources

- [Mastodon API Documentation](https://docs.joinmastodon.org/api/)
- [API Methods Reference](https://docs.joinmastodon.org/methods/)
- [OAuth Documentation](https://docs.joinmastodon.org/spec/oauth/)
- [Mastodon.py (Python Library)](https://mastodonpy.readthedocs.io/)

## Support

If you encounter issues with the test server:

1. Check service health: `./health-check.sh`
2. View logs: `docker compose logs -f mastodon-web`
3. Verify API: `./test-api.sh`
4. Check the main README.md for troubleshooting
