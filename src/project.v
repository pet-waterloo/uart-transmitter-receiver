/*
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_ultrasword_jonz9 (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs

    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)

    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // -------------------------------------------------------------------------- //
  // Internal wires
  wire [2:0] counter_out;      // Output from counter, shows current bit position
  wire [3:0] decode_out;       // Decoded data bits from Hamming decoder
  wire [2:0] syndrome_out;     // Error syndrome from Hamming decoder
  wire valid_out;              // Valid signal from Hamming decoder

  // UART receiver wires
  wire [6:0] uart_data;        // 7-bit Hamming code from UART
  wire [2:0] uart_state;       // Current state of the UART receiver
  wire uart_valid;             // Valid signal from UART
  
  wire hamming_ena;            // Enable signal for Hamming decoder

  // -------------------------------------------------------------------------- //
  // Connect output signals
  assign uo_out[7] = valid_out;         // MSB from decoder valid signal
  assign uo_out[6:4] = syndrome_out;    // Middle 3 bits show syndrome value
  // assign uo_out[3:0] = decode_out;      // Lower 4 bits show decoded data
  assign uo_out[3] = 1'b0;
  assign uo_out[2:0] = uart_state;      // Lower 3 bits show UART state

  // DEBUGGING
  assign uio_oe[7:0] = 8'b11111111;     // All uio pins configured as outputs

  assign uio_out[7] = uart_valid;       // Show UART valid signal
  assign uio_out[6:0] = uart_data;      // Show received Hamming code

  // -------------------------------------------------------------------------- //
  // Instantiate UART receiver
  tt_um_uart_receiver uart_rx (
    .clk(clk),
    .rst_n(rst_n),
    .ena(ena),
    .rx(ui_in[0]),              // UART input on first input bit

    // Output signals
    .data_out(uart_data),       // 7-bit Hamming code output
    .state_out(uart_state),     // Current state of the UART receiver
    .valid_out(uart_valid)      // Valid signal when full frame received
  );

  // Instantiate Hamming decoder
  tt_um_hamming_decoder_74 decoder74 (
    .clk(clk),
    .rst_n(rst_n),
    .ena(hamming_ena),          // Enable when UART has valid data
    .decode_in(uart_data),      // Connect to UART data output
    .valid_out(valid_out),      // Connect to valid_out wire
    .decode_out(decode_out),    // Connect to decode_out wire
    
    // Debug connections
    .debug_syndrome_out(syndrome_out), // Connect syndrome for output display
    .debug_counter_out(counter_out)    // Connect counter for debugging
  );

  // -------------------------------------------------------------------------- //
  // logic

  // Enable Hamming decoder when UART has valid data
  assign hamming_ena = uart_valid && ena;
  
  // -------------------------------------------------------------------------- //
  // List all unused inputs to prevent warnings
  wire _unused = &{ui_in[7:1], uio_in, 1'b0};

endmodule
