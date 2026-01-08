# Makefile for Verilator simulation with cocotb

# Directories
RTL_DIR = rtl
SIM_DIR = sim

# Design files
RTL_FILES = $(RTL_DIR)/counter.v
MODULE = counter
TOPLEVEL = counter
TOPLEVEL_LANG = verilog

# Cocotb configuration
export COCOTB_REDUCED_LOG_FMT = 1
export TOPLEVEL_LANG
export MODULE
export TOPLEVEL

# Simulator
SIM = verilator
export SIM

# Verilator flags
EXTRA_ARGS = --trace --trace-structs
COMPILE_ARGS = -Wall

# Docker configuration
DOCKER_IMAGE = verilator-sim
DOCKER_TAG = latest

.PHONY: all sim clean docker-build docker-run docker-test help

# Default target
all: sim

# Run the simulation using cocotb
sim:
	@echo "Running counter simulation with cocotb..."
	VERILOG_SOURCES=$(RTL_FILES) MODULE=$(SIM_DIR).counter_tb $(MAKE) -f $(shell cocotb-config --makefiles)/Makefile.sim

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf sim_build __pycache__ $(SIM_DIR)/__pycache__ results.xml *.vcd

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Run simulation in Docker
docker-run: docker-build
	@echo "Running simulation in Docker container..."
	docker run --rm -v $(PWD):/work -w /work $(DOCKER_IMAGE):$(DOCKER_TAG) \
		make sim

# Test Docker image (build and run simulation)
docker-test: docker-run
	@echo "Docker test completed successfully!"

# Show help
help:
	@echo "Verilator Simulation Makefile (with cocotb)"
	@echo "============================================"
	@echo ""
	@echo "Targets:"
	@echo "  all          - Run simulation (default)"
	@echo "  sim          - Run the cocotb simulation"
	@echo "  clean        - Remove build artifacts"
	@echo "  docker-build - Build the Docker image"
	@echo "  docker-run   - Run simulation in Docker"
	@echo "  docker-test  - Full Docker test (build image and run simulation)"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Usage examples:"
	@echo "  make                # Run simulation locally"
	@echo "  make docker-test    # Test in Docker container"
	@echo "  make clean          # Clean build artifacts"
