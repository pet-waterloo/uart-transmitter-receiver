# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# Helper function to send bits and observe results
async def perform_test(dut, codeword, test_name):
    # Clock the data into the hamming decoder
    for i, bit in enumerate(codeword):
        # For each bit in the codeword, we need to wait for a full counter cycle
        # to ensure the bit is processed when baud_rate_counter == 7
        for counter_val in range(8):  # 0 through 7
            # Set bit 0 of ui_in to the current bit
            dut.ui_in.value = int(bit)

            # Clock once
            await ClockCycles(dut.clk, 1)

            # Get the current counter value
            baud_counter = (dut.uio_out.value >> 3) & 0x7

            # Log detailed information when we're at the processing cycle (counter == 7)
            if baud_counter == 7:
                valid_bit = (dut.uo_out.value >> 7) & 0x1
                syndrome = (dut.uo_out.value >> 4) & 0x7
                data_bits = dut.uo_out.value & 0xF

                dut._log.info(
                    f"{test_name} - Bit {i+1}/{len(codeword)} (value={bit}): PROCESSING CYCLE "
                    f"Valid={valid_bit}, Syndrome={syndrome:03b}, Data={data_bits:04b}, "
                    f"Full output={dut.uo_out.value:08b}"
                )
            else:
                dut._log.info(
                    f"{test_name} - Bit {i+1}/{len(codeword)} (value={bit}): counter={baud_counter} "
                    f"(waiting for counter=7)"
                )

    # Wait a few more cycles to ensure processing completes
    for i in range(8):
        await ClockCycles(dut.clk, 1)
        baud_counter = (dut.uio_out.value >> 3) & 0x7

        if baud_counter == 7:
            valid_bit = (dut.uo_out.value >> 7) & 0x1
            syndrome = (dut.uo_out.value >> 4) & 0x7
            data_bits = dut.uo_out.value & 0xF

            dut._log.info(
                f"{test_name} - Final cycle: PROCESSING CYCLE "
                f"Valid={valid_bit}, Syndrome={syndrome:03b}, Data={data_bits:04b}, "
                f"Full output={dut.uo_out.value:08b}"
            )

    # Return the final values for assertion checking
    valid_bit = (dut.uo_out.value >> 7) & 0x1
    syndrome = (dut.uo_out.value >> 4) & 0x7
    data_bits = dut.uo_out.value & 0xF

    return valid_bit, syndrome, data_bits


async def send_uart_byte(dut, data_bits):
    """Send a proper UART frame with start/stop bits and correct timing"""
    CYCLES_PER_BIT = 8
    
    # Print complete frame information
    dut._log.info(f"UART TX: Sending complete frame for data: {data_bits:07b}")

    # Idle state (HIGH)
    dut.ui_in.value = 1
    await ClockCycles(dut.clk, CYCLES_PER_BIT)
    dut._log.info(f"UART TX: Idle state complete")

    # Start bit (LOW)
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, CYCLES_PER_BIT)
    dut._log.info(f"UART TX: Start bit sent")
    
    # Debug output before sending data bits
    uart_valid = (dut.uio_out.value >> 7) & 0x1
    hamming_ena = (dut.uio_out.value >> 6) & 0x1
    counter = (dut.uio_out.value >> 3) & 0x7
    dut._log.info(f"UART STATUS: valid={uart_valid}, hamming_ena={hamming_ena}, counter={counter:03b}")

    # Data bits (LSB first)
    for i in range(7):  # 7 bits for Hamming(7,4)
        bit = (data_bits >> i) & 0x1
        dut.ui_in.value = bit
        dut._log.info(f"UART TX: Sending bit #{i} = {bit}")
        await ClockCycles(dut.clk, CYCLES_PER_BIT)
        
        # Debug output after each bit
        uart_valid = (dut.uio_out.value >> 7) & 0x1
        uart_data = (dut.uio_out.value) & 0x7F
        dut._log.info(f"UART BIT COMPLETE: bit={i}, valid={uart_valid}, data={uart_data:07b}")

    # Stop bit (HIGH)
    dut.ui_in.value = 1
    await ClockCycles(dut.clk, CYCLES_PER_BIT)
    dut._log.info(f"UART TX: Stop bit sent")

    # Return to idle (HIGH)
    dut.ui_in.value = 1
    await ClockCycles(dut.clk, CYCLES_PER_BIT)
    dut._log.info(f"UART TX: Frame complete, returned to idle")
    
    # Final status
    uart_valid = (dut.uio_out.value >> 7) & 0x1
    hamming_ena = (dut.uio_out.value >> 6) & 0x1
    counter = (dut.uio_out.value >> 3) & 0x7
    syndrome = (dut.uio_out.value >> 0) & 0x7
    dut._log.info(f"UART FINAL STATUS: valid={uart_valid}, hamming_ena={hamming_ena}, counter={counter:03b}, syndrome={syndrome:03b}")


