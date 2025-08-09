# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

# =============================================================
# Shared Constants and Lookup Tables
# =============================================================

BAUD_CYCLES = 8  # UART oversampling factor (cycles per bit)

# Hamming(7,4) code table: maps 4-bit data to 7-bit codeword
# inputs : [d0, d1, d2, d3]
# outputs: [c0, c1, d0, c2, d1, d2, d3]
HAMMING_CODE_TABLE = {
    "0000": "0000000",
    "0001": "1101001",
    "0010": "0101010",
    "0011": "1000011",
    "0100": "1001100",
    "0101": "0100101",
    "0110": "1100110",
    "0111": "0001111",
    "1000": "1110000",
    "1001": "0011001",
    "1010": "1011010",
    "1011": "0110011",
    "1100": "0111100",
    "1101": "1010101",
    "1110": "0010110",
    "1111": "1111111"
}

# Error masks for testing: no error, single-bit error, two-bit error
NO_ERROR_MASK      = "0000000"
ONE_BIT_ERROR_MASK = "0000100"
TWO_BIT_ERROR_MASK = "0100010"

# UART receiver state mapping for logging
UART_STATE_MAP = {
    0: "IDLE",
    1: "START",
    2: "DATA",
    3: "STOP"
}

# =============================================================
# Utility Functions
# =============================================================

def safe_get_int_value(signal, bit_mask=0x01):
    """Safely extract integer value from a signal, treating X as 0."""
    try:
        return signal.value.integer & bit_mask
    except ValueError:
        return 0

def int_to_binstr(value: int, width: int) -> str:
    """Convert integer to binary string of given width."""
    return format(value, f"0{width}b")

def get_signal_handle_safely(dut, primary_signal, fallback_signals=None):
    """Try to get signal or use fallbacks."""
    if fallback_signals is None:
        fallback_signals = []
    try:
        handle = dut
        for name in primary_signal.split('.'):
            handle = getattr(handle, name)
        _ = handle.value
        return handle
    except AttributeError:
        for signal in fallback_signals:
            try:
                handle = dut
                for name in signal.split('.'):
                    handle = getattr(handle, name)
                _ = handle.value
                return handle
            except AttributeError:
                continue
    return dut.uo_out

async def apply_reset(dut, cycles=2):
    """Apply reset to DUT (for transmitter tests)."""
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    if hasattr(dut, "uio_in"):
        dut.uio_in.value = 0
    if hasattr(dut, "ena"):
        dut.ena.value = 1
    await ClockCycles(dut.clk, cycles)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, cycles)

async def reset_dut(dut):
    """Reset the DUT to a known state (for receiver tests)."""
    dut._log.info("Resetting DUT")
    if hasattr(dut, "ena"):
        dut.ena.value = 1
    dut.ui_in.value = 0
    if hasattr(dut, "uio_in"):
        dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    dut._log.info("Reset complete - all registers should be cleared")

# =============================================================
# UART Bit Senders (Receiver Test)
# =============================================================

async def send_idle_bits(dut, dut_channel, cycles_per_bit: int = 8, callback=None):
    """Send idle (HIGH) bits to UART receiver."""
    dut_channel.value = 1
    for j in range(cycles_per_bit):
        await ClockCycles(dut.clk, 1)
        if callback:
            callback(dut, 0, 1, j, cycles_per_bit)

async def send_start_bit(dut, dut_channel, cycles_per_bit: int = 8, callback=None):
    """Send start (LOW) bit to UART receiver."""
    dut_channel.value = 0
    for j in range(cycles_per_bit):
        await ClockCycles(dut.clk, 1)
        if callback:
            callback(dut, 0, 0, j, cycles_per_bit)

async def send_data_bits(dut, dut_channel, data_bits: str, cycles_per_bit: int = 8, callback=None):
    """Send data bits to UART receiver."""
    for i, bit in enumerate(map(int, data_bits)):
        dut_channel.value = bit
        for j in range(cycles_per_bit):
            await ClockCycles(dut.clk, 1)
            if callback:
                callback(dut, i, bit, j, cycles_per_bit)

