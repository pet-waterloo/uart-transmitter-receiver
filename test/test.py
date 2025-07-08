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


@cocotb.test()
async def test_error_free_data(dut):
    """Test the decoder with error-free Hamming code"""
    dut._log.info("Starting error-free data test")

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
    # Create a valid Hamming(7,4) codeword - "1111" data bits with appropriate parity
    # Format: [p1 p2 d1 p3 d2 d3 d4] where p=parity, d=data
    valid_codeword = "0001111"  # LSB first
    expected_data = 0b1111  # Expected decoded data bits

    dut._log.info(f"Sending valid codeword: {valid_codeword}")
    valid_bit, syndrome, data_bits = await perform_test(
        dut, valid_codeword, "Error-free"
    )

    # --------------------------------------------------------- #
    # Verify results
    dut._log.info(
        f"Final result: Valid={int(valid_bit)}, Syndrome={int(syndrome):03b}, "
        f"Data={int(data_bits):04b}"
    )

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
    error_input = "1001111"  # Flipped the first bit (p1)
    expected_data = 0b1111  # Expected corrected data bits

    dut._log.info(f"Sending error sequence: {error_input}")
    valid_bit, syndrome, data_bits = await perform_test(
        dut, error_input, "Error-correction"
    )

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
