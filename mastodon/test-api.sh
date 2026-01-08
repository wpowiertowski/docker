#!/bin/bash
# Mastodon API Test Script
# This script performs basic API tests to verify the Mastodon instance is working

set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Error: .env file not found!"
    exit 1
fi

MASTODON_URL="https://${LOCAL_DOMAIN}"

echo "=================================="
echo "Mastodon API Test Suite"
echo "=================================="
echo "Testing against: $MASTODON_URL"
echo ""

# Test 1: Instance information
echo "Test 1: Getting instance information..."
response=$(curl -s "${MASTODON_URL}/api/v1/instance")
if [ $? -eq 0 ] && [ ! -z "$response" ]; then
    echo "✓ Instance API responding"
    echo "  Response preview: $(echo $response | head -c 100)..."
else
    echo "✗ Instance API failed"
    exit 1
fi
echo ""

# Test 2: Public timeline
echo "Test 2: Getting public timeline..."
response=$(curl -s "${MASTODON_URL}/api/v1/timelines/public")
if [ $? -eq 0 ]; then
    echo "✓ Public timeline API responding"
    echo "  Response: $(echo $response | head -c 100)..."
else
    echo "✗ Public timeline API failed"
    exit 1
fi
echo ""

# Test 3: Apps endpoint (for OAuth registration)
echo "Test 3: Testing apps endpoint..."
response=$(curl -s -X POST \
    -F 'client_name=Test App' \
    -F 'redirect_uris=urn:ietf:wg:oauth:2.0:oob' \
    -F 'scopes=read write follow' \
    -F 'website=https://example.com' \
    "${MASTODON_URL}/api/v1/apps")
if [ $? -eq 0 ] && [ ! -z "$response" ]; then
    echo "✓ Apps API responding"
    echo "  Response preview: $(echo $response | head -c 100)..."
else
    echo "✗ Apps API failed"
    exit 1
fi
echo ""

# Test 4: Health check
echo "Test 4: Health check endpoint..."
status=$(curl -s -o /dev/null -w "%{http_code}" "${MASTODON_URL}/health")
if [ "$status" = "200" ]; then
    echo "✓ Health check passed (HTTP $status)"
else
    echo "✗ Health check failed (HTTP $status)"
fi
echo ""

# Test 5: Streaming API health
echo "Test 5: Streaming API health check..."
status=$(curl -s -o /dev/null -w "%{http_code}" "${MASTODON_URL}/api/v1/streaming/health")
if [ "$status" = "200" ]; then
    echo "✓ Streaming API health check passed (HTTP $status)"
else
    echo "✗ Streaming API health check failed (HTTP $status)"
fi
echo ""

echo "=================================="
echo "All basic tests completed!"
echo "=================================="
echo ""
echo "Your Mastodon instance appears to be working correctly."
echo ""
echo "Next steps for integration testing:"
echo "  1. Create an application in Settings > Development"
echo "  2. Use the client credentials for API authentication"
echo "  3. Test with your integration app"
echo ""
