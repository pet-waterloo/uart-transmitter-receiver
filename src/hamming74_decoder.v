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
    output wire [2:0] syndrome_out // syndrome bits for error detection
);
    
    // -------------------------------------------- //
    // memory locations

    // buffer and registers
    reg [6:0] input_buffer; // 7-bit buffer for Hamming code input
    reg [2:0] syndrome;
    
    reg [3:0] decode_out_reg; // 4-bit register for decoded output
    reg valid_out_reg; // register for valid output

    wire [2:0] counter; // Changed to wire since it's driven by counter3b

    // -------------------------------------------- //
    // objects
    tt_um_counter_3b counter3b (
        .clk(clk),
        .rst_n(rst_n),
        .ena(ena),
        .count(counter) // Counter is now only driven by this module
    );

    // -------------------------------------------- //
    // logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // reset logic
            input_buffer <= 7'b0000000; // Reset input buffer
            syndrome <= 3'b000; // Reset syndrome
            decode_out_reg <= 4'b0000; // reset output to 0
            valid_out_reg <= 1'b0;
        end else if (ena) begin
            // if component is ENABLED

            // if 7 bits finished
            if (counter == 3'b111) begin
                // REMOVED: counter <= 0; - Don't reset counter here, let the counter3b handle it
                
                // use syndrome bits to check
                syndrome <= {
                    input_buffer[6] ^ input_buffer[4] ^ input_buffer[2] ^ input_buffer[0], // S1
                    input_buffer[5] ^ input_buffer[4] ^ input_buffer[1] ^ input_buffer[0], // S2
                    input_buffer[3] ^ input_buffer[2] ^ input_buffer[1] ^ input_buffer[0]  // S3
                };

                // Temporarily store syndrome-corrected buffer
                if (syndrome == 3'b000) begin
                    // no error detected, use buffer as-is
                end else begin
                    // error detected, correct the bit at syndrome position
                    input_buffer[syndrome] <= ~input_buffer[syndrome];
                end

                // decode the input
                decode_out_reg[0] <= input_buffer[3];
                decode_out_reg[1] <= input_buffer[5];
                decode_out_reg[2] <= input_buffer[6];
                decode_out_reg[3] <= input_buffer[7];

                // set valid output
                valid_out_reg <= 1'b1;
            end else begin
                // set counter index to be received value
                input_buffer[counter] <= decode_in;
                valid_out_reg <= 1'b0;
            end
        end else begin
            valid_out_reg <= 1'b0;
        end
    end

    // Output assignments
    assign valid_out = valid_out_reg;
    assign decode_out = decode_out_reg;
    assign syndrome_out = syndrome;

endmodule