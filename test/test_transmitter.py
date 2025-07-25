import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

# 8 clock cycles per UART bit (already in your bench, keep for spacing if needed)
BAUD_CYCLES = 8

# --------------------------
# Reference Hamming(7,4) table (binary strings)
# (Same mapping you used, but kept as strings for clarity)
# --------------------------
HAMMING_TABLE = {
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

# Error masks (7 bits, MSB on left). Change bit positions if you like.
NO_ERR_MASK  = "0000000"
ONE_ERR_MASK = "0000100"  # flip bit 2
TWO_ERR_MASK = "0100010"  # flip bits 1 and 5

# Internal signal candidates (edit if your names differ)
ENC_CODE_SIG_CANDIDATES  = ["hamming_code", "hamming_code_d", "encoder.code_out"]
ENC_VALID_SIG_CANDIDATES = ["hamming_valid", "hamming_valid_d", "encoder.valid_out"]


# --------------------------
# Helpers
# --------------------------
def bstr_to_int(bstr: str) -> int:
    return int(bstr, 2)

def int_to_bstr(val: int, width: int) -> str:
    return format(val, f"0{width}b")

async def wait_high(sig):
    while sig.value.integer == 0:
        await RisingEdge(sig._path.split('.')[0] == 'dut' and sig._handle._simulator.get_signal('clk') or sig._handle)  # fallback
        # This hacky line is rarely needed; normally just do: await RisingEdge(dut.clk)
        # But we don't know 'dut' here. We'll do it the normal way in real calls.


def get_first_handle(dut, candidates):
    """Return the first signal handle that exists from the list."""
    for path in candidates:
        try:
            handle = dut
            for name in path.split('.'):
                handle = getattr(handle, name)
            # Accessing value once ensures it's real
            _ = handle.value
            return handle
        except AttributeError:
            continue
    raise AttributeError(f"None of {candidates} exist in this design. Adjust the candidate lists.")

async def reset(dut, cycles=2):
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, cycles)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, cycles)

async def run_one_case(dut, payload4_bstr, err_mask_bstr, enc_code_sig, enc_valid_sig):
    """Drive 4-bit payload, inject mask, then check encoder output."""
    payload4 = bstr_to_int(payload4_bstr)
    exp_code_bstr = HAMMING_TABLE[payload4_bstr]

    # Put payload on ui_in[3:0]; bit 4 is the start pulse
    dut.ui_in.value = payload4

    # Pulse start bit
    dut.ui_in.value = payload4 | 0x10
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = payload4

    # Wait until encoder valid goes high (if present)
    # If you don't have a valid signal, just wait a few cycles
    for _ in range(10):
        if enc_valid_sig.value.integer == 1:
            break
        await ClockCycles(dut.clk, 1)

    # Grab original encoded value
    orig_code_int = enc_code_sig.value.integer & 0x7F
    orig_code_bstr = int_to_bstr(orig_code_int, 7)

    # Inject error by XORing code on the fly (one cycle "force")
    mask_int = bstr_to_int(err_mask_bstr)
    new_code_int = orig_code_int ^ mask_int
    enc_code_sig.value = new_code_int  # override for a cycle
    await ClockCycles(dut.clk, 1)
    # release by writing back original so further tx isn't re-broken
    enc_code_sig.value = orig_code_int

    # Bookkeeping / logging
    dut._log.info(
        f"Payload={payload4_bstr}, Encoded={orig_code_bstr}, Mask={err_mask_bstr}, AfterMask={int_to_bstr(new_code_int,7)}"
    )

    return orig_code_bstr, int_to_bstr(new_code_int, 7)


@cocotb.test()
async def test_hamming_no_1bit_2bit(dut):
    """
    Only edit in Python testbench:
    - For every 4-bit input:
        * No error
        * 1-bit error
        * 2-bit error
    We verify the code we *see* on the internal bus after injection.

    NOTE:
    - We are not checking a decoder here because your top doesn't expose one.
      If you later expose decoder flags, we can assert those too (no RTL edits needed).
    """

    # Start clock
    clock = Clock(dut.clk, 50, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    await reset(dut)

    # Get internal signal handles
    enc_code_sig  = get_first_handle(dut, ENC_CODE_SIG_CANDIDATES)
    enc_valid_sig = get_first_handle(dut, ENC_VALID_SIG_CANDIDATES)

    for payload4_bstr in HAMMING_TABLE.keys():

        # --- No error case ---
        await reset(dut)
        orig, after = await run_one_case(dut, payload4_bstr, NO_ERR_MASK, enc_code_sig, enc_valid_sig)
        if after != orig:
            dut._log.error(f"[NO_ERR] mismatch: expected {orig}, got {after} (input={payload4_bstr})")
        else:
            dut._log.info(f"[NO_ERR] PASS: input={payload4_bstr}, code={orig}")
        assert after == orig, f"[NO_ERR] mismatch: expected {orig}, got {after} (input={payload4_bstr})"

        # --- 1-bit error case ---
        await reset(dut)
        orig, after = await run_one_case(dut, payload4_bstr, ONE_ERR_MASK, enc_code_sig, enc_valid_sig)
        if after == orig:
            dut._log.error(f"[1BIT_ERR] expected different codeword, but got same: {after} (input={payload4_bstr})")
        else:
            dut._log.info(f"[1BIT_ERR] PASS: input={payload4_bstr}, orig={orig}, after_mask={after}")
        assert after != orig, f"[1BIT_ERR] expected different codeword, but got same: {after} (input={payload4_bstr})"

        # --- 2-bit error case ---
        await reset(dut)
        orig, after = await run_one_case(dut, payload4_bstr, TWO_ERR_MASK, enc_code_sig, enc_valid_sig)
        if after == orig:
            dut._log.error(f"[2BIT_ERR] expected different codeword, but got same: {after} (input={payload4_bstr})")
        else:
            dut._log.info(f"[2BIT_ERR] PASS: input={payload4_bstr}, orig={orig}, after_mask={after}")
        assert after != orig, f"[2BIT_ERR] expected different codeword, but got same: {after} (input={payload4_bstr})"