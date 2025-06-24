/**
 * Hamming Encoder Module
 * Encodes 4 data bits into 7 bits using Hamming(7,4) code.
 */

`default_nettype none

module hamming_encoder_7_4 (
    input wire clk,
    input wire rst_n,
    input wire ena,                                     // enable encoding
    input wire [3:0] data_in,                           // 4-bit data input
    output wire [6:0] code_out,                         // 7-bit encoded output
    output wire valid_out                               // output valid flag
);
    reg[2:0] parity_bits;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            code_out <= 7'b0;                           // Reset output to 0
            valid_out <= 1'b0;                          // Reset valid flag
        end else if (ena) begin
            parity_bits[0] <= data_in[0] ^ data_in[1] ^ data_in[3]; // P1
            parity_bits[1] <= data_in[0] ^ data_in[2] ^ data_in[3]; // P2
            parity_bits[2] <= data_in[1] ^ data_in[2] ^ data_in[3]; // P3
        
            code_out <= {
                data_in[3],
                data_in[2],
                data_in[1],
                parity_bits[2],
                data_in[0],
                parity_bits[1],     
                parity_bits[0]
            };
            valid_out <= 1'b1;                          // Set valid flag to indicate output is ready
        end else begin
            valid_out <= 1'b0;                          // Clear valid flag if not enabled        
        end
    end

endmodule
