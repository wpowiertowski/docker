AMOUNT ?= 100000
TOP ?= 500

.PHONY: build run

build:
	docker build --pull --rm . -t devbox:latest

run:
	docker run --rm devbox:latest --amount $(AMOUNT) --top $(TOP)
