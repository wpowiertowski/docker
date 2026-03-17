"""Schwab OAuth2 authentication helpers."""

import schwab
from loguru import logger
from .config import Config


def get_client(config: Config) -> schwab.client.Client:
    """Return an authenticated Schwab client, refreshing the token if needed."""
    try:
        client = schwab.auth.client_from_token_file(
            config.token_path,
            config.app_key,
            config.app_secret,
        )
        logger.info("Loaded existing Schwab token from {}", config.token_path)
    except FileNotFoundError:
        logger.info("No token file found — starting OAuth flow")
        client = schwab.auth.client_from_login_flow(
            config.app_key,
            config.app_secret,
            config.callback_url,
            config.token_path,
        )
        logger.info("Token saved to {}", config.token_path)
    return client
