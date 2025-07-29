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

  // ---------------------------- Receiver Signals ---------------------------- //
  wire [2:0] rx_counter_out;    // Output from counter, shows current bit position
  wire [3:0] decode_out;        // Decoded data bits from Hamming decoder
  wire [2:0] syndrome_out;      // Error syndrome from Hamming decoder
  wire valid_out;               // Valid signal from Hamming decoder

  // UART receiver wires
  wire [6:0] uart_data;         // 7-bit Hamming code from UART
  wire [1:0] uart_state;        // Current state of UART receiver
  wire uart_valid;              // Valid signal from UART
  
  wire hamming_ena;             // Enable signal for Hamming decoder

  // -------------------------- Transmitter Signals --------------------------- //
  wire       tx;                // UART TX output
  wire       tx_busy;           // TX busy signal
  wire       hamming_valid;     // Hamming encoder valid
  wire       start_transmission = ui_in[4];
  wire [3:0] data_in            = ui_in[3:0];
  wire [6:0] hamming_code;
  wire [2:0] tx_counter_out;    // Transmitter counter
  
  // Transmitter registers
  reg        start_d;
  reg [6:0]  hamming_code_d;
  reg        hamming_valid_d;
  reg        hamming_valid_q;
  reg [7:0]  tx_data_reg;

  // -------------------------------------------------------------------------- //
  // Connect output signals - CAREFULLY MAPPED TO AVOID CONFLICTS
  // Primary outputs
  assign uo_out[0] = tx;                 // TX pin - needed by transmitter test
  assign uo_out[4] = tx_busy;            // TX busy - needed by transmitter test
  assign uo_out[7] = valid_out;          // Decoder valid - needed by receiver test
  
  // Secondary outputs - decode data exposed on several pins for flexibility
  assign uo_out[1] = uart_valid;         // Receiver valid
  assign uo_out[2] = decode_out[0];      // Decoded data LSB
  assign uo_out[3] = decode_out[1];      // Decoded data bit 1
  assign uo_out[5] = decode_out[2];      // Decoded data bit 2
  assign uo_out[6] = decode_out[3];      // Decoded data MSB
  
  // Bidirectional pins - use as additional outputs
  assign uio_oe = 8'hFF;                 // All pins as outputs
  assign uio_out[2:0] = syndrome_out;    // Error syndrome 
  assign uio_out[5:3] = tx_counter_out;  // TX counter state
  assign uio_out[7:6] = uart_state;      // UART receiver state

  // -------------------------------------------------------------------------- //
  // Receiver logic
  
  // Enable Hamming decoder when UART has valid data
  assign hamming_ena = uart_valid && ena;

  // Debug/unused signal handling
  wire _unused = &{ui_in[7:5], uio_in, 1'b0};

  // Instantiate UART receiver
  tt_um_uart_receiver uart_rx (
    .clk(clk),
    .rst_n(rst_n),
    .ena(ena),
    .rx(ui_in[0]),              // UART input on first input bit
    .data_out(uart_data),       // 7-bit Hamming code output
    .state_out(uart_state),     // Current state of UART receiver
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
    .debug_syndrome_out(syndrome_out), // Connect syndrome for output display
    .debug_counter_out(rx_counter_out) // Connect counter for debugging
  );

  // -------------------------------------------------------------------------- //
  // Transmitter logic

  // Rising edge detector on start_transmission
  wire rising_edge = start_transmission & ~start_d;
  wire tx_start_pulse = hamming_valid & ~hamming_valid_q;
  wire [7:0] padded_data_delayed = {1'b0, hamming_code_d};

  // Debug display
  always @(posedge clk) begin
    if (tx_start_pulse)
      $display("TX_START pulse generated with data 0x%h", tx_data_reg);
  end

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
      hamming_valid_q  <= hamming_valid_d;
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
    .valid_out (hamming_valid)
  );

  // Instantiate UART Transmitter
  tt_um_uart_transmitter transmitter (
    .clk       (clk),
    .rst_n     (rst_n),
    .tx_start  (tx_start_pulse),
    .tx_data   (tx_data_reg),
    .tx        (tx),
    .tx_busy   (tx_busy)
  );

  // Instantiate 3-bit Counter
  tt_um_counter_3b counter (
    .clk   (clk),
    .rst_n (rst_n),
    .ena   (1'b1),
    .count (tx_counter_out),
    .done  ()
  );

endmodule