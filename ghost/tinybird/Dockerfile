FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    jq \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/tinybird

# Install Tinybird CLI
RUN curl -sSL https://install.tinybird.co | bash

ENV PATH="/root/.local/bin:${PATH}"

COPY handleLogin.sh /usr/local/bin/tinybird-login
COPY getTokens.sh /usr/local/bin/get-tokens
COPY tb-wrapper /usr/local/bin/tb-wrapper

RUN chmod +x /usr/local/bin/tinybird-login \
              /usr/local/bin/get-tokens \
              /usr/local/bin/tb-wrapper
