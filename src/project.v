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
  wire [3:0] data_in = ui_in[3:0];
  wire [6:0] hamming_code;
  wire [7:0] padded_data_delayed;
  wire [2:0] counter_out;

  reg        start_d;
  reg [6:0]  hamming_code_d;
  reg        hamming_valid_d;
  reg [7:0]  tx_data_reg;
  reg        tx_start;

  // Rising edge detector on start_transmission
  wire rising_edge = start_transmission & ~start_d;

  // Debug monitor
  always @(posedge clk) begin
    if (tx_start)
      $display("TX_START pulse generated with data 0x%h", tx_data_reg);
  end

  // Assign TX line and debug counter to outputs
  assign uo_out[0]     = tx;               // UART TX output
  assign uio_out[2:0]  = counter_out;      // Debug counter
  assign uio_out[7:3]  = 5'b00000;         // Unused outputs
  assign uio_oe        = 8'b0;             // All UIO pins are inputs

  // Sample start transmission for edge detection
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      start_d <= 1'b0;
    else
      start_d <= start_transmission;
  end

  // Register delayed Hamming output and valid flag
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      hamming_code_d  <= 7'b0;
      hamming_valid_d <= 1'b0;
    end else begin
      hamming_code_d  <= hamming_code;
      hamming_valid_d <= hamming_valid;
    end
  end

  // Build 8-bit padded Hamming output from delayed code
  assign padded_data_delayed = {1'b0, hamming_code_d};

  // Stretch tx_start signal to ensure a full clock-wide pulse
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      tx_start <= 1'b0;
    else if (hamming_valid_d)
      tx_start <= 1'b1;
    else if (tx_busy)
      tx_start <= 1'b0;
  end

  // Capture transmit data aligned with valid Hamming output
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      tx_data_reg <= 8'b0;
    else if (hamming_valid_d)
      tx_data_reg <= padded_data_delayed;
  end

  // Instantiate Hamming (7,4) Encoder
  tt_um_hamming_encoder_74 encoder (
    .clk       (clk),
    .rst_n     (rst_n),
    .ena       (rising_edge),
    .data_in   (data_in),
    .code_out  (hamming_code),
    .valid_out (hamming_valid)
  );

  // Instantiate UART Transmitter
  uart_transmitter transmitter (
    .clk       (clk),
    .rst_n     (rst_n),
    .tx_start  (tx_start),
    .tx_data   (tx_data_reg),
    .tx        (tx),
    .tx_busy   (tx_busy)
  );

  // Instantiate 3-bit Debug Counter
  tt_um_counter_3b counter (
    .clk   (clk),
    .rst_n (rst_n),
    .ena   (1'b1),
    .count (counter_out)
  );

endmodule