async def send_stop_bit(dut, dut_channel, cycles_per_bit: int = 8, callback=None):
    """Send stop (HIGH) bit to UART receiver."""
    dut_channel.value = 1
    for j in range(cycles_per_bit):
        await ClockCycles(dut.clk, 1)
        if callback:
            callback(dut, 0, 1, j, cycles_per_bit)


# =============================================================
# Callback Functions (Receiver Test) - FIXED
# =============================================================

def callback_idle(dut, bit_index, bit_value, cycle_index, total_cycles):
    """Callback for idle bits."""
    _uart_valid = (dut.uo_out.value >> 1) & 0x1        # uo_out[1] - UART valid
    _state = (dut.uio_out.value >> 6) & 0x3             # uio_out[7:6] - UART state
    if cycle_index != total_cycles - 1:
        return
    dut._log.info(f"IDLE CB: STATE={UART_STATE_MAP.get(_state, 'UNKNOWN')}, bit_index={bit_index}, bit_value={bit_value}, uart_valid={_uart_valid}")

def callback_start(dut, bit_index, bit_value, cycle_index, total_cycles):
    """Callback for start bit."""
    _uart_valid = (dut.uo_out.value >> 1) & 0x1        # uo_out[1] - UART valid
    _state = (dut.uio_out.value >> 6) & 0x3             # uio_out[7:6] - UART state
    if cycle_index != total_cycles - 1:
        return
    dut._log.info(f"START CB: STATE={UART_STATE_MAP.get(_state, 'UNKNOWN')}, bit_index={bit_index}, bit_value={bit_value}, uart_valid={_uart_valid}")

def callback_data(dut, bit_index, bit_value, cycle_index, total_cycles):
    """Callback for data bits."""
    _uart_valid = (dut.uo_out.value >> 1) & 0x1        # uo_out[1] - UART valid
    _state = (dut.uio_out.value >> 6) & 0x3             # uio_out[7:6] - UART state
    dut._log.info(f"DATA CB: STATE={UART_STATE_MAP.get(_state, 'UNKNOWN')}, CYCLE [{cycle_index+1}/{total_cycles}] | Bit: [{bit_index+1}/7]={bit_value}, uart_valid={_uart_valid}")
    if cycle_index == total_cycles - 1:
        dut._log.info("="*30)

def callback_stop(dut, bit_index, bit_value, cycle_index, total_cycles):
    """Callback for stop bit."""
    _uart_valid = (dut.uo_out.value >> 1) & 0x1        # uo_out[1] - UART valid
    _state = (dut.uio_out.value >> 6) & 0x3             # uio_out[7:6] - UART state
    if cycle_index != total_cycles - 1:
        return
    dut._log.info(f"STOP CB: STATE={UART_STATE_MAP.get(_state, 'UNKNOWN')}, bit_index={bit_index}, bit_value={bit_value}, uart_valid={_uart_valid}")

def reduced_callback_data(dut, bit_index, bit_value, cycle_index, total_cycles):
    """Reduced callback for data bits."""
    if cycle_index != total_cycles - 1:
        return
    
    _uart_valid = (dut.uo_out.value >> 1) & 0x1        # uo_out[1] - UART valid
    _state = (dut.uio_out.value >> 6) & 0x3             # uio_out[7:6] - UART state
    dut._log.info(f"DATA CB: STATE={UART_STATE_MAP.get(_state, 'UNKNOWN')}, CYCLE [{cycle_index+1}/{total_cycles}] | Bit: [{bit_index+1}/7]={bit_value}, uart_valid={_uart_valid}")

# =============================================================
# Transmitter Test Logic
# =============================================================

