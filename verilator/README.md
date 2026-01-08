# Verilator Simulator Docker Image

A minimal Docker image for RTL simulation using Verilator with cocotb, based on the [OpenTitan container setup](https://github.com/lowRISC/opentitan/tree/master/util/container).

## Overview

This setup provides a lightweight Docker container with Verilator and cocotb for simulating Verilog/SystemVerilog designs. Unlike the OpenTitan setup, this configuration excludes Bazel and focuses solely on Verilator simulation capabilities with Python-based testing.

## Features

- **Verilator 5.044**: High-performance Verilog simulator (built from source)
- **Python 3.12**: Modern Python runtime for cocotb
- **cocotb 2.0.0**: Python-based testbench framework
- **Ubuntu 24.04 base**: Latest LTS release
- **zsh**: Default shell for enhanced usability
- **Pacific timezone**: Configured for America/Los_Angeles
- **Sample design**: Basic 8-bit counter with cocotb tests

## Directory Structure

```
verilator/
├── Dockerfile           # Docker image definition
├── Makefile            # Build and test automation
├── README.md           # This file
├── rtl/                # RTL design files
│   └── counter.v       # Example counter module
└── sim/                # Simulation testbenches
    └── counter_tb.py   # Python/cocotb testbench for counter
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

### Local Development (Verilator & cocotb Required)

If you have Verilator and cocotb installed locally:

1. **Run the simulation:**
   ```bash
   make sim
   ```

2. **Clean build artifacts:**
   ```bash
   make clean
   ```

## Example Design

The included counter design (`rtl/counter.v`) is a simple 8-bit counter with:
- Asynchronous active-low reset
- Enable control
- Parameterizable width

The testbench (`sim/counter_tb.py`) demonstrates:
- Reset sequence verification
- Enable control testing
- Counter operation validation
- Multiple test scenarios using cocotb

### Expected Output

```
Starting counter simulation...
Time    Reset   Enable  Count
====    =====   ======  =====
   0    0       0         0
   1    0       0         0
...
  10    1       1         1
  11    1       1         2
  12    1       1         3
...
Simulation completed successfully!
```

## Customization

### Using Your Own Design

1. Place your RTL files in the `rtl/` directory
2. Create a Python testbench in the `sim/` directory using cocotb
3. Update the Makefile variables:
   ```makefile
   RTL_FILES = $(RTL_DIR)/your_design.v
   MODULE = your_module_name
   TOPLEVEL = your_top_level
   ```

### Changing Verilator Version

The Dockerfile builds Verilator 5.044 from source.
To use a different version, modify the `git checkout` line in the Dockerfile to your desired version tag.

## cocotb Testing

cocotb provides a Python-based verification framework. Key features:
- Write testbenches in Python
- Async/await syntax for timing control
- Easy-to-read test code
- Automatic waveform generation with `--trace`

Example test structure:
```python
@cocotb.test()
async def my_test(dut):
    # Create clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Test logic here
    await RisingEdge(dut.clk)
    assert dut.output.value == expected_value
```

## Reference

This setup is inspired by the OpenTitan project's container infrastructure:
- https://github.com/lowRISC/opentitan/tree/master/util/container

## License

See the repository's main LICENSE file.
