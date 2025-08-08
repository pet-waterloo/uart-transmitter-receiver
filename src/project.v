/*
 * UART Transmitter & Receiver Top Module
 * Implements UART RX/TX with Hamming(7,4) error correction.
 * Copyright (c) 2024 Your Name
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module tt_um_ultrasword_jonz9 (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs

    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Output enable (1=output)

    input  wire       ena,      // Always 1 when powered
    input  wire       clk,      // Clock
    input  wire       rst_n     // Active-low reset
);

  // ------------------- Receiver Signals -------------------
  wire [2:0] rx_counter_out;    // Bit position from counter
  wire [3:0] rx_decode_out;     // Decoded data from Hamming decoder
  wire [2:0] rx_syndrome_out;   // Error syndrome from Hamming decoder
  wire       rx_valid_out;      // Valid signal from Hamming decoder

  // UART receiver wires
  wire [6:0] rx_uart_data;      // 7-bit Hamming code from UART
  wire [1:0] rx_uart_state;     // UART receiver state
  wire       rx_uart_valid;     // UART receiver valid
  wire       rx_hamming_ena;    // Enable for Hamming decoder

  // ------------------- Transmitter Signals ----------------
  wire       tx;                // UART TX output
  wire       tx_busy;           // TX busy signal
  wire       tx_hamming_valid;  // Hamming encoder valid
  wire       tx_start_transmission = ui_in[4];
  wire [3:0] tx_data_in         = ui_in[3:0];
  wire [6:0] tx_hamming_code;
  wire [2:0] tx_counter_out;    // TX counter

  // Transmitter registers
  reg        tx_start_d;
  reg [6:0]  tx_hamming_code_d;
  reg        tx_hamming_valid_d;
  reg        tx_hamming_valid_q;
  reg [7:0]  tx_data_reg;

  // ------------------- Outputs ----------------------------
  assign uo_out[4] = tx_busy;               // TX busy
  assign uo_out[0] = tx;                    // TX pin

  assign uo_out[7] = rx_valid_out;          // Decoder valid
  assign uo_out[6] = rx_decode_out[3];      // Decoded data MSB
  assign uo_out[5] = rx_decode_out[2];      // Decoded data bit 2

  assign uo_out[3] = rx_decode_out[1];      // Decoded data bit 1
  assign uo_out[2] = rx_decode_out[0];      // Decoded data LSB
  assign uo_out[1] = rx_uart_valid;         // Receiver valid

  assign uio_oe = 8'hFF;                    // All IOs as outputs
  assign uio_out[2:0] = rx_syndrome_out;    // Error syndrome
  assign uio_out[5:3] = tx_counter_out;     // TX counter state
  assign uio_out[7:6] = rx_uart_state;      // UART receiver state

  // ------------------- Receiver Logic ---------------------
  assign rx_hamming_ena = rx_uart_valid && ena; // Enable decoder when UART valid
  wire _unused = &{ui_in[7:5], uio_in, 1'b0}; // Unused inputs

  // UART receiver instance
  tt_um_uart_receiver uart_rx (
    .clk(clk),
    .rst_n(rst_n),
    .ena(ena),
    .rx(ui_in[0]),              // UART RX input
    .data_out(rx_uart_data),    // 7-bit Hamming code
    .state_out(rx_uart_state),  // UART state
    .valid_out(rx_uart_valid)   // Valid when frame received
  );

  // Hamming decoder instance
  tt_um_hamming_decoder_74 decoder74 (
    .clk(clk),
    .rst_n(rst_n),
    .ena(rx_hamming_ena),              // Enable on UART valid
    .decode_in(rx_uart_data),          // UART data
    .valid_out(rx_valid_out),          // Decoder valid
    .decode_out(rx_decode_out),        // Decoded data
    .debug_syndrome_out(rx_syndrome_out),   // Syndrome output
    .debug_counter_out(rx_counter_out)      // Counter output
  );

  // ------------------- Transmitter Logic ------------------
  // Rising edge detector for tx_start_transmission
  wire tx_rising_edge = tx_start_transmission & ~tx_start_d;
  wire tx_start_pulse = tx_hamming_valid & ~tx_hamming_valid_q;
  wire [7:0] tx_padded_data_delayed = {1'b0, tx_hamming_code_d};

  always @(posedge clk) begin
    if (tx_start_pulse)
      $display("TX_START pulse generated with data 0x%h", tx_data_reg);
  end

  // Sample tx_start_transmission for edge detect
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      tx_start_d <= 1'b0;
    else
      tx_start_d <= tx_start_transmission;
  end

  // Register delayed Hamming output/valid, track previous valid for pulse
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      tx_hamming_code_d   <= 7'b0;
      tx_hamming_valid_d  <= 1'b0;
      tx_hamming_valid_q  <= 1'b0;
    end else begin
      tx_hamming_code_d   <= tx_hamming_code;
      tx_hamming_valid_d  <= tx_hamming_valid;
      tx_hamming_valid_q  <= tx_hamming_valid_d;
    end
  end

  // Capture transmit data on tx_start pulse
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      tx_data_reg <= 8'b0;
    else if (tx_start_pulse)
      tx_data_reg <= tx_padded_data_delayed;
  end

  // Hamming (7,4) Encoder instance
  tt_um_hamming_encoder_74 encoder (
    .clk       (clk),
    .rst_n     (rst_n),
    .ena       (tx_rising_edge),
    .data_in   (tx_data_in),
    .code_out  (tx_hamming_code),
    .valid_out (tx_hamming_valid)
  );

  // UART Transmitter instance
  tt_um_uart_transmitter transmitter (
    .clk       (clk),
    .rst_n     (rst_n),
    .tx_start  (tx_start_pulse),
    .tx_data   (tx_data_reg),
    .tx        (tx),
    .tx_busy   (tx_busy)
  );

  // 3-bit Counter instance
  tt_um_counter_3b counter (
    .clk   (clk),
    .rst_n (rst_n),
    .ena   (1'b1),
    .count (tx_counter_out),
    .done  ()
  );

endmodule