`default_nettype none

// 8-bit counter module ~ 256 states
module tt_um_counter_8b (
    input  wire clk,      // clock
    input  wire rst_n,   // reset_n - low to reset
    input  wire ena,     // enable signal (active high)
    output reg [7:0] count // 8-bit counter output
);

    // Counter logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 8'b0; // Reset counter to 0
        end else if (ena) begin
            count <= count + 1; // Increment counter on each clock cycle
        end
    end

endmodule