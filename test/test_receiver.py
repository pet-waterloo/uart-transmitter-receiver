# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# ---------------------------------------------------------------------------- #
# utils
# ---------------------------------------------------------------------------- #

async def send_idle_bits(dut, dut_channel, cycles_per_bit: int = 8, callback=None):
    """Send idle bits to ensure the UART receiver is in a known state"""
    
    # Idle state (HIGH)
    dut_channel.value = 1
    for j in range(cycles_per_bit):
        await ClockCycles(dut.clk, 1)
        
        if callback:
            callback(dut, 0, 1, j, cycles_per_bit)


async def send_start_bit(dut, dut_channel, cycles_per_bit: int = 8, callback=None):
    """Send the start bit to the UART receiver"""

    # Start bit (LOW)
    dut_channel.value = 0
    for j in range(cycles_per_bit):
        await ClockCycles(dut.clk, 1)
        
        if callback:
            callback(dut, 0, 0, j, cycles_per_bit)


async def send_data_bits(dut, dut_channel, data_bits: str, cycles_per_bit: int = 8, callback=None):
    """Send data bits to the UART receiver"""
    
    for i, bit in enumerate(map(int, data_bits)):
        dut_channel.value = bit

        for j in range(cycles_per_bit):
            await ClockCycles(dut.clk, 1)
        
            if callback:
                callback(dut, i, bit, j, cycles_per_bit)


async def send_stop_bit(dut, dut_channel, cycles_per_bit: int = 8, callback=None):
    """Send the stop bit to the UART receiver"""
    
    # Stop bit (HIGH)
    dut_channel.value = 1
    for j in range(cycles_per_bit):
        await ClockCycles(dut.clk, 1)
        
        if callback:
            callback(dut, 0, 1, j, cycles_per_bit)

    

async def reset_dut(dut):
    """Reset the DUT to a known state"""
    dut._log.info("Resetting DUT")

    # reset io ports
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0

    # wait for reset to propagate
    await ClockCycles(dut.clk, 10)
    
    # release reset
    dut.rst_n.value = 1

    dut._log.info("Reset complete - all registers should be cleared")


# ---------------------------------------------------------------------------- #
# callback functions
# ---------------------------------------------------------------------------- #

UART_STATE_MAP = {
    0: "IDLE",
    1: "START",
    2: "DATA",
    3: "STOP"}

def callback_idle(dut, bit_index, bit_value, cycle_index, total_cycles):
    """Callback for idle bits"""
    _uart_data = dut.uio_out.value & 0x7F  # Mask to get only the relevant bits
    _uart_valid = (dut.uio_out.value >> 7) & 0x1
    _state = dut.uo_out.value & 0x3  # Extract UART state (2 bits)

    if cycle_index != total_cycles - 1:
        return

    dut._log.info(
        f"IDLE CB: STATE={UART_STATE_MAP.get(_state, 'UNKNOWN')}, bit_index={bit_index}, bit_value={bit_value}, uart_data={_uart_data:07b}, uart_valid={_uart_valid}"
    )

def callback_start(dut, bit_index, bit_value, cycle_index, total_cycles):
    """Callback for start bit"""
    _uart_data = dut.uio_out.value & 0x7F  # Mask to get only the relevant bits
    _uart_valid = (dut.uio_out.value >> 7) & 0x1
    _state = dut.uo_out.value & 0x3  # Extract UART state (2 bits)

    if cycle_index != total_cycles - 1:
        return

    dut._log.info(
        f"START CB: STATE={UART_STATE_MAP.get(_state, 'UNKNOWN')}, bit_index={bit_index}, bit_value={bit_value}, uart_data={_uart_data:07b}, uart_valid={_uart_valid}"
    )

