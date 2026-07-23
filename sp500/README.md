# About

Simplified blended rebalancer for **S&P 500 + FTSE Developed (ex-US)**.

Pulls live SPY (S&P 500) and VEA (FTSE Developed Markets ex-US) holdings,
applies your exclusion list, then caps the buy list to the top N names by
blended weight (default **100**) so the plan can actually be executed by a
single trader.

## Instructions

### Build

```shell
docker build --pull --rm . -t devbox:latest
```

### Run standalone

```shell
docker run --rm devbox:latest --amount 100000
```

Default behaviour: 60% S&P 500 / 40% FTSE Developed ex-US, capped at 100
holdings, with the built-in exclusion list (TSLA, MSFT, NVDA, INTC, AMD,
DELL, HPQ, ORCL, PLTR).

Custom exclusion and tighter cap:

```shell
docker run --rm devbox:latest --amount 100000 \
  --exclude TSLA,MSFT,NVDA --max-stocks 50
```

Different US/International split, write a CSV:

```shell
docker run --rm devbox:latest --amount 100000 \
  --us-weight 0.7 --csv plan.csv
```

US-only or International-only:

```shell
docker run --rm devbox:latest --amount 100000 --us-only
docker run --rm devbox:latest --amount 100000 --intl-only
```

### Debug in VSCode

- install "Container Tools"
- run container in interactive mode
- right-click running container -> "Attach VSCode"
- start debugging in the debug panel (may get prompted to install debugpy)
