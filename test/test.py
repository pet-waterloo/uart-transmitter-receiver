# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

# ---------------------------------------------------------------------- #
# utils
# ---------------------------------------------------------------------- #

async def reset_dut(dut):
    """Reset the DUT by asserting the reset signal."""
    dut.rst.value = 1
    yield ClockCycles(dut.clk, 10)  # Wait for 10 clock cycles
    dut.rst.value = 0


async def start_dut(dut):
    """Start the DUT by asserting the start signal."""
    dut.ena = 1


async def uart_send_idle_bits(dut, num_idle_bits: int):
    """Send idle bits for UART transmission."""
    for _ in range(num_idle_bits):
        dut.uart_rx.value = 1  # Idle state is high
        await ClockCycles(dut.clk, 1)  # Wait for the duration of the idle bit


async def uart_send_start_bit(dut, cycles_per_bit: int):
    """Send the start bit for UART transmission."""
    dut.uart_rx.value = 0  # Start bit is low
    await ClockCycles(dut.clk, cycles_per_bit)  # Wait for the duration of the start bit


async def uart_send_data_bit(dut, bit: int, cycles_per_bit: int):
    """Send a data bit for UART transmission."""
    dut.uart_rx.value = bit
    await ClockCycles(dut.clk, cycles_per_bit)  # Wait for the duration of the data bit


async def uart_send_stop_bit(dut, cycles_per_bit: int):
    """Send the stop bit for UART transmission."""
    dut.uart_rx.value = 1  # Stop bit is high
    await ClockCycles(dut.clk, cycles_per_bit)  # Wait for the duration of the stop bit


# ---------------------------------------------------------------------- #
# test functions
# ---------------------------------------------------------------------- #

@cocotb.test()
async def test_uart_rx(dut):
    """Test that the UART valid signal is asserted when data is received."""
    # Start the clock
    cocotb.start_soon(Clock(dut.clk, 20, units="ns").start())
    
    # -------------------------------------------------------- #
    # wait for dut reset
    await reset_dut(dut)
    await start_dut(dut)

    # -------------------------------------------------------- #
    # begin test

    _num_bits = 7
    _num_cpb = 8        # cycles per bit
    
    # calculate total cycles for each state
    _num_start_cycles = _num_cpb
    _num_data_cycles = _num_cpb * _num_bits
    _num_stop_cycles = _num_cpb

    # valid data to send
    _target_data = 0b0001111

    # -------------------------------------------------------- #
    # send data

    data_output = 0
    data_valid = 0

    # send idle bits
    print("Sending idle bits...")
    await uart_send_idle_bits(dut, 10)

    data_valid, data_output = dut.uio_out.value >> 7, dut.uio_out.value & 0x7F
    dut._log.info(f"UART Output: {data_output:<10} | UART Valid: {data_valid:<4}")

    # send start bit
    print("Sending start bit...")
    await uart_send_start_bit(dut, _num_start_cycles)

    data_valid, data_output = dut.uio_out.value >> 7, dut.uio_out.value & 0x7F
    dut._log.info(f"UART Output: {data_output:<10} | UART Valid: {data_valid:<4}")

    # begin sending data bits
    for i in range(_num_bits):

        print(f"Sending data bit {i}...")
        await uart_send_data_bit(dut, (_target_data >> i) & 0x1, _num_cpb)

        data_valid, data_output = dut.uio_out.value >> 7, dut.uio_out.value & 0x7F
        dut._log.info(f"UART Output: {data_output:<10} | UART Valid: {data_valid:<4}")
    
    # send stop bit
    print("Sending stop bit...")
    await uart_send_stop_bit(dut, _num_stop_cycles)

    data_valid, data_output = dut.uio_out.value >> 7, dut.uio_out.value & 0x7F
    dut._log.info(f"UART Output: {data_output:<10} | UART Valid: {data_valid:<4}")

    # -------------------------------------------------------- #
    # check if data is valid

    assert data_valid, "UART valid signal should be asserted (0x01) when data is received"
    assert data_output == _target_data, f"UART output data should be {_target_data:07b}, but got {data_output:07b}"
