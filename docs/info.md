# 298a Design Document

## UART Transmitter + Receiver

**Peter and John Zhang**

[**Download the full design document (PDF)**](./DesignDocument.pdf)

---

## Introduction

This project implements a self-contained UART transmitter and receiver with built-in Hamming(7,4) error-correction, synthesized in Verilog for the Tiny Tapeout flow. By inserting a lightweight Hamming encoder before framing each byte and a matching decoder after reception, it guarantees single-bit error detection and correction over an asynchronous serial or wireless link. Designed for the ECE 298A’s prototyping lab, this design demonstrates how digital communication, finite-state controllers, and error correcting codes can be combined into a compact, silicon-ready IP block.

---

## Objectives & Main Function

The main objective of this project is to implement functional components of a UART communication system in Verilog. The chip design is separated into 2 distinct sections:

- **UART Transmitter**
- **UART Receiver**

The transmitter and receiver both integrate a Hamming(7,4) encoder/decoder for single-bit error detection and correction—delivering a robust, error-corrected asynchronous serial link and demonstrating key digital-design skills (finite-state machines, clock-division, coding theory, and testbench verification) in the ECE 298A prototyping flow.

### Main Function

The goal is to reliably send and receive 4-bit data over an asynchronous serial link by:

- **Transmitter**: Converting parallel bytes into start-framed Hamming-encoded bit streams
- **Receiver**: Sampling and reassembling those streams, correcting any single-bit errors, and outputting the original bytes

This ensures robust, error-corrected communication between two Verilog IP blocks.

---

## Design Specifications

### [1] Key Components

- **8x Oversampler**  
  Generates periodic “sample” ticks at a fixed rate of 8× the baud rate.

- **Finite State Machine**  
  Controls the 4 phases:

  - `IDLE` – line should be 1 (high)
  - `START` – reads 8 cycles of 0 (low)
  - `DATA` – reads 8 bits (64 cycles of data)
  - `STOP` – reads 8 cycles of 1 (high)

- **Hamming(7,4) Encoder/Decoder**  
  Inserted before transmitting and after receiving 4 bits of data.

  - **TX Encoder**:

    - Receives `[d0, d1, d2, d3]` as input data
    - Calculates 3 check bits
    - Outputs 7 bits as `[c0, c1, d0, c2, d1, d2, d3]`

  - **RX Decoder**:
    - Receives `[c0, c1, d0, c2, d1, d2, d3]`
    - Calculates 3 parity bits
    - Performs bit correction
    - Outputs `[d0, d1, d2, d3]` parallel bits of data

- **Serial I/O Streams**
  - Input – Single-bit `RX` line
  - Output – Single-bit `TX` line

---

### [2] Configuration Parameters

| Parameter          | Value   |
| ------------------ | ------- |
| Clock Speed        | 50 MHz  |
| Baud Rate          | 650 KHz |
| UART Protocol Bits |         |
| - IDLE bit         | 1       |
| - START bit        | 0       |
| - STOP bit         | 1       |

---

## IO Design

### [1] IO Lines for General Usage

| Line               | Description                           |
| ------------------ | ------------------------------------- |
| `tx_data_in[3:0]`  | Feeds 4-bit parallel data into the TX |
| `tx_data_out`      | Outputs UART data stream from TX      |
| `rx_data_in`       | Inputs UART data stream into RX       |
| `rx_data_out[3:0]` | Outputs 4-bit parallel data from RX   |
| `clk`              | Shared system clock                   |
| `enable`           | Activates/deactivates system          |

### [2] Debug IO Lines

| Line                  | Description                    |
| --------------------- | ------------------------------ |
| `tx_check_bits[2:0]`  | Calculated check bits from TX  |
| `tx_state_bits[1:0]`  | TX FSM state bits              |
| `rx_parity_bits[2:0]` | Calculated parity bits from RX |
| `rx_state_bits[1:0]`  | RX FSM state bits              |

---

## Testing & Verification Plan

### `test_full_hamming_code`

Verifies the UART transmitter and Hamming encoder by testing all 4-bit values. It checks:

- Correct codeword in error-free case
- Codeword changes when 1 or 2 bits are flipped
- Assertions validate expected behavior

### `test_error_free_data`

Tests the UART receiver and decoder with valid codewords:

- Decoder output matches expected 4-bit value
- Syndrome = 0 (no error)
- Valid signal is asserted

### `test_single_bit_error`

Tests decoder's ability to fix single-bit errors:

- Syndrome ≠ 0 (error detected)
- Correct decoded output
- Valid signal is asserted
