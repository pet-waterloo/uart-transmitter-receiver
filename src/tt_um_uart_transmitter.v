`default_nettype none

/**
 * UART Transmitter Module
 * Transmits parallel data serially over UART protocol.
 */
// State encoding
localparam IDLE = 2'b00;
localparam LOAD = 2'b01;
localparam SEND = 2'b10;
localparam DONE = 2'b11;

module tt_um_uart_transmitter (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        tx_start,        // start transmission (1-cycle pulse)
    input  wire [7:0]  tx_data,         // 8-bit data (Hamming encoded)
    output reg         tx,              // UART serial output
    output wire        tx_busy          // transmitter busy flag
);
    reg [1:0] state, next_state;

    reg [9:0] shift_reg;                // {stop bit, data[7:0], start bit}
    reg [3:0] bit_count;                // counts bits in frame (0 to 9)
    reg [2:0] clk_count;                // counts 0 to 7 (8 cycles per bit)
    reg [7:0] tx_data_latched;

    assign tx_busy = (state != IDLE);

    // Debug monitoring
    always @(posedge clk) begin
        if (tx_start)
            $display("UART TX: Start signal received with data 0x%h", tx_data);
    end

    // FSM: State transition
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    // FSM: Next-state logic
    always @(*) begin
        case (state)
            IDLE : next_state = tx_start ? LOAD : IDLE;
            LOAD : next_state = SEND;
            // 10 bits total (0..9). Go DONE after last bit has been held for full baud period.
            SEND : next_state = (bit_count == 4'd9 && clk_count == 3'd7) ? DONE : SEND;
            DONE : next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end

    // shift register and counters
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            shift_reg        <= 10'b1111111111; // idle state
            bit_count        <= 4'd0;
            clk_count        <= 3'd0;
            tx               <= 1'b1;           // idle line high
            tx_data_latched  <= 8'h00;
        end else begin
            case (state)
                // IDLE state when line is high, waiting for tx_start signal
                IDLE: begin
                    tx        <= 1'b1;
                    clk_count <= 3'd0;
                    bit_count <= 4'd0;
                    if (tx_start) begin
                        tx_data_latched <= tx_data;
                    end
                end

                // LOAD state prepares shift_reg with start/data/stop bits
                LOAD: begin
                    // Format: {stop bit, data MSB→LSB, start bit}
                    shift_reg <= {1'b1, tx_data_latched, 1'b0};
                    tx        <= 1'b0;  // immediately output start bit
                    bit_count <= 4'd0;
                    clk_count <= 3'd0;
                end

                // SEND state shifts out the data bits
                SEND: begin
                    tx <= shift_reg[0]; // drive current bit onto tx line

                    if (clk_count == 3'd7) begin
                        clk_count <= 3'd0;
                        bit_count <= bit_count + 1'b1;
                        shift_reg <= {1'b1, shift_reg[9:1]}; // shift right, MSB filled with 1 (idle)
                    end else begin
                        clk_count <= clk_count + 1'b1;
                    end
                end

                // DONE state resets shift_reg and counters after transmission
                DONE: begin
                    shift_reg  <= 10'b1111111111;
                    bit_count  <= 4'd0;
                    clk_count  <= 3'd0;
                    tx         <= 1'b1; // idle
                end
            endcase
        end
    end
endmodule