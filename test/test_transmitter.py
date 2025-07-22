import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer

BAUD_CYCLES = 8

def calculate_hamming_74(data_in):
    """Calculate Hamming(7,4) code for given 4-bit data"""
    # Extract individual bits
    d0, d1, d2, d3 = [(data_in >> i) & 1 for i in range(4)]
    
    # Calculate parity bits
    p1 = d0 ^ d1 ^ d3
    p2 = d0 ^ d2 ^ d3
    p3 = d1 ^ d2 ^ d3
    
    # Assemble 7-bit Hamming code
    hamming = (p1 << 6) | (p2 << 5) | (d0 << 4) | (p3 << 3) | (d1 << 2) | (d2 << 1) | d3
    
    # Add 0 as MSB to make it 8 bits as per project.v
    return hamming

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
    
    # Calculate expected Hamming code
    expected_hamming = calculate_hamming_74(test_input)
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
    
    # Calculate expected Hamming code
    expected_hamming = calculate_hamming_74(test_input)
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
    
    # Calculate expected Hamming code
    expected_hamming = calculate_hamming_74(test_input)
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
        
        # Calculate expected Hamming code
        expected_hamming = calculate_hamming_74(test_input)
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