def callback_data(dut, bit_index, bit_value, cycle_index, total_cycles):
    """Callback for data bits"""
    _uart_data = dut.uio_out.value & 0x7F  # Mask to get only the relevant bits
    _uart_valid = (dut.uio_out.value >> 7) & 0x1
    _state = dut.uo_out.value & 0x3  # Extract UART state (2 bits)

    dut._log.info(
        f"DATA CB: STATE={UART_STATE_MAP.get(_state, 'UNKNOWN')}, CYCLE [{cycle_index+1}/{total_cycles}] | Bit: [{bit_index+1}/7]={bit_value}, uart_data={_uart_data:07b}, uart_valid={_uart_valid}"
    )

    # border off new cycle
    if cycle_index == total_cycles - 1:
        dut._log.info("="*30)

def callback_stop(dut, bit_index, bit_value, cycle_index, total_cycles):
    """Callback for stop bit"""
    _uart_data = dut.uio_out.value & 0x7F  # Mask to get only the relevant bits
    _uart_valid = (dut.uio_out.value >> 7) & 0x1
    _state = dut.uo_out.value & 0x3  # Extract UART state (2 bits)

    if cycle_index != total_cycles - 1:
        return

    dut._log.info(
        f"STOP CB: STATE={UART_STATE_MAP.get(_state, 'UNKNOWN')}, bit_index={bit_index}, bit_value={bit_value}, uart_data={_uart_data:07b}, uart_valid={_uart_valid}"
    )

# ---------------------------------------------------------------------------- #
# cocotb tests
# ---------------------------------------------------------------------------- #


@cocotb.test()
async def test_error_free_data(dut):
    """Test the decoder with error-free Hamming code"""
    dut._log.info("Starting error-free data test")

    # Set the clock period to 50 us (20 MHz)
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())
    
    # --------------------------------------------------------- #
    # Reset DUT
    await reset_dut(dut)

    # --------------------------------------------------------- #
    # Variables
    valid_hamming = 0b1111111  # 7-bit codeword
    expected_data = 0b1111     # Expected decoded value
    cycles_per_bit = 8         # UART baud timing

    dut._log.info(f"Sending valid codeword: {valid_hamming:07b}")

    # --------------------------------------------------------- #
    # UART transmission
    await send_idle_bits(dut, dut.ui_in, cycles_per_bit, callback=callback_idle)
    await send_start_bit(dut, dut.ui_in, cycles_per_bit, callback=callback_start)
    await send_data_bits(dut, dut.ui_in, f"{valid_hamming:07b}"[::-1], cycles_per_bit, callback=callback_data)
    await send_stop_bit(dut, dut.ui_in, cycles_per_bit, callback=callback_stop)
    await send_idle_bits(dut, dut.ui_in, cycles_per_bit, callback=callback_idle)

    # --------------------------------------------------------- #
    # Wait for decoder to process
    for _ in range(cycles_per_bit):
        await ClockCycles(dut.clk, 1)

    # --------------------------------------------------------- #
    # Extract signals
    d0 = (dut.uo_out.value >> 2) & 0x1  # uo_out[2]
    d1 = (dut.uo_out.value >> 3) & 0x1  # uo_out[3]
    d2 = (dut.uo_out.value >> 5) & 0x1  # uo_out[5]
    d3 = (dut.uo_out.value >> 6) & 0x1  # uo_out[6]
    decode_out = (d3 << 3) | (d2 << 2) | (d1 << 1) | d0

    syndrome_out = dut.uio_out.value & 0x7      # uio_out[2:0]
    valid_out = (dut.uo_out.value >> 7) & 0x1    # uo_out[7]

    dut._log.info(
        f"Decoder Output -> Data: {decode_out:04b}, Syndrome: {syndrome_out:03b}, Valid: {valid_out}"
    )

    # --------------------------------------------------------- #
    # Assertions
    assert syndrome_out == 0, f"Expected syndrome 000, got {syndrome_out:03b}"
    assert decode_out == expected_data, f"Expected data {expected_data:04b}, got {decode_out:04b}"
    assert valid_out == 1, f"Expected valid bit 1, got {valid_out}"

    dut._log.info("Error-free data test PASSED")


