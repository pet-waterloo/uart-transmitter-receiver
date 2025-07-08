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

  reg [2:0] oversampling_counter; // Oversampling counter for UART receiver -- count of 8
  wire hamming_ena;         // Enable signal for Hamming decoder

  // -------------------------------------------------------------------------- //
  // Connect output signals
  assign uo_out[7] = valid_out;         // MSB from decoder valid signal
  assign uo_out[6:4] = syndrome_out;    // Middle 3 bits show syndrome value
  assign uo_out[3:0] = decode_out;      // Lower 4 bits show decoded data

  assign uio_oe[7:0] = 8'b11111111;     // All uio pins configured as outputs

  assign uio_out[7:6] = 2'b0;               // Upper 2 bits set to 0
  assign uio_out[5:3] = oversampling_counter;  // Middle 3 bits show oversampling counter value
  assign uio_out[2:0] = counter_out;        // Lower 3 bits show bit counter value

  // -------------------------------------------------------------------------- //
  // create objects

  /*
   * Implementation Notes:
   * - Currently only implementing the Hamming(7,4) decoder
   *   - 3 bit clock for oversampling counter
   * - Future additions could include:
   *   - statemachine (4 states)
   *   - simple 2-4 decoder
   *   - uart receiver (8N1)
   */

  // Instantiate 3-bit counter for oversampling
  tt_um_counter_3b counter3b (
    .clk(clk),
    .rst_n(rst_n),
    .ena(ena),                     // Enable signal for counter
    .count(oversampling_counter)   // Connect counter output to counter_out wire
  );

  // Instantiate Hamming decoder
  tt_um_hamming_decoder_74 decoder74 (
    .clk(clk),
    .rst_n(rst_n),
    .ena(hamming_ena),        // Enable signal for Hamming decoder
    .decode_in(ui_in[0]),             // Use bit 0 of ui_in as serial input
    .valid_out(valid_out),            // Connect to valid_out wire
    .decode_out(decode_out),          // Connect to decode_out wire
    
    // Debug connections
    .debug_syndrome_out(syndrome_out), // Connect syndrome for output display
    .debug_counter_out(counter_out)    // Connect counter for debugging
  );

  // -------------------------------------------------------------------------- //
  // logic

  // Enable signal for Hamming decoder -- when oversampling_counter = 7 and ena is enabled
  assign hamming_ena = (oversampling_counter == 3'b111) && ena;
  
  // -------------------------------------------------------------------------- //
  // List all unused inputs to prevent warnings
  wire _unused = &{ui_in[7:1], uio_in, 1'b0};

endmodule
