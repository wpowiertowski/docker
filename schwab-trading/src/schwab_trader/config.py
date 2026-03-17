"""Configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    app_key: str = os.environ["SCHWAB_APP_KEY"]
    app_secret: str = os.environ["SCHWAB_APP_SECRET"]
    callback_url: str = os.environ.get("SCHWAB_CALLBACK_URL", "https://127.0.0.1:8182")
    token_path: str = os.environ.get("SCHWAB_TOKEN_PATH", "/app/tokens/token.json")
    trading_mode: str = os.environ.get("TRADING_MODE", "paper")
    max_position_size: float = float(os.environ.get("MAX_POSITION_SIZE", "1000"))
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
