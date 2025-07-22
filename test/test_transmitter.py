import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer

BAUD_CYCLES = 8

# Test vectors: (4-bit input, expected 7-bit Hamming code)
# Format: {4-bit input: 7-bit hamming code with 0 MSB padding to 8-bits}
TEST_VECTORS = {
    0x0: 0x00,  # 0000 -> 00000000 (all zeros)
    0x1: 0x71,  # 0001 -> 01110001 (LSB set)
    0x2: 0x62,  # 0010 -> 01100010 (bit 1 set)
    0x3: 0x13,  # 0011 -> 00010011 (bits 0,1 set)
    0x4: 0x54,  # 0100 -> 01010100 (bit 2 set)
    0x5: 0x25,  # 0101 -> 00100101 (bits 0,2 set)
    0x6: 0x36,  # 0110 -> 00110110 (bits 1,2 set)
    0x7: 0x47,  # 0111 -> 01000111 (bits 0,1,2 set)
    0x8: 0x38,  # 1000 -> 00111000 (bit 3 set)
    0x9: 0x49,  # 1001 -> 01001001 (bits 0,3 set)
    0xA: 0x5A,  # 1010 -> 01011010 (bits 1,3 set)
    0xB: 0x2B,  # 1011 -> 00101011 (bits 0,1,3 set)
    0xC: 0x1C,  # 1100 -> 00011100 (bits 2,3 set)
    0xD: 0x6D,  # 1101 -> 01101101 (bits 0,2,3 set)
    0xE: 0x7E,  # 1110 -> 01111110 (bits 1,2,3 set)
    0xF: 0x0F   # 1111 -> 00001111 (all ones)
}

def uart_frame(data_byte):
    """Convert 8-bit data into UART frame bits (start bit, data LSB→MSB, stop bit)"""
    return [0] + [int(x) for x in f"{data_byte:08b}"][::-1] + [1]

async def verify_uart_transmission(dut, data_byte, expected_bits):
    """Helper function to verify UART transmission"""
    for i, bit in enumerate(expected_bits):
        # Sample in the middle of each bit
        await ClockCycles(dut.clk, BAUD_CYCLES // 2)
        actual = dut.uo_out[0].value.integer
        dut._log.info(f"Bit {i}: Expected {bit}, Got {actual}")
        assert actual == bit, f"Mismatch at bit {i}: expected {bit}, got {actual}"
        await ClockCycles(dut.clk, BAUD_CYCLES // 2)

@cocotb.test()
async def test_all_zeros(dut):
    """Test transmission of all zeros input"""
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1

    # Set input to 0000
    test_input = 0x0
    dut.ui_in.value = test_input
    
    # Get expected Hamming code from test vectors
    expected_hamming = TEST_VECTORS[test_input]
    expected_frame = uart_frame(expected_hamming)
    
    # Verify transmission
    await verify_uart_transmission(dut, expected_hamming, expected_frame)

@cocotb.test()
async def test_all_ones(dut):
    """Test transmission of all ones input"""
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1

    # Set input to 1111
    test_input = 0xF
    dut.ui_in.value = test_input
    
    # Get expected Hamming code from test vectors
    expected_hamming = TEST_VECTORS[test_input]
    expected_frame = uart_frame(expected_hamming)
    
    # Verify transmission
    await verify_uart_transmission(dut, expected_hamming, expected_frame)

@cocotb.test()
async def test_alternating_pattern(dut):
    """Test transmission of alternating 1010 pattern"""
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1

    # Set input to 1010
    test_input = 0xA
    dut.ui_in.value = test_input
    
    # Get expected Hamming code from test vectors
    expected_hamming = TEST_VECTORS[test_input]
    expected_frame = uart_frame(expected_hamming)
    
    # Verify transmission
    await verify_uart_transmission(dut, expected_hamming, expected_frame)

@cocotb.test()
async def test_single_bit_patterns(dut):
    """Test transmission of single bit patterns (0001, 0010, 0100, 1000)"""
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # Test each single bit pattern
    for bit_pos in range(4):
        # Reset
        dut.rst_n.value = 0
        dut.ui_in.value = 0
        await ClockCycles(dut.clk, 2)
        dut.rst_n.value = 1

        # Set input with single bit set
        test_input = 1 << bit_pos
        dut.ui_in.value = test_input
        
        # Get expected Hamming code from test vectors
        expected_hamming = TEST_VECTORS[test_input]
        expected_frame = uart_frame(expected_hamming)
        
        # Verify transmission
        await verify_uart_transmission(dut, expected_hamming, expected_frame)
        
        # Wait for system to return to idle
        await ClockCycles(dut.clk, BAUD_CYCLES)

@cocotb.test()
async def test_counter_output(dut):
    """Test that the 3-bit counter is working correctly"""
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1

    # Check counter for 8 cycles (should count 0-7)
    last_count = -1
    for _ in range(8):
        await RisingEdge(dut.clk)
        current_count = (dut.uo_out.value.integer >> 1) & 0x7  # Counter output is on bits [3:1]
        if last_count != -1:
            assert (current_count == (last_count + 1) % 8), f"Counter did not increment correctly: {last_count} -> {current_count}"
        last_count = current_count

@cocotb.test()
async def test_all_input_patterns(dut):
    """Test all 16 possible 4-bit input patterns"""
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # Test all 16 possible 4-bit patterns
    for test_input in range(16):
        # Reset
        dut.rst_n.value = 0
        dut.ui_in.value = 0
        await ClockCycles(dut.clk, 2)
        dut.rst_n.value = 1

        # Set input value
        dut.ui_in.value = test_input
        
        # Get expected Hamming code from test vectors
        expected_hamming = TEST_VECTORS[test_input]
        expected_frame = uart_frame(expected_hamming)
        
        dut._log.info(f"Testing input 0x{test_input:X} -> Expected Hamming code 0x{expected_hamming:02X}")
        
        # Verify transmission
        await verify_uart_transmission(dut, expected_hamming, expected_frame)
        
        # Wait for system to return to idle
        await ClockCycles(dut.clk, BAUD_CYCLES * 2)

@cocotb.test()
async def test_hamming_code_encoding(dut):
    """Test the specific bit positions in the Hamming code"""
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())
    
    # Test case descriptions (test_input, hamming_description)
    test_cases = [
        (0x0, "All zeros"),
        (0x1, "D0 only (LSB)"),
        (0x2, "D1 only"),
        (0x4, "D2 only"),
        (0x8, "D3 only (MSB)"),
        (0xF, "All ones")
    ]
    
    for test_input, desc in test_cases:
        # Reset
        dut.rst_n.value = 0
        dut.ui_in.value = 0
        await ClockCycles(dut.clk, 2)
        dut.rst_n.value = 1
        
        # Set input value
        dut.ui_in.value = test_input
        
        # Get expected Hamming code
        expected_hamming = TEST_VECTORS[test_input]
        
        # Wait for valid output
        for _ in range(3):
            await RisingEdge(dut.clk)
        
        # Verify the bits are correctly set in the hamming_code signal
        # This test requires access to internal signals which may not be accessible in all test setups
        
        dut._log.info(f"Test case: {desc} - Input: {bin(test_input)[2:].zfill(4)}, "
                    f"Expected Hamming: {bin(expected_hamming)[2:].zfill(8)}")
        
        # Continue with transmission test to verify encoder works correctly
        expected_frame = uart_frame(expected_hamming)
        await verify_uart_transmission(dut, expected_hamming, expected_frame)
        
        # Wait for system to return to idle
        await ClockCycles(dut.clk, BAUD_CYCLES * 2)
