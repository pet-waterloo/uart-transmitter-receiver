/**
 * UART Transmitter Module
 * Transmits parallel data serially over UART protocol.
 */

`default_nettype none

typedef enum logic [1:0] {
    IDLE = 2'b00,               // wait for tx_start = 1 signal to load
    LOAD = 2'b01,               // load data into shift register
    SEND = 2'b10,               // shift out one bit each clock tick
    DONE = 2'b11                // transmission complete, return to IDLE
} state_t;

module uart_tx (
    input wire clk,
    input wire rst_n,
    input wire tx_start,        // start transmission
    input wire [7:0] tx_data,   // 8-bit data to transmit
    output wire tx,             // UART serial output
    output wire tx_busy         // transmitter busy flag
);
    state_t state, next_state;

    reg[9:0] shift_reg;         // 1 stop bit, 8 data bits, 1 start bit
    reg[3:0] bit_count;         // counts number of bits sent

    assign tx = shift_reg[0];
    assign tx_busy = (state != IDLE);

    // fsm next state logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
        else
            state <= next_state;
        end
    end

    // shift register and bit counter logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg <= 10'b1111111111;
            bit_count <= 0;
        end else begin
            case (state)
                LOAD: begin
                    shift_reg <= {1'b1, tx_data, 1'b0};
                    bit_count <= 0;
                end
                SEND: begin
                    shift_reg <= {1'b1, shift_reg[9:1]};
                    bit_count <= bit_count + 1;
                end
            endcase
        end
    end
endmodule
