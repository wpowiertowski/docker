# Schwab Trading — Docker Dev Environment

Python 3.12 development environment for automated stock trading using the
[Charles Schwab API](https://developer.schwab.com) via
[schwab-py](https://schwab-py.readthedocs.io/).

## Quick start

### 1. Register an app with Schwab

1. Go to <https://developer.schwab.com> and create an account.
2. Create a new app and note the **App Key** and **App Secret**.
3. Set the callback URL to `https://127.0.0.1:8182`.

### 2. Configure environment

```bash
cp .env.example .env
# edit .env and fill in SCHWAB_APP_KEY and SCHWAB_APP_SECRET
```

### 3. Build and run

```bash
make build    # build the Docker image
make up       # start the trader container
make logs     # tail logs
```

On first run the container will open a browser window for the Schwab OAuth
flow. Complete the login and paste the redirect URL when prompted. The token
is saved to `./tokens/token.json` and reused on subsequent starts.

### 4. Interactive shell

```bash
make shell    # drops into an ipython REPL with all deps available
```

### 5. Jupyter Lab (optional)

```bash
make jupyter  # starts Jupyter at http://localhost:8888
```

## Project layout

```
schwab-trading/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
├── tokens/          # OAuth token (git-ignored)
├── data/            # downloaded market data (git-ignored)
├── notebooks/       # Jupyter notebooks
└── src/
    └── schwab_trader/
        ├── __init__.py
        ├── __main__.py   # entry point
        ├── auth.py       # OAuth helpers
        └── config.py     # env-based config
```

## Key dependencies

| Package | Purpose |
|---|---|
| `schwab-py` | Official-style Schwab REST + streaming API client |
| `pandas` / `numpy` | Data manipulation and numerical computing |
| `httpx` | Async HTTP |
| `schedule` | Cron-style task scheduling |
| `loguru` | Structured logging |
| `jupyter` (dev) | Interactive analysis |
| `pytest` (dev) | Testing |
| `black` / `ruff` / `mypy` (dev) | Code quality |

## Trading modes

Set `TRADING_MODE=paper` in `.env` to prevent live order submission while
developing strategies. Switch to `live` only when ready.
