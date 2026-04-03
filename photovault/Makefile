IMAGE ?= photovault
TAG   ?= latest

build:
	docker build --pull --rm . -t $(IMAGE):$(TAG)

run:
	docker run --rm \
	  -v ~/.photovault:/root/.photovault \
	  -e PHOTOVAULT_B2_KEY_ID \
	  -e PHOTOVAULT_B2_APP_KEY \
	  -e PHOTOVAULT_B2_BUCKET \
	  $(IMAGE):$(TAG)

shell:
	docker run --rm -it \
	  -v ~/.photovault:/root/.photovault \
	  -e PHOTOVAULT_B2_KEY_ID \
	  -e PHOTOVAULT_B2_APP_KEY \
	  -e PHOTOVAULT_B2_BUCKET \
	  --entrypoint bash \
	  $(IMAGE):$(TAG)

.PHONY: build run shell
