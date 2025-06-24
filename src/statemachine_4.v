`default_nettype none

// 3-bit counter module ~ 8 states
module tt_um_statemachine_4 (
    input  wire clk,      // clock
    input  wire rst_n,   // reset_n - low to reset
    input  wire ena,     // enable signal (active high)
    output reg [1:0] count // 2-bit counter output
);

    // Counter logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 2'b0; // Reset counter to 0
        end else if (ena) begin
            count <= count + 1; // Increment counter on enable
        end
    end

endmodule