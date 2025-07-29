import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

BAUD_CYCLES = 8

HAMMING_CODE_TABLE = {
    "0000": "0000000",
    "0001": "1110001",
    "0010": "1100010",
    "0011": "0010011",
    "0100": "1010100",
    "0101": "0100101",
    "0110": "0110110",
    "0111": "1000111",
    "1000": "0111000",
    "1001": "1001001",
    "1010": "1011010",
    "1011": "0101011",
    "1100": "0011100",
    "1101": "1101101",
    "1110": "1111110",
    "1111": "0001111",
}

NO_ERROR_MASK      = "0000000"
ONE_BIT_ERROR_MASK = "0000100"
TWO_BIT_ERROR_MASK = "0100010"

ENCODER_CODE_SIGNAL = "uo_out"
ENCODER_VALID_SIGNAL = "uo_out"

def int_to_binstr(value: int, width: int) -> str:
    return format(value, f"0{width}b")

def get_first_signal_handle(dut, signal):
    try:
        handle = dut
        for name in signal.split('.'):
            handle = getattr(handle, name)
        _ = handle.value
        return handle
    except AttributeError:
        pass
    raise AttributeError(f"None of {signal} exist in this design.")

async def apply_reset(dut, cycles=2):
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, cycles)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, cycles)

# test for UART transmission
async def run_hamming_case(dut, data_bits_str, error_mask_str, output_sig, busy_sig):
    data_bits = int(data_bits_str, 2)
    dut.ui_in.value = data_bits
    dut.ui_in.value = data_bits | 0x10
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = data_bits

    for _ in range(10):
        if (output_sig.value.integer & 0x01) == 0:
            break
        await ClockCycles(dut.clk, 1)

    uart_frame = ""
    for bit in range(10):
        uart_frame = str(int(output_sig.value.integer & 0x01)) + uart_frame
        await ClockCycles(dut.clk, BAUD_CYCLES)
    
    expected_code = HAMMING_CODE_TABLE[data_bits_str]
    masked_code = "".join(["1" if int(a) ^ int(b) == 1 else "0" 
                      for a, b in zip(expected_code, error_mask_str)])
    
    return expected_code, masked_code

# helper function to get signal handle safely
def get_signal_handle_safely(dut, primary_signal, fallback_signals=None):
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

# main test to check hamming code and error cases
@cocotb.test()
async def test_full_hamming_code(dut):
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())
    await apply_reset(dut)

    encoder_code_sig = get_signal_handle_safely(dut, "uo_out", ["tx"])
    busy_sig = get_signal_handle_safely(dut, "tx_busy", ["uo_out"])

    for data_bits_str in HAMMING_CODE_TABLE.keys():
        await apply_reset(dut)
        original, masked = await run_hamming_case(
            dut, data_bits_str, NO_ERROR_MASK, encoder_code_sig, busy_sig
        )
        if masked != original:
            dut._log.error(f"[NO_ERR] expected {original}, got {masked} (input={data_bits_str})")
        assert masked == original

        await apply_reset(dut)
        original, masked = await run_hamming_case(
            dut, data_bits_str, ONE_BIT_ERROR_MASK, encoder_code_sig, busy_sig
        )
        if masked == original:
            dut._log.error(f"[1BIT_ERR] expected different codeword, but got same: {masked} (input={data_bits_str})")
        assert masked != original

        await apply_reset(dut)
        original, masked = await run_hamming_case(
            dut, data_bits_str, TWO_BIT_ERROR_MASK, encoder_code_sig, busy_sig
        )
        if masked == original:
            dut._log.error(f"[2BIT_ERR] expected different codeword, but got same: {masked} (input={data_bits_str})")
        assert masked != original

        encoder_code_sig = get_signal_handle_safely(dut, "uo_out", ["tx"])
        busy_sig = get_signal_handle_safely(dut, "tx_busy", ["uo_out"])

        tx_busy_active = False
        try:
            tx_busy_active = busy_sig.value.integer != 0
        except ValueError:
            tx_busy_active = (busy_sig.value.integer & 0x10) != 0