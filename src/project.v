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
    input  wire       clk,      // Clock
    input  wire       rst_n     // Active-low reset
);

// Internal signals
  wire       tx;
  wire       tx_busy;
  wire       hamming_valid;
  wire       start_transmission = ui_in[4];
  wire [3:0] data_in            = ui_in[3:0];
  wire [6:0] hamming_code;
  wire [2:0] counter_out;

  reg        start_d;
  reg [6:0]  hamming_code_d;
  reg        hamming_valid_d;
  reg        hamming_valid_q;
  reg [7:0]  tx_data_reg;

  // Rising edge detector on start_transmission
  wire rising_edge = start_transmission & ~start_d;
  wire tx_start_pulse = hamming_valid & ~hamming_valid_q;
  wire [7:0] padded_data_delayed = {1'b0, hamming_code_d};

  always @(posedge clk) begin
    if (tx_start_pulse)
      $display("TX_START pulse generated with data 0x%h", tx_data_reg);
  end

  assign uo_out[0]   = tx;             // UART TX output
  assign uo_out[3:1] = counter_out;    // Counter output (for debugging)
  assign uo_out[7:4] = 4'b0000;        // Remaining bits set to 0

  assign uio_out     = 8'b0;           // Not driving any bidir pins
  assign uio_oe      = 8'b0;           // All bidir pins as inputs

  // Sample start_transmission for rising edge detect
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      start_d <= 1'b0;
    else
      start_d <= start_transmission;
  end

  // Register delayed Hamming output/valid, track previous valid for pulse
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      hamming_code_d   <= 7'b0;
      hamming_valid_d  <= 1'b0;
      hamming_valid_q  <= 1'b0;
    end else begin
      hamming_code_d   <= hamming_code;
      hamming_valid_d  <= hamming_valid;
      hamming_valid_q  <= hamming_valid;
    end
  end

  // Capture transmit data on tx_start pulse
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      tx_data_reg <= 8'b0;
    else if (tx_start_pulse)
      tx_data_reg <= padded_data_delayed;
  end

  // Instantiate Hamming (7,4) Encoder
  tt_um_hamming_encoder_74 encoder (
    .clk       (clk),
    .rst_n     (rst_n),
    .ena       (rising_edge),
    .data_in   (data_in),
    .code_out  (hamming_code),
    .valid_out (hamming_valid),
    .done      ()
  );

  // Instantiate UART Transmitter
  tt_um_uart_transmitter transmitter (
    .clk       (clk),
    .rst_n     (rst_n),
    .tx_start  (tx_start_pulse),
    .tx_data   (tx_data_reg),
    .tx        (tx),
    .tx_busy   (tx_busy),
    .done      ()
  );

  // Instantiate 3-bit Counter
  tt_um_counter_3b counter (
    .clk   (clk),
    .rst_n (rst_n),
    .ena   (1'b1),
    .count (counter_out),
    .done  ()
  );

endmodule