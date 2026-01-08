"""
Cocotb testbench for counter module
Tests reset, enable, and counting functionality
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer


@cocotb.test()
async def counter_test(dut):
    """Test counter module with reset and enable"""
    
    # Create a 10ns period clock (100 MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Print header
    dut._log.info("Starting counter simulation...")
    dut._log.info("Time\tReset\tEnable\tCount")
    dut._log.info("====\t=====\t======\t=====")
    
    # Initialize signals
    dut.rst_n.value = 0
    dut.enable.value = 0
    
    # Wait a few clock cycles with reset asserted
    for i in range(5):
        await RisingEdge(dut.clk)
        dut._log.info(f"{i:4d}\t{int(dut.rst_n.value)}\t{int(dut.enable.value)}\t{int(dut.count.value):3d}")
    
    # Release reset
    dut.rst_n.value = 1
    
    # Wait a few more cycles with enable low
    for i in range(5, 10):
        await RisingEdge(dut.clk)
        dut._log.info(f"{i:4d}\t{int(dut.rst_n.value)}\t{int(dut.enable.value)}\t{int(dut.count.value):3d}")
    
    # Assert enable and watch counter increment
    dut.enable.value = 1
    
    for i in range(10, 50):
        await RisingEdge(dut.clk)
        dut._log.info(f"{i:4d}\t{int(dut.rst_n.value)}\t{int(dut.enable.value)}\t{int(dut.count.value):3d}")
    
    # Verify counter is incrementing
    count_value = int(dut.count.value)
    assert count_value > 30, f"Counter should be > 30, got {count_value}"
    
    dut._log.info("\nSimulation completed successfully!")


@cocotb.test()
async def counter_reset_test(dut):
    """Test that reset properly clears the counter"""
    
    # Create a clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize
    dut.rst_n.value = 1
    dut.enable.value = 1
    
    # Wait for counter to increment
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # Verify counter is not zero
    assert int(dut.count.value) > 0, "Counter should have incremented"
    
    # Apply reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    
    # Verify counter is reset to zero
    assert int(dut.count.value) == 0, f"Counter should be 0 after reset, got {dut.count.value}"
    
    dut._log.info("Reset test passed!")


@cocotb.test()
async def counter_enable_test(dut):
    """Test that counter only increments when enabled"""
    
    # Create a clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize - reset and disable
    dut.rst_n.value = 0
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    
    # Release reset but keep enable low
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # Counter should still be zero
    assert int(dut.count.value) == 0, f"Counter should be 0 when disabled, got {dut.count.value}"
    
    # Enable counter
    dut.enable.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # Counter should now be 1 after enable
    count_val = int(dut.count.value)
    assert count_val >= 1, f"Counter should be >= 1 after enable, got {count_val}"
    
    dut._log.info("Enable test passed!")
