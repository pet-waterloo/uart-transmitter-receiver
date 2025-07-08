`default_nettype none

module tt_um_uart_receiver (
    input  wire clk,      // clock
    input  wire rst_n,   // reset_n - low to reset
    input  wire ena,     // enable signal (active high)
    input  wire rx,      // UART receive line
    output reg [7:0] data_out, // Received data output
    output reg valid_out // Indicates if the received data is valid
);

    // State encoding
    localparam [1:0] IDLE     = 2'b00,
                     DECODE   = 2'b01,
                     VALIDATE = 2'b10,
                     DONE     = 2'b11;

    wire state_ena; // Enable signal for state machine

    reg [1:0] state; // Current state of the receiver
    reg [3:0] baud_rate; // oversample rate ~ 0-15 ticks

    // -------------------------------------------------------------------------- //
    // State counter for UART receiver

    tt_um_counter2b counter2b (
        .clk(clk),
        .rst_n(rst_n),
        .ena(state_ena),
        .count(state) // Use state as the counter output
    );

    // -------------------------------------------------------------------------- //
    // UART receiver logic depending on the state
    
    always @(posedge clk or negedge rst_n) begin


    end


endmodule