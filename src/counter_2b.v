`default_nettype none

// 2-bit counter module ~ 4 states
module tt_um_counter_2b (
    input  wire clk,      // clock
    input  wire rst_n,   // reset_n - low to reset
    input  wire ena,     // enable signal (active high)
    output reg [1:0] count // 3-bit counter output
);

    // Counter logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 2'b0; // Reset counter to 0
        end else if (ena) begin
            count <= count + 1; // Increment counter on each clock cycle
        end
    end

endmodule