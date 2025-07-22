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
    actual_bits = []
    
    for i, bit in enumerate(expected_bits):
        # Sample in the middle of each bit
        await ClockCycles(dut.clk, BAUD_CYCLES // 2)
        actual = dut.uo_out[0].value.integer
        actual_bits.append(actual)
        dut._log.info(f"Bit {i}: Expected {bit}, Got {actual}")
        
        try:
            assert actual == bit, f"Mismatch at bit {i}: expected {bit}, got {actual}"
        except AssertionError as e:
            # If assertion fails, collect all bits before raising the exception
            await ClockCycles(dut.clk, BAUD_CYCLES // 2)
            # Continue collecting remaining bits
            remaining_bits = len(expected_bits) - i - 1
            for j in range(remaining_bits):
                await ClockCycles(dut.clk, BAUD_CYCLES)
                actual_next = dut.uo_out[0].value.integer
                actual_bits.append(actual_next)
            
            # Format comprehensive error message
            expected_str = ''.join(str(b) for b in expected_bits)
            actual_str = ''.join(str(b) for b in actual_bits)
            
            # Format data and frame details
            error_msg = f"\nTest failed at bit {i}:\n"
            error_msg += f"Input data: 0x{data_byte:02X} (binary: {data_byte:08b})\n"
            error_msg += f"Expected UART frame: {expected_str}\n"
            error_msg += f"Actual UART frame:   {actual_str}\n"
            
            # Add markers to highlight the difference
            marker = ' ' * (i + len("Actual UART frame:   ")) + "^"
            error_msg += marker
            
            raise AssertionError(error_msg) from e
            
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
    
    dut._log.info(f"Testing input: 0x{test_input:X} (binary: {test_input:04b})")
    dut._log.info(f"Expected Hamming code: 0x{expected_hamming:02X} (binary: {expected_hamming:08b})")
    dut._log.info(f"Expected UART frame: {''.join(str(b) for b in expected_frame)}")
    
    # Verify transmission
    try:
        await verify_uart_transmission(dut, expected_hamming, expected_frame)
    except AssertionError as e:
        dut._log.error(f"Test failed for input 0x{test_input:X} -> Hamming 0x{expected_hamming:02X}")
        raise

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
    
    dut._log.info(f"Testing input: 0x{test_input:X} (binary: {test_input:04b})")
    dut._log.info(f"Expected Hamming code: 0x{expected_hamming:02X} (binary: {expected_hamming:08b})")
    dut._log.info(f"Expected UART frame: {''.join(str(b) for b in expected_frame)}")
    
    # Verify transmission
    try:
        await verify_uart_transmission(dut, expected_hamming, expected_frame)
    except AssertionError as e:
        dut._log.error(f"Test failed for input 0x{test_input:X} -> Hamming 0x{expected_hamming:02X}")
        raise

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
    
    dut._log.info(f"Testing input: 0x{test_input:X} (binary: {test_input:04b})")
    dut._log.info(f"Expected Hamming code: 0x{expected_hamming:02X} (binary: {expected_hamming:08b})")
    dut._log.info(f"Expected UART frame: {''.join(str(b) for b in expected_frame)}")
    
    # Verify transmission
    try:
        await verify_uart_transmission(dut, expected_hamming, expected_frame)
    except AssertionError as e:
        dut._log.error(f"Test failed for input 0x{test_input:X} -> Hamming 0x{expected_hamming:02X}")
        raise

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
        
        dut._log.info(f"Testing input: 0x{test_input:X} (binary: {test_input:04b})")
        dut._log.info(f"Expected Hamming code: 0x{expected_hamming:02X} (binary: {expected_hamming:08b})")
        dut._log.info(f"Expected UART frame: {''.join(str(b) for b in expected_frame)}")
        
        # Verify transmission
        try:
            await verify_uart_transmission(dut, expected_hamming, expected_frame)
        except AssertionError as e:
            dut._log.error(f"Test failed for input 0x{test_input:X} -> Hamming 0x{expected_hamming:02X}")
            raise
        
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
        
        dut._log.info(f"Testing input: 0x{test_input:X} (binary: {test_input:04b})")
        dut._log.info(f"Expected Hamming code: 0x{expected_hamming:02X} (binary: {expected_hamming:08b})")
        dut._log.info(f"Expected UART frame: {''.join(str(b) for b in expected_frame)}")
        
        # Verify transmission
        try:
            await verify_uart_transmission(dut, expected_hamming, expected_frame)
        except AssertionError as e:
            dut._log.error(f"Test failed for input 0x{test_input:X} -> Hamming 0x{expected_hamming:02X}")
            raise
        
        # Wait for system to return to idle
        await ClockCycles(dut.clk, BAUD_CYCLES * 2)

@cocotb.test()
async def test_hamming_encoder_only(dut):
    """Test just the Hamming encoder part of the circuit"""
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    
    # Try each test input and directly examine outputs before UART
    for test_input in range(16):
        dut.ui_in.value = test_input
        
        # Wait for encoder to process
        await ClockCycles(dut.clk, 3)
        
        # Log the expected value
        expected_hamming = TEST_VECTORS[test_input]
        
        # If possible, try to access internal signals
        # Note: This depends on simulator support and might not work
        try:
            # Try to access the hamming_code signal if supported
            if hasattr(dut, "hamming_code"):
                actual_hamming = dut.hamming_code.value.integer
                dut._log.info(f"Input: 0x{test_input:X}, Expected Hamming: 0x{expected_hamming:02X}, Actual Hamming: 0x{actual_hamming:02X}")
        except Exception as e:
            dut._log.info(f"Could not access internal signals: {e}")
        
        # If we can't directly access internal signals, we can 
        # still check if the UART is transmitting anything
        await ClockCycles(dut.clk, 1)
        tx_value = dut.uo_out[0].value.integer
        dut._log.info(f"Input: 0x{test_input:X}, TX line: {tx_value}")
        
        # Wait between tests
        await ClockCycles(dut.clk, 5)

@cocotb.test()
async def test_check_shift_register(dut):
    """Test that examines the UART shift register"""
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    dut.ena.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    
    # Test input 0x5 (0101) which should produce a distinctive pattern
    test_input = 0x5
    dut.ui_in.value = test_input
    
    # Expected Hamming code
    expected_hamming = TEST_VECTORS[test_input]
    expected_frame = uart_frame(expected_hamming)
    expected_pattern = ''.join(str(b) for b in expected_frame)
    
    dut._log.info(f"Input: 0x{test_input:X} (binary: {test_input:04b})")
    dut._log.info(f"Expected Hamming: 0x{expected_hamming:02X} (binary: {expected_hamming:08b})")
    dut._log.info(f"Expected UART frame: {expected_pattern}")
    
    # Wait for hamming_valid signal to assert
    await ClockCycles(dut.clk, 5)
    
    # Now check the actual UART transmission bit by bit
    dut._log.info("Starting UART frame capture:")
    
    # Check for start bit first
    dut._log.info("Waiting for start bit (should be 0)...")
    for i in range(30):  # Try for several cycles
        bit_value = dut.uo_out[0].value.integer
        dut._log.info(f"Cycle {i}: TX = {bit_value}")
        if bit_value == 0:
            dut._log.info(f"Start bit detected at cycle {i}")
            break
        await ClockCycles(dut.clk, 1)
    
    # If we found the start bit, capture the next 8 data bits
    if bit_value == 0:
        data_bits = []
        # Wait half a bit period to sample in the middle
        await ClockCycles(dut.clk, BAUD_CYCLES // 2)
        
        # Capture 8 data bits
        for i in range(8):
            await ClockCycles(dut.clk, BAUD_CYCLES)
            bit_value = dut.uo_out[0].value.integer
            data_bits.append(bit_value)
            dut._log.info(f"Data bit {i}: {bit_value}")
        
        # Capture stop bit
        await ClockCycles(dut.clk, BAUD_CYCLES)
        stop_bit = dut.uo_out[0].value.integer
        dut._log.info(f"Stop bit: {stop_bit}")
        
        # Convert captured bits to byte
        captured_byte = 0
        for i, bit in enumerate(data_bits):
            captured_byte |= (bit << i)
        
        dut._log.info(f"Captured byte: 0x{captured_byte:02X} (binary: {captured_byte:08b})")
        dut._log.info(f"Expected byte: 0x{expected_hamming:02X} (binary: {expected_hamming:08b})")