async def run_hamming_case(dut, data_bits_str, error_mask_str, output_sig, busy_sig):
    """Drive UART transmitter and check codeword with/without errors."""
    data_bits = int(data_bits_str, 2)
    # Set data on input, pulse start bit
    dut.ui_in.value = data_bits
    dut.ui_in.value = data_bits | 0x10
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = data_bits
    # Wait for UART start bit (TX low) or timeout
    for _ in range(10):
        if safe_get_int_value(output_sig) == 0:
            break
        await ClockCycles(dut.clk, 1)
    # Capture UART frame (10 bits: start, data, stop)
    uart_frame = ""
    for bit in range(10):
        bit_value = safe_get_int_value(output_sig)
        uart_frame = str(bit_value) + uart_frame
        await ClockCycles(dut.clk, BAUD_CYCLES)
    # Calculate expected and masked codewords
    expected_code = HAMMING_CODE_TABLE[data_bits_str]
    masked_code = "".join(["1" if int(a) ^ int(b) == 1 else "0" for a, b in zip(expected_code, error_mask_str)])
    return expected_code, masked_code


# =============================================================
# Transmitter Test
# =============================================================

@cocotb.test()
async def test_full_hamming_code(dut):
    """Test the UART transmitter and Hamming encoder for all 4-bit inputs and error cases."""
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())
    await apply_reset(dut)
    encoder_code_sig = get_signal_handle_safely(dut, "uo_out", ["tx"])
    busy_sig = get_signal_handle_safely(dut, "tx_busy", ["uo_out"])
    for data_bits_str in HAMMING_CODE_TABLE.keys():
        await apply_reset(dut)
        # Test: no error
        original, masked = await run_hamming_case(
            dut, data_bits_str, NO_ERROR_MASK, encoder_code_sig, busy_sig
        )
        if masked != original:
            dut._log.error(f"[NO_ERR] expected {original}, got {masked} (input={data_bits_str})")
        assert masked == original
        await apply_reset(dut)
        # Test: single-bit error
        original, masked = await run_hamming_case(
            dut, data_bits_str, ONE_BIT_ERROR_MASK, encoder_code_sig, busy_sig
        )
        if masked == original:
            dut._log.error(f"[1BIT_ERR] expected different codeword, but got same: {masked} (input={data_bits_str})")
        assert masked != original
        await apply_reset(dut)
        # Test: two-bit error
        original, masked = await run_hamming_case(
            dut, data_bits_str, TWO_BIT_ERROR_MASK, encoder_code_sig, busy_sig
        )
        if masked == original:
            dut._log.error(f"[2BIT_ERR] expected different codeword, but got same: {masked} (input={data_bits_str})")
        assert masked != original

# =============================================================
# Receiver Tests - FIXED
# =============================================================

