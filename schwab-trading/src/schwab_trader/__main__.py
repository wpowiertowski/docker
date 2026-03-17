"""Entry point — demonstrates a basic quote fetch."""

from loguru import logger
from .config import Config
from .auth import get_client


def main() -> None:
    config = Config()
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=config.log_level)

    logger.info("Trading mode: {}", config.trading_mode)

    client = get_client(config)

    # Example: fetch a quote for Apple
    response = client.get_quote("AAPL")
    response.raise_for_status()
    data = response.json()
    price = data["AAPL"]["quote"]["lastPrice"]
    logger.info("AAPL last price: ${:.2f}", price)


if __name__ == "__main__":
    main()
