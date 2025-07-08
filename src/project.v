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

  // Internal wires
  wire [2:0] counter_out;
  wire [3:0] decode_out;
  wire [2:0] syndrome_out; // Not used, but declared for completeness
  wire valid_out;

  // Connect output signals
  assign uo_out[3:0] = decode_out;  // Lower 4 bits from decoder
  assign uo_out[6:4] = syndrome_out;        // Middle 3 bits set to 0
  assign uo_out[7] = valid_out;     // MSB from decoder valid signal
  
  // Connect uio_out signals
  assign uio_oe[7:0] = 8'b11111111; // All uio_oe bits to 1 (output enabled)
  assign uio_out[2:0] = counter_out; // Lower 3 bits from counter
  assign uio_out[7:3] = 5'b0;        // Upper 5 bits set to 0
  assign uio_oe  = 8'b0;              // All uio_oe bits to 0

  // Instantiate 3-bit counter
  tt_um_counter_3b counter (
      .clk(clk),
      .rst_n(rst_n),
      .ena(ena),
      .count(counter_out)
  );

  // Instantiate Hamming decoder
  tt_um_hamming_decoder_74 decoder74 (
    .clk(clk),
    .rst_n(rst_n),
    .ena(ena),
    .decode_in(ui_in[0]),      // Use the first bit of ui_in as input for decoding
    .valid_out(valid_out),     // Use internal wire for valid output
    .decode_out(decode_out),    // Use internal wire for decoded output

    // debug
    .debug_syndrome_out(syndrome_out), // Not used, but declared for completeness
    .debug_counter_out(counter_out) // Use counter_out for debugging
  );

  // List all unused inputs to prevent warnings
  // Not using ui_in[7:1] and all of uio_in
  wire _unused = &{ui_in[7:1], uio_in, counter_out, 1'b0};

endmodule
