AMOUNT ?= 100000
MAX_STOCKS ?= 100
US_WEIGHT ?= 0.60

.PHONY: build run

build:
	docker build --pull --rm . -t devbox:latest

run:
	docker run --rm devbox:latest --amount $(AMOUNT) --max-stocks $(MAX_STOCKS) --us-weight $(US_WEIGHT)
