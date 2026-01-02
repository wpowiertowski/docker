# About

Simple hello-world demo inside docker with VSCode debug hooks and poetry dependency setup

## Instructions

### Build

```shell
docker build --pull --rm . -t hello:latest
```

### Run standalone

```shell
docker run hello:latest
```

### Debug in VSCode

- install "Container Tools"
- run container in interactive mode
- right-click running container -> "Attach VSCode"
- start debugging in the debug panel (may get prompted to install debugpy)