@cocotb.test()
async def test_error_free_data(dut):
    """Test the decoder with error-free Hamming code"""
    dut._log.info("Starting error-free data test")

    # Set the clock period to 50 us (20 KHz)
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())

    # Log initial state
    dut._log.info(f"Initial state - uo_out: {str(dut.uo_out.value)}, uio_out: {str(dut.uio_out.value)}")
    
    # Reset
    dut._log.info("Applying reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    dut._log.info("Reset complete - all registers should be cleared")
    dut._log.info(f"Post-reset state - uo_out: {str(dut.uo_out.value)}, uio_out: {str(dut.uio_out.value)}")

    # --------------------------------------------------------- #
    valid_hamming = 0b0001111  # Binary format
    expected_data = 0b1111     # Expected decoded data bits

    dut._log.info(f"Sending valid codeword: {valid_hamming:07b}")
    
    # Send proper UART frame with the Hamming code
    await send_uart_byte(dut, valid_hamming)

    
    # Wait for processing to complete with monitoring
    dut._log.info("Waiting for processing to complete with monitoring...")
    for i in range(24):
        await ClockCycles(dut.clk, 1)
        if i % 4 == 0:  # Print every few cycles to reduce log volume
            uart_valid = (dut.uio_out.value >> 7) & 0x1
            hamming_ena = (dut.uio_out.value >> 6) & 0x1
            counter = (dut.uio_out.value >> 3) & 0x7
            syndrome = (dut.uio_out.value >> 0) & 0x7
            valid_out = (dut.uo_out.value >> 7) & 0x1
            decoded_data = dut.uo_out.value & 0xF
            dut._log.info(f"Cycle {i}: uart_valid={uart_valid}, hamming_ena={hamming_ena}, " + 
                         f"counter={counter:03b}, syndrome={syndrome:03b}, " +
                         f"valid_out={valid_out}, decoded_data={decoded_data:04b}")
    
    # Extract results
    valid_bit = (dut.uo_out.value >> 7) & 0x1
    syndrome = (dut.uo_out.value >> 4) & 0x7
    data_bits = dut.uo_out.value & 0xF

    # Detailed debug
    dut._log.info(f"Raw uo_out value: {dut.uo_out.value:08b}")
    dut._log.info(f"Raw uio_out value: {dut.uio_out.value:08b}")
    
    # --------------------------------------------------------- #
    # Verify results
    dut._log.info(
        f"Final result: Valid={int(valid_bit)}, Syndrome={int(syndrome):03b}, "
        f"Data={int(data_bits):04b}"
    )

    # More detailed assertions
    if syndrome != 0:
        dut._log.error(f"SYNDROME ERROR: Expected 0, got {syndrome:03b}")
    if data_bits != expected_data:
        dut._log.error(f"DATA ERROR: Expected {expected_data:04b}, got {data_bits:04b}")
    if valid_bit != 1:
        dut._log.error(f"VALID ERROR: Expected 1, got {valid_bit}")

    # Continue with assertions
    # Syndrome should be 0 (no errors)
    assert syndrome == 0, f"Expected syndrome 0, got {syndrome}"

    # Data should match expected
    assert (
        data_bits == expected_data
    ), f"Expected data {expected_data:04b}, got {data_bits:04b}"

    # Valid should be 1
    assert valid_bit == 1, f"Expected valid bit 1, got {valid_bit}"

    dut._log.info("Error-free data test PASSED")


@cocotb.test()
async def test_single_bit_error(dut):
    """Test the decoder with a single bit error in the Hamming code"""
    dut._log.info("Starting single bit error test")

    # Set the clock period to 50 us (20 KHz)
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1

    # --------------------------------------------------------- #
    # Original codeword with a bit flipped
    # Original: "0001111", Flipped first bit: "1001111"
    error_hamming = 0b1001111  # Flipped the first bit (p1)
    expected_data = 0b1111     # Expected corrected data bits

    dut._log.info(f"Sending error sequence: {error_hamming:07b}")
    
    # Send proper UART frame with the error Hamming code
    await send_uart_byte(dut, error_hamming)
    
    # Wait for processing to complete
    await ClockCycles(dut.clk, 24)
    
    # Extract results
    valid_bit = (dut.uo_out.value >> 7) & 0x1
    syndrome = (dut.uo_out.value >> 4) & 0x7
    data_bits = dut.uo_out.value & 0xF

    # --------------------------------------------------------- #
    # Verify results
    dut._log.info(
        f"Final result: Valid={int(valid_bit)}, Syndrome={int(syndrome):03b}, "
        f"Data={int(data_bits):04b}"
    )

    # Syndrome should be non-zero (error detected)
    assert syndrome != 0, f"Expected non-zero syndrome, got {syndrome}"

    # Data should still match expected (error corrected)
    assert (
        data_bits == expected_data
    ), f"Expected data {expected_data:04b}, got {data_bits:04b}"

    # Valid should be 1 (successful correction)
    assert valid_bit == 1, f"Expected valid bit 1, got {valid_bit}"

    dut._log.info("Single bit error test PASSED")


@cocotb.test()
async def test_basic_operation(dut):
    """Test basic UART receiver operation"""
    dut._log.info("Starting basic operation test")
    
    # Start clock and reset
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())

    # Reset everything
    dut.rst_n.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1

    # Send two different frames with different Hamming codes
    test_codes = [0b0001111, 0b0110101]  # Valid Hamming codes
    
    for i, code in enumerate(test_codes):
        dut._log.info(f"Sending test frame {i+1}: {code:07b}")
        
        # Send the UART frame with this code
        await send_uart_byte(dut, code)
        
        # Wait for processing
        await ClockCycles(dut.clk, 16)
        
        # Log the results
        valid_bit = (dut.uo_out.value >> 7) & 0x1
        syndrome = (dut.uo_out.value >> 4) & 0x7
        data_bits = dut.uo_out.value & 0xF
        
        dut._log.info(
            f"Frame {i+1} results: Valid={valid_bit}, "
            f"Syndrome={syndrome:03b}, Data={data_bits:04b}"
        )
