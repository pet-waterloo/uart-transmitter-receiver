`default_nettype none
`timescale 1ns / 1ps

/* This testbench tests the hamming encoder module separately */

module tt_um_hamming_encoder_tb ();
  initial begin
    $dumpfile("hamming_encoder_test.vcd");
    $dumpvars(0, tt_um_hamming_encoder_tb);
    #1;
  end

  reg clk;VERILOG_SOURCES += $(SRC_DIR)/hamming_encoder.v
  reg rst_n;
  reg ena;
  reg [3:0] data_in;
  wire [6:0] code_out;
  wire valid_out;
  wire [7:0] uio_oe;

  tt_um_hamming_encoder_7_4 encoder (
      .clk     (clk),
      .rst_n   (rst_n),
      .ena     (ena),
      .data_in (data_in),
      .code_out(code_out),
      .valid_out(valid_out)
  );

endmodule