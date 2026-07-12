AMOUNT ?= 100000
TOP ?= 500
BASKET_SIZE ?= 50
OUT_DIR ?= $(CURDIR)/out

.PHONY: build run baskets basket-csvs

build:
	docker build --pull --rm . -t devbox:latest

run:
	docker run --rm devbox:latest --amount $(AMOUNT) --top $(TOP)

baskets:
	docker run --rm devbox:latest --amount $(AMOUNT) --top 1 --baskets --basket-size $(BASKET_SIZE)

basket-csvs:
	mkdir -p $(OUT_DIR)
	docker run --rm -v $(OUT_DIR):/out devbox:latest --amount $(AMOUNT) --top 1 --basket-size $(BASKET_SIZE) --basket-csv-prefix /out/basket
