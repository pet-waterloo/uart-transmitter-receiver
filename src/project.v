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

  // -------------------------------------------------------------------------- //
  // Internal wires
  wire [2:0] counter_out;      // Output from counter, shows current bit position
  wire [3:0] decode_out;       // Decoded data bits from Hamming decoder
  wire [2:0] syndrome_out;     // Error syndrome from Hamming decoder
  wire valid_out;              // Valid signal from Hamming decoder

  // UART receiver wires
  wire [6:0] uart_data;        // 7-bit Hamming code from UART
  wire [1:0] uart_state;       // Current state of UART receiver
  wire uart_valid;             // Valid signal from UART
  
  wire hamming_ena;            // Enable signal for Hamming decoder

  reg [3:0] uo_out_4b;

  // -------------------------------------------------------------------------- //
  // Connect output signals
  assign uo_out[7] = valid_out;         // MSB from decoder valid signal
  assign uo_out[6:4] = syndrome_out;    // Middle 3 bits show syndrome value
  // assign uo_out[3:0] = decode_out;      // Lower 4 bits show decoded data
  assign uo_out[3:0] = uo_out_4b; // Lower 4 bits show decoded data

  // DEBUGGING
  assign uio_oe[7:0] = 8'b11111111;     // All uio pins configured as outputs

  assign uio_out[7] = uart_valid;       // Show UART valid signal
  assign uio_out[6:0] = uart_data;      // Show received Hamming code

  // -------------------------------------------------------------------------- //
  // logic

  // Enable Hamming decoder when UART has valid data
  assign hamming_ena = uart_valid && ena;

  // -------------------------------------------------------------------------- //
  // List all unused inputs to prevent warnings
  wire _unused = &{ui_in[7:1], uio_in, 1'b0};

  // -------------------------------------------------------------------------- //
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

    // Output connections
    .valid_out(valid_out),      // Connect to valid_out wire
    .decode_out(decode_out),    // Connect to decode_out wire
    
    // Debug connections
    .debug_syndrome_out(syndrome_out), // Connect syndrome for output display
    .debug_counter_out(counter_out)    // Connect counter for debugging
  );

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      // Reset logic for internal state
      uo_out_4b <= 4'b0000; // Reset output to 0
    end else if (ena) begin
      // if not hamming_ena
      if (!hamming_ena) begin
        // drive state information
        uo_out_4b[1:0] <= uart_state; // Show UART state (2 bits)
        uo_out_4b[3:2] <= 2'b00; // Unused bits, set to 0
      end else begin
        // drive decode information
        uo_out_4b[3:0] <= decode_out; // Lower 4 bits show decoded data
      end
    end
  end
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
  assign uo_out[4]   = tx_busy;        // Transmitter busy flag
  assign uo_out[7:5] = 3'b000;        // Remaining bits set to 0

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
    .count (counter_out),
    .done  ()
  );

endmodule