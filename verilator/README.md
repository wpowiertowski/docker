# Verilator Simulator Docker Image

A minimal Docker image for RTL simulation using Verilator, based on the [OpenTitan container setup](https://github.com/lowRISC/opentitan/tree/master/util/container).

## Overview

This setup provides a lightweight Docker container with Verilator for simulating Verilog/SystemVerilog designs. Unlike the OpenTitan setup, this configuration excludes Bazel and focuses solely on Verilator simulation capabilities.

## Features

- **Verilator 5.028**: High-performance Verilog simulator
- **Ubuntu 22.04 base**: Stable and well-supported
- **Minimal dependencies**: Only essential tools included
- **Sample design**: Basic 8-bit counter for testing

## Directory Structure

```
verilator/
├── Dockerfile           # Docker image definition
├── Makefile            # Build and test automation
├── README.md           # This file
├── rtl/                # RTL design files
│   └── counter.v       # Example counter module
└── sim/                # Simulation testbenches
    └── counter_tb.cpp  # C++ testbench for counter
```

## Quick Start

### Using Docker (Recommended)

1. **Build and test the Docker image:**
   ```bash
   cd verilator
   make docker-test
   ```

2. **Build Docker image only:**
   ```bash
   make docker-build
   ```

3. **Run simulation in Docker:**
   ```bash
   make docker-run
   ```

### Local Development (Verilator Required)

If you have Verilator installed locally:

1. **Build the simulation:**
   ```bash
   make build
   ```

2. **Run the simulation:**
   ```bash
   make run
   ```

3. **Build and run:**
   ```bash
   make all
   ```

## Example Design

The included counter design (`rtl/counter.v`) is a simple 8-bit counter with:
- Asynchronous active-low reset
- Enable control
- Parameterizable width

The testbench (`sim/counter_tb.cpp`) demonstrates:
- Reset sequence
- Enable control
- Counter operation verification

### Expected Output

```
Starting counter simulation...
Time    Reset   Enable  Count
====    =====   ======  =====
  5     0       0         0
  6     1       0         0
 10     1       1         0
 11     1       1         1
 12     1       1         2
...
```

## Customization

### Using Your Own Design

1. Place your RTL files in the `rtl/` directory
2. Create a testbench in the `sim/` directory
3. Update the Makefile variables:
   ```makefile
   RTL_FILES = $(RTL_DIR)/your_design.v
   TB_FILES = $(SIM_DIR)/your_testbench.cpp
   ```

### Changing Verilator Version

Edit the `VERILATOR_VERSION` argument in the Dockerfile:
```dockerfile
ARG VERILATOR_VERSION=5.028
```

## Verilator Options

The Makefile uses these Verilator flags:
- `--cc`: Generate C++ output
- `--exe`: Create executable
- `--build`: Compile the generated code
- `-Wall`: Enable all warnings

Add more flags in the Makefile as needed:
```makefile
VERILATOR_FLAGS = --cc --exe --build -Wall --trace
```

## Reference

This setup is inspired by the OpenTitan project's container infrastructure:
- https://github.com/lowRISC/opentitan/tree/master/util/container

## License

See the repository's main LICENSE file.
