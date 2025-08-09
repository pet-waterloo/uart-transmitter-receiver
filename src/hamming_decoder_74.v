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

    // Wires for syndrome calculation and corrected bits
    wire [2:0] syndrome;
    reg [6:0] corrected_bits; // Use reg instead of wire for correction
    
    // Extract original bits
    wire c0_rx = decode_in[0];
    wire c1_rx = decode_in[1];
    wire d0_rx = decode_in[2];
    wire c2_rx = decode_in[3];
    wire d1_rx = decode_in[4];
    wire d2_rx = decode_in[5];
    wire d3_rx = decode_in[6];

    // -------------------------------------------------------------------------- //
    // Syndrome calculation
    assign syndrome = {
        c2_rx ^ d1_rx ^ d2_rx ^ d3_rx,  // syndrome[2]
        c1_rx ^ d0_rx ^ d2_rx ^ d3_rx,  // syndrome[1]
        c0_rx ^ d0_rx ^ d1_rx ^ d3_rx   // syndrome[0]
    };

    // Error correction logic
    always @(*) begin
        // Default: no correction
        corrected_bits = decode_in;
        
        case (syndrome)
            3'b001: corrected_bits[0] = ~decode_in[0]; // c0
            3'b010: corrected_bits[1] = ~decode_in[1]; // c1
            3'b011: corrected_bits[2] = ~decode_in[2]; // d0
            3'b100: corrected_bits[3] = ~decode_in[3]; // c2
            3'b101: corrected_bits[4] = ~decode_in[4]; // d1
            3'b110: corrected_bits[5] = ~decode_in[5]; // d2
            3'b111: corrected_bits[6] = ~decode_in[6]; // d3
            default: ; // No error, keep original
        endcase
    end

    // -------------------------------------------------------------------------- //
    // Main decoder logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset logic
            decode_buffer <= 7'b0000000;
            decode_out_reg <= 4'b0000;
            valid_out_reg <= 1'b0;
        end else if (ena) begin
            // Store corrected bits
            decode_buffer <= corrected_bits;
            
            // Extract corrected data bits
            decode_out_reg <= {
                corrected_bits[6], // d3
                corrected_bits[5], // d2
                corrected_bits[4], // d1
                corrected_bits[2]  // d0
            };
            
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