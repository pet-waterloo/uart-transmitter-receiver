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

    # --------------------------------------------------------- #
    # testing with hamming decoder

    async def perform_test(codeword):
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
                        f"Bit {i+1}/{len(codeword)} (value={bit}): PROCESSING CYCLE "
                        f"Valid={valid_bit}, Syndrome={syndrome:03b}, Data={data_bits:04b}, "
                        f"Full output={dut.uo_out.value:08b}"
                    )
                else:
                    dut._log.info(
                        f"Bit {i+1}/{len(codeword)} (value={bit}): counter={baud_counter} "
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
                    f"Final cycle: PROCESSING CYCLE "
                    f"Valid={valid_bit}, Syndrome={syndrome:03b}, Data={data_bits:04b}, "
                    f"Full output={dut.uo_out.value:08b}"
                )

    # ----------------------------------------------------------- #
    # Create a valid Hamming(7,4) codeword - "1111" data bits with appropriate parity
    # Format: [p1 p2 d1 p3 d2 d3 d4] where p=parity, d=data

    valid_codeword = "0001111"  # LSB first
    dut._log.info(f"Sending valid codeword: {valid_codeword}")

    await perform_test(valid_codeword)
    dut._log.info("Testing with error correction")

    # ----------------------------------------------------------- #
    # Reset the system
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 2)

    # ----------------------------------------------------------- #
    # Original codeword with a bit flipped
    error_input = "1000111"  # Flipped the first bit

    dut._log.info(f"Sending error sequence: {error_input}")

    await perform_test(error_input)

    # ----------------------------------------------------------- #
    # Check final output
    await ClockCycles(dut.clk, 1)
    valid_bit = (dut.uo_out.value & 0x80) >> 7
    data_bits = dut.uo_out.value & 0x0F
    syndrome_out = (dut.uo_out.value & 0x70) >> 4

    dut._log.info(
        f"Final result: Valid={int(valid_bit)}, Syndrome={int(syndrome_out):03b}, Data={int(data_bits):04b}, Full output={int(dut.uo_out.value):08b}"
    )

    # This should pass if your decoder is working
    # this will let me see the output results
    assert False
