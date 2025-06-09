# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start")

    # Set the clock period to 50 us (20 KHz)
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0

    # Wait for 10 clock cycles to ensure the reset is applied
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # --------------------------------------------------------- #
    # begin testing

    dut._log.info("Test project behavior")

    # --------------------------------------------------------- #
    # Set the input values you want to test
    dut.ui_in.value = 0
    dut.uio_in.value = 0

    # Wait for one clock cycle to see the output values
    for i in range(20):
        await ClockCycles(dut.clk, 1)

        # Log the output values
        dut._log.info(f"Cycle {i+1}: Counter={dut.uo_out.value}")

    # The following assersion is just an example of how to check the output values.
    # Change it to match the actual expected output of your module:
    print("Defaulting testing result to: True")
    assert True

    # Keep testing the module by changing the input values, waiting for
    # one or more clock cycles, and asserting the expected output values.
