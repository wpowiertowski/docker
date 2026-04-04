IMAGE      ?= photovault
TAG        ?= latest
CONFIG_DIR ?= $(HOME)/.photovault

build:
	docker build --pull --rm . -t $(IMAGE):$(TAG)

# Ensure the config directory and a starter config exist before running.
$(CONFIG_DIR)/config.toml:
	mkdir -p $(CONFIG_DIR)
	cp config.toml.example $@
	@echo "Created $(CONFIG_DIR)/config.toml — fill in your B2 credentials before running."

run: $(CONFIG_DIR)/config.toml
	docker run --rm \
	  -v $(CONFIG_DIR):/root/.photovault \
	  $(IMAGE):$(TAG)

shell: $(CONFIG_DIR)/config.toml
	docker run --rm -it \
	  -v $(CONFIG_DIR):/root/.photovault \
	  --entrypoint bash \
	  $(IMAGE):$(TAG)

.PHONY: build run shell
