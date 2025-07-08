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
    reg [6:0] input_buffer;   // Buffer to store and correct input
    reg [3:0] decode_out_reg; // 4-bit register for decoded output
    reg valid_out_reg;        // Register for valid output signal

    // Wire for syndrome calculation
    wire [2:0] syndrome;

    // -------------------------------------------------------------------------- //
    // Syndrome calculation (same as before)
    assign syndrome = {
        input_buffer[6] ^ input_buffer[4] ^ input_buffer[2] ^ input_buffer[0],
        input_buffer[5] ^ input_buffer[4] ^ input_buffer[1] ^ input_buffer[0],
        input_buffer[3] ^ input_buffer[2] ^ input_buffer[1] ^ input_buffer[0]
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
            // Load input data
            input_buffer <= decode_in;
            
            // Correct errors if needed
            if (syndrome != 3'b000) begin
                // Error detected, attempt to correct
                case (syndrome)
                    3'b001: input_buffer[0] <= ~input_buffer[0]; // c0
                    3'b010: input_buffer[1] <= ~input_buffer[1]; // c1
                    3'b011: input_buffer[2] <= ~input_buffer[2]; // d0
                    3'b100: input_buffer[3] <= ~input_buffer[3]; // c2
                    3'b101: input_buffer[4] <= ~input_buffer[4]; // d1
                    3'b110: input_buffer[5] <= ~input_buffer[5]; // d2
                    3'b111: input_buffer[6] <= ~input_buffer[6]; // d3
                    default: ; // No action for other syndromes
                endcase
            end
            
            // Extract the data bits
            decode_out_reg[0] <= input_buffer[2]; // d0
            decode_out_reg[1] <= input_buffer[4]; // d1
            decode_out_reg[2] <= input_buffer[5]; // d2
            decode_out_reg[3] <= input_buffer[6]; // d3
            
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