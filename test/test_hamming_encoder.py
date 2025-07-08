import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

@cocotb.test()
async def test_hamming_encoder(dut):
    """Test the Hamming(7,4) encoder module"""

    # Start clock (adjust period as needed)
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.ena.value = 0
    dut.data_in.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1

    # Test vectors: (input, expected output)
    test_vectors = [
        (0b0000, None),  # Fill in expected code_out for each input
        (0b0001, None),
        (0b0010, None),
        (0b0101, None),
        (0b1111, None),
    ]

    for data, expected in test_vectors:
        dut.data_in.value = data
        dut.ena.value = 1
        await RisingEdge(dut.clk)
        dut.ena.value = 0
        await RisingEdge(dut.clk)

        # Log and check output
        dut._log.info(f"Input: {data:04b}, Output: {dut.code_out.value.integer:07b}, Valid: {dut.valid_out.value}")
        assert dut.valid_out.value == 1, "Valid flag should be high after encoding"
        # If you know the expected output, uncomment the next line:
        # assert dut.code_out.value.integer == expected, f"Expected {expected:07b}, got {dut.code_out.value.integer:07b}"

        await ClockCycles(dut.clk, 1)