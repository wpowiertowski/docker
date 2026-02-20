#!/bin/bash
set -e

TINYB_FILE="/home/tinybird/.tinyb"

if [ ! -f "$TINYB_FILE" ]; then
    echo "Error: Not logged in to Tinybird." >&2
    echo "Run: docker compose run --rm tinybird-login" >&2
    exit 1
fi

TOKEN=$(jq -r '.token' "$TINYB_FILE")
HOST=$(jq -r '.host' "$TINYB_FILE")
WORKSPACE_ID=$(jq -r '.id' "$TINYB_FILE")

for VAR in TOKEN HOST WORKSPACE_ID; do
    VAL="${!VAR}"
    if [ -z "$VAL" ] || [ "$VAL" = "null" ]; then
        echo "Error: Missing $VAR in $TINYB_FILE" >&2
        exit 1
    fi
done

RESPONSE=$(curl -s -H "Authorization: Bearer ${TOKEN}" "${HOST}/v0/tokens/")

ADMIN_TOKEN=$(echo "$RESPONSE" | jq -r '.tokens[] | select(.name == "workspace admin token") | .token')
TRACKER_TOKEN=$(echo "$RESPONSE" | jq -r '.tokens[] | select(.name == "tracker") | .token')

echo ""
echo "Add the following to your .env file:"
echo ""
echo "TINYBIRD_WORKSPACE_ID=${WORKSPACE_ID}"
echo "TINYBIRD_API_URL=${HOST}"
echo "TINYBIRD_ADMIN_TOKEN=${ADMIN_TOKEN}"
echo "TINYBIRD_TRACKER_TOKEN=${TRACKER_TOKEN}"
