
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
    input wire decode_in,

    output wire valid_out,
    output wire[3:0] decode_out
);

    // -------------------------------------------- //
    // counter bits
    wire [2:0] c;
    tt_um_counter_3b counter (
        .clk(clk),
        .rst_n(rst_n),
        .ena(ena),
        .count(c[2:0])
    );

    // -------------------------------------------- //
    // input register -- buffers 7 bits of input
    reg [6:0] decode_in_reg;
    reg stream_in_reg;

    assign stream_in_reg = decode_in;

    // -------------------------------------------- //
    // output register -- buffers 4 bits of output
    reg [3:0] decode_out_reg;
    reg valid_out_reg;

    assign valid_out = valid_out_reg;
    assign decode_out = decode_out_reg;

    // -------------------------------------------- //
    // logic for decoding -- check if enabled
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            decode_in_reg <= 0;
            decode_out_reg <= 0;
            valid_out_reg <= 0;
        end else if (ena) begin
            // collect 7 bits -- assume synced system
            //          bits pushed to left (new data into right // LSB)
            decode_in_reg <= {decode_in_reg[1:6], stream_in_reg};
            
            // Check if we have enough bits to decode
            if (c == 3'b111) begin
                // decoding logic


                // finished
                valid_out_reg <= 1; // Set valid output

            end else if (c == 3'b000) begin
                // Reset the output when we have no bits to decode
                decode_out_reg <= 0;
                valid_out_reg <= 0; // Clear valid output
            end

            
        end else begin
            // If not enabled, keep the previous state
            valid_out_reg <= 0; // Clear valid output
        end
    end

    // -------------------------------------------- //

endmodule