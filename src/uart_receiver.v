



`default_nettype none

module tt_um_uart_receiver (
    input  wire clk,      // clock
    input  wire rst_n,   // reset_n - low to reset
    input  wire ena,     // enable signal (active high)
    input  wire rx,      // UART receive line
    output reg [7:0] data_out, // Received data output
    output reg valid_out // Indicates if the received data is valid
);

    typedef enum [1:0] {
        IDLE = 2'b00,
        DECODE = 2'b01,
        VALIDATE = 2'b10,
        DONE = 2'b11
    } state_t;
    state_t state = IDLE; // Current state of the decoder

    reg [3:0] baud_rate; // oversample rate ~ 0-15 ticks

    // -------------------------------------------- //
    // State machine for UART receiver


endmodule