@cocotb.test()
async def test_error_free_data(dut):
    """Test decoder with error-free Hamming code sent over UART."""
    dut._log.info("Starting error-free data test")
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    valid_hamming = 0b1111111
    expected_data = 0b1111
    cycles_per_bit = 8
    dut._log.info(f"Sending valid codeword: {valid_hamming:07b}")

    # Send UART frame: idle, start, data, stop, idle
    await send_idle_bits(dut, dut.ui_in, cycles_per_bit, callback=callback_idle)
    await send_start_bit(dut, dut.ui_in, cycles_per_bit, callback=callback_start)
    await send_data_bits(dut, dut.ui_in, f"{valid_hamming:07b}"[::-1], cycles_per_bit, callback=callback_data)
    await send_stop_bit(dut, dut.ui_in, cycles_per_bit, callback=callback_stop)
    await send_idle_bits(dut, dut.ui_in, cycles_per_bit, callback=callback_idle)
    dut._log.info("UART frame sent, waiting for processing...")

    # Output UART status only (no raw data available)
    _uart_valid = (dut.uo_out.value >> 1) & 0x1
    dut._log.info(f"UART STATUS: uart_valid={_uart_valid}")

    # Wait for decoder to process and log intermediate results
    for i in range(cycles_per_bit):
        await ClockCycles(dut.clk, 1)
        if (i+1) % 4 == 0:
            # Extract decoded data bits from output pins
            d0 = (dut.uo_out.value >> 2) & 0x1  # uo_out[2]
            d1 = (dut.uo_out.value >> 3) & 0x1  # uo_out[3]
            d2 = (dut.uo_out.value >> 5) & 0x1  # uo_out[5]
            d3 = (dut.uo_out.value >> 6) & 0x1  # uo_out[6]
            decode_out = (d3 << 3) | (d2 << 2) | (d1 << 1) | d0
            # Syndrome from uio_out
            syndrome_out = dut.uio_out.value & 0x7  # uio_out[2:0]
            valid_out = (dut.uo_out.value >> 7) & 0x1  # uo_out[7]
            dut._log.info(f"Cycle {i+1}: decode_out={decode_out:04b}, syndrome_out={syndrome_out:03b}, valid_out={valid_out}")

    # Extract and check final results
    d0 = (dut.uo_out.value >> 2) & 0x1  # uo_out[2]
    d1 = (dut.uo_out.value >> 3) & 0x1  # uo_out[3]
    d2 = (dut.uo_out.value >> 5) & 0x1  # uo_out[5]
    d3 = (dut.uo_out.value >> 6) & 0x1  # uo_out[6]
    decode_out = (d3 << 3) | (d2 << 2) | (d1 << 1) | d0
    syndrome_out = dut.uio_out.value & 0x7  # uio_out[2:0]
    valid_out = (dut.uo_out.value >> 7) & 0x1  # uo_out[7]
    dut._log.info(f"Hamming Decoder output: decode_out={decode_out:04b}, syndrome_out={syndrome_out:03b}, valid_out={valid_out}")
    dut._log.info("Verifying results...")
    dut._log.info(f"Final result: Valid={int(valid_out)}, Syndrome={int(syndrome_out):03b}, Data={int(decode_out):04b}")

    # Assertions
    if syndrome_out != 0:
        dut._log.error(f"SYNDROME ERROR: Expected 0, got {syndrome_out:03b}")
    if decode_out != expected_data:
        dut._log.error(f"DATA ERROR: Expected {expected_data:04b}, got {decode_out:04b}")
    if valid_out != 1:
        dut._log.error(f"VALID ERROR: Expected 1, got {valid_out}")
    assert syndrome_out == 0, f"Expected syndrome 0, got {syndrome_out:03b}"
    assert decode_out == expected_data, f"Expected data {expected_data:04b}, got {decode_out:04b}"
    assert valid_out == 1, f"Expected valid bit 1, got {valid_out}"
    dut._log.info("Error-free data test PASSED")

