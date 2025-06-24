
/**
    * Hamming Decoder Module
    * This module implements a simple Hamming decoder.
    * It takes a single bit input and outputs a single bit.
*/


`default_nettype none


module tt_um_hamming_decoder_74 (
    // 1 wire input
    // 4 wire output

    input wire clk,
    input wire rst_n, // reset_n - low to reset
    input wire ena, // decides when to start "decoding"

    // single line of input
    input wire decode_in,

    // 1 byte of output
    output reg valid_out, // indicates if the output is valid
    output reg [3:0] decode_out // decoded output
);
    

    // -------------------------------------------- //
    // memory locations

    // counter for input tracking
    reg [6:0] input_buffer; // 7-bit buffer for Hamming code input
    reg [2:0] syndrome;

    reg [2:0] counter;


    // -------------------------------------------- //
    // objects
    tt_um_counter_3b counter3b (
        .clk(clk),
        .rst_n(rst_n),
        .ena(ena),
        .count(counter) // Use lower 3 bits for counter output
    );

    // -------------------------------------------- //
    // logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // reset logic
            decode_out <= 0;
            valid_out <= 0;
        end else if (ena) begin
            // if component is ENABLED

            // if 4 bits finished
            if (counter == 3'b111) begin
                // reset counter
                counter <= 0;
                
                // use syndrome bits to check
                syndrome = {
                    input_buffer[6] ^ input_buffer[4] ^ input_buffer[2] ^ input_buffer[0], // S1
                    input_buffer[5] ^ input_buffer[4] ^ input_buffer[1] ^ input_buffer[0], // S2
                    input_buffer[3] ^ input_buffer[2] ^ input_buffer[1] ^ input_buffer[0]  // S3
                };

                if (syndrome == 3'b000) begin
                    // no error detected, do nothing
                end else begin
                    // error detected, flip the bit at syndrome position
                    input_buffer[syndrome] <= ~input_buffer[syndrome]; // flip the bit at syndrome position
                end

                // decode the input
                decode_out[0] <= input_buffer[0];
                decode_out[1] <= input_buffer[1];
                decode_out[2] <= input_buffer[2];
                decode_out[3] <= input_buffer[4];

                // set valid output
                valid_out <= 1;

            end else begin
                // set counter index to be received value
                input_buffer[counter] <= decode_in;
            end
            
        end else begin
            valid_out <= 0;
        end
    end

    // -------------------------------------------- //

endmodule