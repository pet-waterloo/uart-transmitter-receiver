/**
    * Hamming Decoder Module
    * This module implements a simple Hamming decoder.
    * It takes a single bit input and outputs a single bit.
*/


`default_nettype none

module tt_um_hamming_decoder_74 (
    input wire clk,
    input wire rst_n, // reset_n - low to reset
    input wire ena, // decides when to start "decoding"
    input wire decode_in,

    // 1 byte of output
    output wire valid_out, // indicates if the output is valid
    output wire [3:0] decode_out, // decoded output

    // debug information
    output wire [2:0] debug_syndrome_out, // syndrome bits for error detection
    output wire [2:0] debug_counter_out // current counter value for debugging

);
    
    // -------------------------------------------------------------------------- //
    // buffer and registers

    reg [6:0] input_buffer; // 7-bit buffer for Hamming code input

    reg [3:0] decode_out_reg; // 4-bit register for decoded output
    reg valid_out_reg; // register for valid output

    wire [2:0] syndrome; // Current syndrome bits, calculated from input buffer
    wire [2:0] counter; // Changed to wire since it's driven by counter3b

    // -------------------------------------------------------------------------- //
    // objects
    tt_um_counter_3b counter3b (
        .clk(clk),
        .rst_n(rst_n),
        .ena(ena),
        .count(counter) // Counter is now only driven by this module
    );

    // -------------------------------------------------------------------------- //
    // logic

    assign syndrome = {
        input_buffer[6] ^ input_buffer[4] ^ input_buffer[2] ^ input_buffer[0],
        input_buffer[5] ^ input_buffer[4] ^ input_buffer[1] ^ input_buffer[0],
        input_buffer[3] ^ input_buffer[2] ^ input_buffer[1] ^ input_buffer[0]
    };

    // every clock cycle...
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // reset logic
            input_buffer <= 7'b0000000;
            decode_out_reg <= 4'b0000;
            valid_out_reg <= 1'b0;
        end else if (ena) begin

            // Data collection logic
            if (counter == 3'b111) begin

                // Fix bits
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
            
                // Set decoded output from input buffer -- following designed bit format
                decode_out_reg[0] <= input_buffer[2];
                decode_out_reg[1] <= input_buffer[4];
                decode_out_reg[2] <= input_buffer[5];
                decode_out_reg[3] <= input_buffer[6];

                // Set output values
                valid_out_reg <= 1'b1;
            end else if (counter == 3'b001) begin
                // Only reset "valid" reg when we are on cycle 1
                valid_out_reg <= 1'b0;
            end else begin
                // Shift in new bits
                input_buffer[counter] <= decode_in;
            end
        end else begin
            valid_out_reg <= 1'b0;
        end
    end

    // -------------------------------------------------------------------------- //
    // Output assignments - these are fine
    assign valid_out = valid_out_reg;
    assign decode_out = decode_out_reg;
    assign debug_syndrome_out = syndrome;
    assign debug_counter_out = counter;

endmodule