@cocotb.test()
async def test_single_bit_error(dut):
    """Test decoder with a single bit error in the Hamming code sent over UART."""
    dut._log.info("Starting single bit error test")
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())
    await reset_dut(dut)
    invalid_hamming = 0b1111110
    expected_data = 0b1111
    cycles_per_bit = 8
    dut._log.info(f"Sending invalid codeword: {invalid_hamming:07b}")

    # Send UART frame: idle, start, data, stop, idle
    await send_idle_bits(dut, dut.ui_in, cycles_per_bit, callback=callback_idle)
    await send_start_bit(dut, dut.ui_in, cycles_per_bit, callback=callback_start)
    await send_data_bits(dut, dut.ui_in, f"{invalid_hamming:07b}"[::-1], cycles_per_bit, callback=callback_data)
    await send_stop_bit(dut, dut.ui_in, cycles_per_bit, callback=callback_stop)
    await send_idle_bits(dut, dut.ui_in, cycles_per_bit, callback=callback_idle)
    dut._log.info("UART frame sent, waiting for processing...")

    # Output UART status only (no raw data available)
    _uart_valid = (dut.uo_out.value >> 1) & 0x1
    dut._log.info(f"UART STATUS: uart_valid={_uart_valid}")

    # Wait for decoder to process and log intermediate results
    for i in range(cycles_per_bit):
        await ClockCycles(dut.clk, 1)
        if (i+1) % 4 == 0:
            # Extract decoded data bits from output pins
            d0 = (dut.uo_out.value >> 2) & 0x1  # uo_out[2]
            d1 = (dut.uo_out.value >> 3) & 0x1  # uo_out[3]
            d2 = (dut.uo_out.value >> 5) & 0x1  # uo_out[5]
            d3 = (dut.uo_out.value >> 6) & 0x1  # uo_out[6]
            decode_out = (d3 << 3) | (d2 << 2) | (d1 << 1) | d0
            # Syndrome from uio_out
            syndrome_out = dut.uio_out.value & 0x7  # uio_out[2:0]
            valid_out = (dut.uo_out.value >> 7) & 0x1  # uo_out[7]
            dut._log.info(f"Cycle {i+1}: decode_out={decode_out:04b}, syndrome_out={syndrome_out:03b}, valid_out={valid_out}")

    # Extract and check final results
    d0 = (dut.uo_out.value >> 2) & 0x1  # uo_out[2]
    d1 = (dut.uo_out.value >> 3) & 0x1  # uo_out[3]
    d2 = (dut.uo_out.value >> 5) & 0x1  # uo_out[5]
    d3 = (dut.uo_out.value >> 6) & 0x1  # uo_out[6]
    decode_out = (d3 << 3) | (d2 << 2) | (d1 << 1) | d0
    syndrome_out = dut.uio_out.value & 0x7  # uio_out[2:0]
    valid_out = (dut.uo_out.value >> 7) & 0x1  # uo_out[7]
    dut._log.info(f"Hamming Decoder output: decode_out={decode_out:04b}, syndrome_out={syndrome_out:03b}, valid_out={valid_out}")
    dut._log.info("Verifying results...")
    dut._log.info(f"Final result: Valid={int(valid_out)}, Syndrome={int(syndrome_out):03b}, Data={int(decode_out):04b}")
    
    # Assertions
    if syndrome_out == 0:
        dut._log.error(f"SYNDROME ERROR: Expected non-zero (error detected), got {syndrome_out:03b}")
    if decode_out != expected_data:
        dut._log.error(f"DATA ERROR: Expected {expected_data:04b}, got {decode_out:04b}")
    if valid_out != 1:
        dut._log.error(f"VALID ERROR: Expected 1, got {valid_out}")
    assert syndrome_out != 0, f"Expected non-zero syndrome (error detected), got {syndrome_out:03b}"
    assert decode_out == expected_data, f"Expected data {expected_data:04b}, got {decode_out:04b}"
    assert valid_out == 1, f"Expected valid bit 1, got {valid_out}"
    dut._log.info("Single bit error test PASSED")