@cocotb.test()
async def test_single_bit_error(dut):
    """Test the decoder with a single bit error in the Hamming code"""
    dut._log.info("Starting single bit error test")

    # Set the clock period to 50 us (20 MHz)
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())
    
    # --------------------------------------------------------- #
    # reset

    await reset_dut(dut)

    # --------------------------------------------------------- #
    # variables -- https://i-naeem.github.io/heyming/#/heyming
    invalid_hamming = 0b1111110  # Binary format
    expected_data = 0b1111     # Expected decoded data bits
    cycles_per_bit = 8  # Number of clock cycles per bit

    # --------------------------------------------------------- #
    # perform uart operation

    dut._log.info(f"Sending invalid codeword: {invalid_hamming:07b}")

    # perform UART cycle
    await send_idle_bits(dut, dut.ui_in, cycles_per_bit, callback=callback_idle)
    await send_start_bit(dut, dut.ui_in, cycles_per_bit, callback=callback_start)
    await send_data_bits(dut, dut.ui_in, f"{invalid_hamming:07b}"[::-1], cycles_per_bit, callback=callback_data)
    await send_stop_bit(dut, dut.ui_in, cycles_per_bit, callback=callback_stop)

    # reset to idle
    await send_idle_bits(dut, dut.ui_in, cycles_per_bit, callback=callback_idle)

    dut._log.info("UART frame sent, waiting for processing...")

    # --------------------------------------------------------- #
    # output uart results

    _uart_data = dut.uio_out.value & 0x7F  # Mask to get only the relevant bits
    _uart_valid = (dut.uio_out.value >> 7) & 0x1

    dut._log.info(f"UART OUTPUT: uart_data={_uart_data:07b}, uart_valid={_uart_valid}")

    # --------------------------------------------------------- #
    # wait for Hamming Decoder to process the input

    for i in range(cycles_per_bit):
        await ClockCycles(dut.clk, 1)
        if (i+1) % 4 == 0:  # Print every few cycles to reduce log volume
            decode_out = dut.uo_out.value & 0xF
            syndrome_out = dut.uio_out.value & 0x7
            valid_out = (dut.uo_out.value >> 7) & 0x1

            dut._log.info(
                f"Cycle {i+1}: decode_out={decode_out:04b}, syndrome_out={syndrome_out:03b}, "
                f"valid_out={valid_out}"
            )

    # --------------------------------------------------------- #
    # Extract final results

    decode_out = dut.uo_out.value & 0xF
    syndrome_out = dut.uio_out.value & 0x7
    valid_out = (dut.uo_out.value >> 7) & 0x1

    dut._log.info(
        f"Hamming Decoder output: decode_out={decode_out:04b}, syndrome_out={syndrome_out:03b}, valid_out={valid_out}"
    )
    
    # --------------------------------------------------------- #
    # Verify results

    dut._log.info("Verifying results...")
    dut._log.info(
        f"Final result: Valid={int(valid_out)}, Syndrome={int(syndrome_out):03b}, "
        f"Data={int(decode_out):04b}"
    )

    # More detailed assertions
    if syndrome_out == 0:
        dut._log.error(f"SYNDROME ERROR: Expected non-zero (error detected), got {syndrome_out:03b}")
    if decode_out != expected_data:
        dut._log.error(f"DATA ERROR: Expected {expected_data:04b}, got {decode_out:04b}")
    if valid_out != 1:
        dut._log.error(f"VALID ERROR: Expected 1, got {valid_out}")

    # Continue with assertions
    # Syndrome should be non-zero (error detected)
    assert syndrome_out != 0, f"Expected non-zero syndrome (error detected), got {syndrome_out:03b}"

    # Data should match expected
    assert (
        decode_out == expected_data
    ), f"Expected data {expected_data:04b}, got {decode_out:04b}"

    # Valid should be 1
    assert valid_out == 1, f"Expected valid bit 1, got {valid_out}"

    dut._log.info("Single bit error test PASSED")

