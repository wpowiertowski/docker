# About

Simple SP500 rebalancer takes the dollar amount to invest and stocks you want to exclude and produces how much of each SP500 stock to buy today.

## Instructions

### Build

```shell
docker build --pull --rm . -t devbox:latest
```

### Run standalone

```shell
docker run --rm devbox:latest --amount 100000
```

With a custom exclusion list and top-N preview:

```shell
docker run --rm devbox:latest --amount 100000 --exclude TSLA,MSFT,NVDA --top 20
```

### Debug in VSCode

- install "Container Tools"
- run container in interactive mode
- right-click running container -> "Attach VSCode"
- start debugging in the debug panel (may get prompted to install debugpy)
