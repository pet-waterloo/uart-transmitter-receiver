import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

BAUD_CYCLES = 8  # UART oversampling factor

# test vectors for hamming 7,4 code
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

# Error masks for codeword bit flips
NO_ERROR_MASK      = "0000000"
ONE_BIT_ERROR_MASK = "0000100"
TWO_BIT_ERROR_MASK = "0100010"

# encoder output signals
ENCODER_CODE_SIGNAL = "hamming_code"
ENCODER_VALID_SIGNAL = "hamming_valid"

def int_to_binstr(value: int, width: int) -> str:
    return format(value, f"0{width}b")

def get_first_signal_handle(dut, signal):
    # return signal handle if it exists in the DUT
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
    # reset DUT and clear inputs
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, cycles)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, cycles)

async def run_hamming_case(dut, data_bits_str, error_mask_str, encoder_code_sig, encoder_valid_sig):
    # drive 4-bit input, pulse start, wait for valid, inject error mask
    data_bits = int(data_bits_str, 2)
    expected_code_str = HAMMING_CODE_TABLE[data_bits_str]

    dut.ui_in.value = data_bits
    dut.ui_in.value = data_bits | 0x10  # pulse start
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = data_bits

    # wait for encoder valid
    for _ in range(10):
        if encoder_valid_sig.value.integer == 1:
            break
        await ClockCycles(dut.clk, 1)

    # get codeword, apply error mask for 1 cycle
    original_code_int = encoder_code_sig.value.integer & 0x7F
    original_code_str = int_to_binstr(original_code_int, 7)
    mask_int = int(error_mask_str, 2)
    masked_code_int = original_code_int ^ mask_int
    encoder_code_sig.value = masked_code_int
    await ClockCycles(dut.clk, 1)
    encoder_code_sig.value = original_code_int

    dut._log.info(
        f"Input={data_bits_str}, Encoded={original_code_str}, Mask={error_mask_str}, AfterMask={int_to_binstr(masked_code_int,7)}"
    )
    return original_code_str, int_to_binstr(masked_code_int, 7)

@cocotb.test()
async def test_full_hamming_code(dut):
    # For each 4-bit input, check: no error, 1-bit error, 2-bit error
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())
    await apply_reset(dut)

    encoder_code_sig  = get_first_signal_handle(dut, ENCODER_CODE_SIGNAL)
    encoder_valid_sig = get_first_signal_handle(dut, ENCODER_VALID_SIGNAL)

    for data_bits_str in HAMMING_CODE_TABLE.keys():
        await apply_reset(dut)
        original, masked = await run_hamming_case(
            dut, data_bits_str, NO_ERROR_MASK, encoder_code_sig, encoder_valid_sig
        )
        if masked != original:
            dut._log.error(f"[NO_ERR] expected {original}, got {masked} (input={data_bits_str})")
        assert masked == original

        await apply_reset(dut)
        original, masked = await run_hamming_case(
            dut, data_bits_str, ONE_BIT_ERROR_MASK, encoder_code_sig, encoder_valid_sig
        )
        if masked == original:
            dut._log.error(f"[1BIT_ERR] expected different codeword, but got same: {masked} (input={data_bits_str})")
        assert masked != original

        await apply_reset(dut)
        original, masked = await run_hamming_case(
            dut, data_bits_str, TWO_BIT_ERROR_MASK, encoder_code_sig, encoder_valid_sig
        )
        if masked == original:
            dut._log.error(f"[2BIT_ERR] expected different codeword, but got same: {masked} (input={data_bits_str})")
        assert masked != original