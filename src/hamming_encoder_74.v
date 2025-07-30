`default_nettype none

module tt_um_hamming_encoder_74 (
    input wire clk,
    input wire rst_n,
    input wire ena,
    input wire [3:0] data_in,
    output reg [6:0] code_out,
    output reg valid_out
);
    // parity bits output
    reg p1, p2, p3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            code_out <= 7'b0;
            valid_out <= 1'b0;
        end else if (ena) begin
            // calculate 3 parity bits for hamming code 7,4
            p1 = data_in[0] ^ data_in[1] ^ data_in[3];
            p2 = data_in[0] ^ data_in[2] ^ data_in[3];
            p3 = data_in[1] ^ data_in[2] ^ data_in[3];

            code_out <= {p1, p2, data_in[0], p3, data_in[1], data_in[2], data_in[3]};
            valid_out <= 1'b1;
            
            // Debug information
            $display("Hamming Encoder: Input=0x%h, Encoding to code=0x%h (p1=%b, p2=%b, p3=%b)",
                     data_in, 
                     {p1, p2, data_in[0], p3, data_in[1], data_in[2], data_in[3]},
                     p1, p2, p3);
        end else begin
            valid_out <= 1'b0;
        end
    end
endmodule