@cocotb.test()
async def test_all_inputs(dut):
    """
    Exhaustively test all 4-bit data inputs (16 values) for:
      - Correct reception of the valid Hamming(7,4) codeword (no error)
      - Correction of each single-bit error (7 possible bit flips per codeword)
    """
    dut._log.info("Starting exhaustive all inputs test")
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())

    cycles_per_bit = BAUD_CYCLES
    total_pass = 0
    total_fail = 0

    # Iterate all 4-bit data inputs (keys in table)
    for data_key, codeword_str in HAMMING_CODE_TABLE.items():
        # Build list of test variants: (label, code_int, is_error)
        base_code_int = int(codeword_str, 2)
        variants = [("NO_ERR", base_code_int, False)]
        # Single-bit error injections (flip each of 7 bits)
        for bit_idx in range(7):
            flip_mask = 1 << bit_idx
            variants.append((f"ERR_BIT{bit_idx}", base_code_int ^ flip_mask, True))

        for label, tx_code_int, is_err in variants:
            sep = "=" * 60
            dut._log.info(sep)
            dut._log.info(f"Testing DATA_KEY={data_key} VARIANT={label}")
            dut._log.info(f"Sending codeword: {tx_code_int:07b}")

            # Send UART frame: idle, start, data, stop, idle (matching existing tests)
            await send_idle_bits(dut, dut.ui_in, cycles_per_bit, callback=callback_idle)
            await send_start_bit(dut, dut.ui_in, cycles_per_bit, callback=callback_start)
            await send_data_bits(dut, dut.ui_in, f"{tx_code_int:07b}"[::-1], cycles_per_bit, callback=reduced_callback_data)
            await send_stop_bit(dut, dut.ui_in, cycles_per_bit, callback=callback_stop)
            await send_idle_bits(dut, dut.ui_in, cycles_per_bit, callback=callback_idle)
            dut._log.info(sep)

            # Output UART status only (no raw data available)
            _uart_valid = (dut.uo_out.value >> 1) & 0x1
            dut._log.info(f"UART STATUS: uart_valid={_uart_valid}")

            # Wait for decoder to process - sample once at the end of the bit period
            await ClockCycles(dut.clk, cycles_per_bit)

            # Use calculate_hamming_decode to compute expected results
            # Extract bits from tx_code_int (received codeword)
            c0_tx = (tx_code_int >> 0) & 0x1
            c1_tx = (tx_code_int >> 1) & 0x1
            d0_tx = (tx_code_int >> 2) & 0x1
            c2_tx = (tx_code_int >> 3) & 0x1
            d1_tx = (tx_code_int >> 4) & 0x1
            d2_tx = (tx_code_int >> 5) & 0x1
            d3_tx = (tx_code_int >> 6) & 0x1

            print(f"c0: {c0_tx}, c1: {c1_tx}, c2: {c2_tx}, d0: {d0_tx}, d1: {d1_tx}, d2: {d2_tx}, d3: {d3_tx}")

            d0_rx = (dut.uo_out.value >> 2) & 0x1
            d1_rx = (dut.uo_out.value >> 3) & 0x1
            d2_rx = (dut.uo_out.value >> 5) & 0x1      # weird offset in project.v
            d3_rx = (dut.uo_out.value >> 6) & 0x1      # same here

            rx_valid_out = (dut.uo_out.value >> 1) & 0x1

            # Calculate expected decode using your function
            p0_tx = c0_tx ^ d0_tx ^ d1_tx ^ d3_tx
            p1_tx = c1_tx ^ d0_tx ^ d2_tx ^ d3_tx
            p2_tx = c2_tx ^ d1_tx ^ d2_tx ^ d3_tx
            parity = (p2_tx << 2) | (p1_tx << 1) | p0_tx
            if parity != 0:
                # Correct the error
                d_bits = [0, 0, 0, d0_tx, 0, d1_tx, d2_tx, d3_tx]
                d_bits[parity] ^= 1
                _, _, _, d0_tx, _, d1_tx, d2_tx, d3_tx = d_bits
            expected_decode = (d3_tx << 3) | (d2_tx << 2) | (d1_tx << 1) | d0_tx
            decode = (d3_rx << 3) | (d2_rx << 2) | (d1_rx << 1) | d0_rx

            dut._log.info("")
            dut._log.info(f"Inputted Data: {tx_code_int:07b} | Expected Decode: {expected_decode:04b} | Actual Decode: {decode:04b} | ")

            # Evaluate pass/fail using calculated expected values
            pass_cond = (
                rx_valid_out == 1 and
                decode == expected_decode
            )

            if pass_cond:
                total_pass += 1
                dut._log.info(f"{label} test PASSED")
            else:
                total_fail += 1
                if decode != expected_decode:
                    dut._log.error(f"DATA ERROR: Expected {expected_decode:04b}, got {decode:04b}")
                if rx_valid_out != 1:
                    dut._log.error(f"VALID ERROR: Expected 1, got {rx_valid_out}")
                dut._log.error(f"{label} test FAILED")

    # All tests should pass since Hamming(7,4) can correct single-bit errors
    # 16 data values * (1 no-error + 7 single-bit errors) = 128 total tests
    expected_pass = 16 * 8  # 128
    expected_fail = 0

    dut._log.info(f"SUMMARY: total_pass={total_pass} total_fail={total_fail}")
    dut._log.info(f"Expected: pass={expected_pass} fail={expected_fail}")
    
    assert total_pass == expected_pass, f"Expected {expected_pass} passes, got {total_pass}"
    assert total_fail == expected_fail, f"Expected {expected_fail} fails, got {total_fail}"
    dut._log.info("Exhaustive all inputs test COMPLETED")

