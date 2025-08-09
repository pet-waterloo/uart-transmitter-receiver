/**
 * Hamming Decoder Module - Parallel Input Version
 * This module implements a Hamming(7,4) decoder with parallel input.
 * It takes 7 bits of input and outputs 4 decoded data bits.
 */

`default_nettype none

module tt_um_hamming_decoder_74 (
    input wire clk,
    input wire rst_n,         // reset_n - low to reset
    input wire ena,           // enable signal
    input wire [6:0] decode_in, // 7-bit parallel input from UART

    // Output signals
    output wire valid_out,       // indicates if the output is valid
    output wire [3:0] decode_out, // decoded 4-bit output

    // Debug information
    output wire [2:0] debug_syndrome_out, // syndrome bits for error detection
    output wire [2:0] debug_counter_out   // Not used in parallel version, kept for compatibility
);
    
    // -------------------------------------------------------------------------- //
    // Registers
    reg [6:0] decode_buffer;
    reg [3:0] decode_out_reg; // 4-bit register for decoded output
    reg valid_out_reg;        // Register for valid output signal

    // Wire for syndrome calculation
    wire [2:0] syndrome;
    wire c0_rx;
    wire c1_rx;
    wire d0_rx;
    wire c2_rx;
    wire d1_rx;
    wire d2_rx;
    wire d3_rx;

    // -------------------------------------------------------------------------- //
    // Syndrome calculation (same as before)

    assign c0_rx = decode_in[0];
    assign c1_rx = decode_in[1];
    assign d0_rx = decode_in[2];
    assign c2_rx = decode_in[3];
    assign d1_rx = decode_in[4];
    assign d2_rx = decode_in[5];
    assign d3_rx = decode_in[6];

    assign syndrome = {
        c0_rx ^ d0_rx ^ d1_rx ^ d3_rx,
        c1_rx ^ d0_rx ^ d2_rx ^ d3_rx,
        c2_rx ^ d1_rx ^ d2_rx ^ d3_rx
    };

    // use a mux to negate the appropriate bits based on the syndrome
    always @(*) begin
        case (syndrome)
            3'b001: c0_rx = ~c0_rx; // c0
            3'b010: c1_rx = ~c1_rx; // c1
            3'b011: d0_rx = ~d0_rx; // d0
            3'b100: c2_rx = ~c2_rx; // c2
            3'b101: d1_rx = ~d1_rx; // d1
            3'b110: d2_rx = ~d2_rx; // d2
            3'b111: d3_rx = ~d3_rx; // d3
            default: ;
        endcase
    end

    // extract data bits as well
    assign decode_out[3:0] = {
        d3_rx,
        d2_rx,
        d1_rx,
        d0_rx
    };

    // -------------------------------------------------------------------------- //
    // Main decoder logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset logic
            input_buffer <= 7'b0000000;
            decode_out_reg <= 4'b0000;
            valid_out_reg <= 1'b0;
        end else if (ena) begin
            // Set valid output flag
            valid_out_reg <= 1'b1;
        end else begin
            valid_out_reg <= 1'b0;
        end
    end

    // -------------------------------------------------------------------------- //
    // Output assignments
    assign valid_out = valid_out_reg;
    assign decode_out = decode_out_reg;
    assign debug_syndrome_out = syndrome;
    assign debug_counter_out = 3'b000; // Not used in parallel version

endmodule