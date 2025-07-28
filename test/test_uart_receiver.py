import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer

async def send_uart_frame(dut, data_bits, test_name):
    """
    Send a UART frame with the specified data bits.
    Using inverted UART format where:
    - Start bit is LOW (0)
    - Data bits are sent LSB first
    - Stop bit is LOW (0) - inverted UART format
    """
    # Each bit lasts for 8 clock cycles (based on sample_counter in the design)
    BIT_CYCLES = 8
    
    dut._log.info(f"{test_name} - Sending UART frame with data: {data_bits:07b}")
    
    # Send start bit (LOW = 0)
    dut.rx.value = 0
    await ClockCycles(dut.clk, BIT_CYCLES)
    
    # Send data bits (LSB first)
    for i in range(7):
        bit = (data_bits >> i) & 0x1
        dut.rx.value = bit
        await ClockCycles(dut.clk, BIT_CYCLES)
        dut._log.info(f"{test_name} - Sent bit {i}: {bit}")
    
    # Send stop bit (LOW = 0 for inverted UART)
    dut.rx.value = 0
    await ClockCycles(dut.clk, BIT_CYCLES)
    
    # Return to idle state (HIGH = 1)
    dut.rx.value = 1
    await ClockCycles(dut.clk, 2)  # Short idle period

@cocotb.test()
async def test_uart_basic_reception(dut):
    """Test basic UART reception functionality"""
    # Start clock
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    dut.rx.value = 1  # Idle state
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    
    # Test with various data patterns
    test_data = [
        0b1010101,  # Alternating bits
        0b0000000,  # All zeros
        0b1111111,  # All ones
        0b1000001,  # Edge bits
        0b0111110   # Middle bits
    ]
    
    for i, data in enumerate(test_data):
        # Before transmission, check we're in idle state
        await ClockCycles(dut.clk, 5)
        assert dut.valid_out.value == 0, "valid_out should be 0 in idle state"
        
        # Send the UART frame
        await send_uart_frame(dut, data, f"Basic test {i+1}")
        
        # Wait for processing and check reception
        await ClockCycles(dut.clk, 5)
        
        # At this point valid_out should have pulsed and data_out should contain our data
        assert dut.data_out.value == data, f"Expected {data:07b}, got {dut.data_out.value:07b}"
        
        # Log the result
        dut._log.info(f"Test {i+1}: Received data: {dut.data_out.value:07b}")

@cocotb.test()
async def test_uart_false_start(dut):
    """Test handling of false start bits"""
    # Start clock
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.rx.value = 1  # Idle state
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    
    # Send a false start bit (LOW then returns to HIGH too soon)
    dut._log.info("Testing false start bit")
    dut.rx.value = 0  # Start bit
    await ClockCycles(dut.clk, 3)  # Not long enough for full bit
    dut.rx.value = 1  # Back to idle
    
    # The receiver should reject this and stay in IDLE
    await ClockCycles(dut.clk, 20)
    
    # Now send a valid frame to verify receiver is still working
    test_data = 0b1010101
    await send_uart_frame(dut, test_data, "After false start")
    
    # Wait and verify
    await ClockCycles(dut.clk, 5)
    assert dut.data_out.value == test_data, f"Expected {test_data:07b}, got {dut.data_out.value:07b}"

@cocotb.test()
async def test_uart_back_to_back(dut):
    """Test back-to-back frame reception"""
    # Start clock
    clock = Clock(dut.clk, 50, units="us")
    cocotb.start_soon(clock.start())
    
    # Reset
    dut.ena.value = 1
    dut.rx.value = 1  # Idle state
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    
    # Send two frames back-to-back
    data1 = 0b0101010
    data2 = 0b1010101
    
    # Send first frame
    await send_uart_frame(dut, data1, "Back-to-back 1")
    
    # Minimal idle time (just 1 cycle)
    await ClockCycles(dut.clk, 1)
    
    # Send second frame immediately
    await send_uart_frame(dut, data2, "Back-to-back 2")
    
    # Wait and verify the receiver got the second frame
    await ClockCycles(dut.clk, 5)
    assert dut.data_out.value == data2, f"Expected {data2:07b}, got {dut.data_out.value:07b}"
    
    dut._log.info(f"Back-to-back test passed: received {dut.data_out.value:07b}")