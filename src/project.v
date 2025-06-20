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

  wire [2:0] counter_out;

  // All output pins must be assigned. If not used, assign to 0.
  // REMOVED: assign uo_out  = ui_in + uio_in;  // This conflicts with line 24
  assign uo_out[2:0] = counter_out; // Counter output on lower 3 bits
  assign uo_out[7:3] = 5'b0;        // Upper 5 bits set to 0
  assign uio_out = 8'b0;            // All uio_out bits to 0
  assign uio_oe  = 8'b0;            // All uio_oe bits to 0

  tt_um_counter_3b counter (
      .clk(clk),
      .rst_n(rst_n),
      .ena(ena),
      .count(counter_out)
  );

  // List all unused inputs to prevent warnings
  wire _unused = &{ui_in, uio_in, ena, 1'b0};

endmodule
