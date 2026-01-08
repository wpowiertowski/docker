# Makefile for Verilator simulation

# Verilator configuration
VERILATOR = verilator
VERILATOR_FLAGS = --cc --exe --build -Wall

# Directories
RTL_DIR = rtl
SIM_DIR = sim
OBJ_DIR = obj_dir

# Design files
RTL_FILES = $(RTL_DIR)/counter.v
TB_FILES = $(SIM_DIR)/counter_tb.cpp

# Output executable
EXE = $(OBJ_DIR)/Vcounter

# Docker configuration
DOCKER_IMAGE = verilator-sim
DOCKER_TAG = latest

.PHONY: all build run clean docker-build docker-run docker-test help

# Default target
all: build run

# Build the simulation
build:
	@echo "Building counter simulation with Verilator..."
	$(VERILATOR) $(VERILATOR_FLAGS) $(RTL_FILES) $(TB_FILES)

# Run the simulation
run: build
	@echo "Running counter simulation..."
	@$(EXE)

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf $(OBJ_DIR)

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

# Run simulation in Docker
docker-run: docker-build
	@echo "Running simulation in Docker container..."
	docker run --rm -v $(PWD):/work -w /work $(DOCKER_IMAGE):$(DOCKER_TAG) \
		make build run

# Test Docker image (build and run simulation)
docker-test: docker-run
	@echo "Docker test completed successfully!"

# Show help
help:
	@echo "Verilator Simulation Makefile"
	@echo "=============================="
	@echo ""
	@echo "Targets:"
	@echo "  all          - Build and run simulation (default)"
	@echo "  build        - Build the simulation"
	@echo "  run          - Run the simulation"
	@echo "  clean        - Remove build artifacts"
	@echo "  docker-build - Build the Docker image"
	@echo "  docker-run   - Run simulation in Docker"
	@echo "  docker-test  - Full Docker test (build image and run simulation)"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Usage examples:"
	@echo "  make                # Build and run locally"
	@echo "  make docker-test    # Test in Docker container"
	@echo "  make clean          # Clean build artifacts"
