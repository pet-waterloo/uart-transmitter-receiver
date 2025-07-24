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
  // Internal signals
  wire       tx;
  wire       tx_busy;
  wire       hamming_valid;
  wire start_transmission = ui_in[4];

  wire [3:0] data_in = ui_in[3:0];
  wire [6:0] hamming_code;
  wire [7:0] padded_data;
  wire [2:0] counter_out;

  reg start_d;
  reg hamming_valid_d;
  wire rising_edge = start_transmission & ~start_d;
  assign padded_data = {1'b0, hamming_code}; // 0 extend MSB to 8 bits
  
  // Debug monitor
  always @(posedge clk) begin
    if (tx_start)
      $display("TX_START pulse generated with data 0x%h", padded_data);
  end

  // Output assignments
  assign uo_out[0] = tx;               // TX line output
  assign uio_out[2:0] = counter_out;   // Counter output (for debugging)
  assign uio_out[7:3] = 5'b00000;      // Remaining bits set to 0

  assign uio_oe  = 8'b0;

  always @(posedge clk or negedge rst_n) begin
      if (!rst_n)
          start_d <= 1'b0;
      else
          start_d <= start_transmission;
  end

  always @(posedge clk or negedge rst_n) begin
      if (!rst_n)
          hamming_valid_d <= 1'b0;
      else
          hamming_valid_d <= hamming_valid;
  end

  // stretch tx_start signal to ensure it's high for at least one clock cycle
  reg tx_start;
  always @(posedge clk or negedge rst_n) begin
      if (!rst_n)
          tx_start <= 1'b0;
      else if (hamming_valid)
          tx_start <= 1'b1;
      else if (tx_busy)
          tx_start <= 1'b0;
  end

  // Instantiate Hamming Encoder
  tt_um_hamming_encoder_74 encoder (
      .clk(clk),
      .rst_n(rst_n),
      .ena(rising_edge),
      .data_in(data_in),
      .code_out(hamming_code),
      .valid_out(hamming_valid)
  );

  // Instantiate UART Transmitter
  uart_transmitter transmitter (
      .clk(clk),
      .rst_n(rst_n),
      .tx_start(tx_start),
      .tx_data(padded_data),
      .tx(tx),
      .tx_busy(tx_busy)
  );

  // Instantiate 3-bit Counter
  tt_um_counter_3b counter (
      .clk(clk),
      .rst_n(rst_n),
      .ena(1'b1),
      .count(counter_out)
  );

endmodule