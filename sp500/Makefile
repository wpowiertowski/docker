AMOUNT ?= 100000
MAX_STOCKS ?= 100
US_WEIGHT ?= 0.60
BASKET_SIZE ?= 50
OUT_DIR ?= $(CURDIR)/out

.PHONY: build run baskets basket-csvs

build:
	docker build --pull --rm . -t devbox:latest

run:
	docker run --rm devbox:latest --amount $(AMOUNT) --max-stocks $(MAX_STOCKS) --us-weight $(US_WEIGHT)

baskets:
	docker run --rm devbox:latest --amount $(AMOUNT) --max-stocks $(MAX_STOCKS) --us-weight $(US_WEIGHT) --top 1 --baskets --basket-size $(BASKET_SIZE)

basket-csvs:
	mkdir -p $(OUT_DIR)
	docker run --rm -v $(OUT_DIR):/out devbox:latest --amount $(AMOUNT) --max-stocks $(MAX_STOCKS) --us-weight $(US_WEIGHT) --basket-csv-prefix /out/basket --basket-size $(BASKET_SIZE)
