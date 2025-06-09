<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project implements a Hamming (7,4) decoder that can detect and correct single-bit errors in transmitted data. The system consists of:

1. **Input Processing**: Takes a serial bit stream through `decode_in` and shifts it into a 7-bit register
2. **3-bit Counter**: Tracks how many bits have been received (0-7 states)
3. **Hamming Decoding**: When 7 bits are collected, applies Hamming error detection and correction to extract 4 data bits
4. **Output Control**: Provides a `valid_out` signal when decoded data is ready and outputs the 4-bit corrected data

The decoder operates by:
- Collecting 7 bits of input data (4 data bits + 3 parity bits)
- Using parity check equations to detect single-bit errors
- Correcting any detected errors
- Outputting the original 4 data bits with errors corrected

## How to test

1. **Reset the system**: Assert `rst_n` low, then high
2. **Enable operation**: Set `ena` high to start decoding
3. **Send 7-bit codeword**: Input 7 bits serially through `decode_in`, one bit per clock cycle
4. **Check output**: After 7 clock cycles, `valid_out` will go high and `decode_out` will contain the 4 corrected data bits
5. **Test error correction**: Introduce single-bit errors in the 7-bit input and verify the decoder corrects them

Example test sequence:
- Input: 7'b1010101 (with possible single-bit error)
- Output: 4-bit corrected data word

## External hardware

No external hardware required. The design uses only the standard Tiny Tapeout interface:
- Clock and reset from the board
- Serial data input through dedicated input pins
- Parallel data output through dedicated output pins
