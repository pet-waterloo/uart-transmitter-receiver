`default_nettype none

// 3-bit counter module ~ 8 states
module tt_um_counter_3b (
    input  wire clk,      // clock
    input  wire rst_n,   // reset_n - low to reset
    input  wire ena,     // enable signal (active high)
    output reg [2:0] count, // 3-bit counter output
    output wire done
);

    assign done = (count == 3'b111);

    // Counter logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 3'b0; // Reset counter to 0
        end else if (ena) begin
            count <= count + 1; // Increment counter on each clock cycle
        end
    end

endmodule