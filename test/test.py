# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# ------------------------------------------------------------ #
# utils
# ------------------------------------------------------------ #

async def send_bits(dut, dut_channel, bits: str, cycles_per_bit: int):
    """
    Helper function to send bits to the UART input.
    """
    dut._log.info(f"Sending bits: {bits} (cycles_per_bit={cycles_per_bit})")
    
    for i, bit in enumerate(bits):
        # Set bit on specified channel
        dut._log.info(f"Sending bit #{i} = {bit}")
        dut_channel.value = int(bit)

        await ClockCycles(dut.clk, cycles_per_bit)


async def send_data(dut, dut_channel, _4bits: str, cycles_per_bit: int, callback: None = None):
    """
    Helper function to perform a test on the Hamming decoder.
    """

    for i, bit in enumerate(_4bits):

        # allow for oversampling
        for counter_val in range(cycles_per_bit): 

            # send bit
            dut._log.info(f"Sending bit #{i} = {bit} (cycle={counter_val})")
            dut_channel.value = int(bit)

            # clock system
            await ClockCycles(dut.clk, cycles_per_bit)

            if callback:
                # Call the callback function if provided
                callback(dut, i, bit, counter_val)


# ------------------------------------------------------------ #
# callback functions
# ------------------------------------------------------------ #

UART_STATE_MAP = {
    0: "IDLE",
    1: "START",
    2: "DATA",
    3: "STOP"
}

def idle_callback(dut, i, bit, counter):
    """
    Callback function for idle state.
    """

    _state = dut.uo_out & 0x07
    state_str = UART_STATE_MAP.get(_state, "UNKNOWN")

    dut._log.info(f"UART RX: {state_str} state, bit #{i} = {bit} (cycle={counter})")

def start_bit_callback(dut, i, bit, counter):
    """
    Callback function for start bit.
    """
    _state = dut.uo_out & 0x07
    state_str = UART_STATE_MAP.get(_state, "UNKNOWN")

    dut._log.info(f"UART RX: {state_str} state, bit #{i} = {bit} (cycle={counter})")

def data_bit_callback(dut, i, bit, counter):
    """
    Callback function for data bits.
    """

    # collect dut info
    _data_bits = dut.uio_out & 0x7F
    _state = dut.uo_out & 0x07
    state_str = UART_STATE_MAP.get(_state, "UNKNOWN")

    dut._log.info(f"UART RX: {state_str} state -- bit #{i} = {bit} (cycle={counter}) | rx data = {_data_bits:07b}")

def stop_bit_callback(dut, i, bit, counter):
    """
    Callback function for stop bit.
    """

    # collect dut info
    _data_bits = dut.uio_out & 0x7F
    _valid_bit = (dut.uo_out >> 7) & 0x01
    _state = dut.uo_out & 0x07
    state_str = UART_STATE_MAP.get(_state, "UNKNOWN")

    dut._log.info(f"UART RX: {state_str} state -- bit #{i} = {bit} (cycle={counter}) | rx data = {_data_bits:07b} | valid = {_valid_bit}")

# ------------------------------------------------------------ #
# cocotb tests
# ------------------------------------------------------------ #

@cocotb.test()
async def test_rx_valid_data(dut):
    """Test the UART receiver with valid data."""

    # ------------------------------------------------------------ #
    # setup

    dut._log.info("Starting test_rx_valid_data")

    # reset
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 4)
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 4)

    # ------------------------------------------------------------ #
    # send data

    # Send valid data: 4d, 3p
    _target_data = "0001111"
    _cycles_per_bit = 8

    # idle state
    await send_bits(dut, dut.ui_in, "1111", 1, 
                    callback = idle_callback)

    # start bit
    await send_bits(dut, dut.ui_in, "0", 1, 
                    callback = start_bit_callback)

    # data bits
    await send_bits(dut, dut.ui_in, _target_data, _cycles_per_bit, 
                    callback = data_bit_callback)

    # stop bit
    await send_bits(dut, dut.ui_in, "1", 1, 
                    callback = stop_bit_callback)
    
    # ------------------------------------------------------------ #
    # check results

    # collect dut info
    _data_bits = dut.uio_out & 0x7F
    _valid_bit = (dut.uo_out >> 7) & 0x01
    _state = dut.uo_out & 0x07
    state_str = UART_STATE_MAP.get(_state, "UNKNOWN")

    dut._log.info("Finished test_rx_valid_data")
    dut._log.info(f"UART RX: {state_str} state -- data = {_data_bits:07b} | valid = {_valid_bit}")

    assert _data_bits == 0b0001111, f"Expected data bits 0001111, got {_data_bits:07b}"
    assert _valid_bit == 1, f"Expected valid bit 1, got {_valid_bit}"
    assert _state == 3, f"Expected state 3 (STOP), got {_state} ({state_str})"
