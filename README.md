![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# UART Transmitter & Receiver Project

- [Read the official documentation for our project](https://docs.google.com/document/d/1tlF-jqzEoZz30VtqMln9JiZ-5Pucy0jMslVNLtq-4XA/edit?usp=sharing)

## Overview

This project implements a UART (Universal Asynchronous Receiver/Transmitter) system in Verilog, including both transmitter and receiver modules. It features Hamming(7,4) encoding/decoding for error detection and correction, and is designed for simulation and hardware verification.

## Directory Structure

```
├── src/
│   ├── config.json           # Project configuration file
│   ├── counter_2b.v          # 2-bit counter module
│   ├── counter_3b.v          # 3-bit counter module
│   ├── counter_8b.v          # 8-bit counter module
│   ├── hamming_decoder_74.v  # Hamming(7,4) decoder module
│   ├── hamming_encoder_74.v  # Hamming(7,4) encoder module
│   ├── project.v             # Top-level project module
│   ├── statemachine_4.v      # 4-state state machine module
│   ├── uart_receiver.v       # UART receiver module
│   └── uart_transmitter.v    # UART transmitter module
├── test/
│   ├── Makefile              # Automation for running cocotb simulations and tests
│   ├── README.md             # Notes and instructions for the test suite
│   ├── requirements.txt      # Python dependencies for running tests
│   ├── tb.gtkw               # GTKWave configuration for waveform viewing
│   ├── tb.v                  # Verilog testbench top module for simulation
│   ├── test.py               # Main Python cocotb testbench for UART and Hamming modules
│   ├── test_receiver.py      # Python cocotb tests for UART receiver and Hamming decoder
│   └── test_transmitter.py   # Python cocotb tests for UART transmitter and Hamming encoder
├── docs/
│   ├── README.md               # Project documentation and design notes
│   └── DesignDocument.pdf       # Full design document (PDF)
├── README.md                 # This file
├── info.yaml                 # Project metadata
└── LICENSE                   # License information
```

## Quickstart

1. **Install dependencies:**

   - Python 3.8+
   - [cocotb](https://cocotb.org/)
   - Verilog simulator (e.g., Icarus Verilog)
   - See `test/requirements.txt` for Python packages.

2. **Run tests:**
   ```sh
   cd test
   make
   ```
   This will run all cocotb testbenches and report results.

## Main Features

- UART transmitter and receiver modules
- Hamming(7,4) error correction
- Comprehensive cocotb-based testbenches

## Documentation

- See the [project documentation](https://docs.google.com/document/d/1tlF-jqzEoZz30VtqMln9JiZ-5Pucy0jMslVNLtq-4XA/edit?usp=sharing) for detailed design and usage notes.
