`default_nettype none

module tt_um_uart_receiver (
    input  wire clk,      // clock
    input  wire rst_n,    // reset_n - low to reset
    input  wire ena,      // enable signal (active high)
    input  wire rx,       // UART receive line

    // Outputs
    output reg [6:0] data_out, // Received Hamming(7,4) data output (7 bits)
    output reg [1:0] state_out, // Current state of the receiver
    output reg valid_out  // Indicates if the received data is valid
);

    // -------------------------------------------------------------------------- //
    // State encoding
    localparam [1:0] IDLE  = 2'b00,
                     START = 2'b01,
                     DATA  = 2'b10,
                     STOP  = 2'b11;

    // -------------------------------------------------------------------------- //
    // State and control registers
    reg [1:0] state;          // Current state
    reg [2:0] bit_counter;    // Counts data bits (0-6 for 7 Hamming bits)
    reg [2:0] sample_counter; // Oversampling counter

    assign state_out = state; // Output current state for debugging

    // -------------------------------------------------------------------------- //
    // Main state machine logic

    always @(posedge clk or negedge rst_n) begin    
        if (!rst_n) begin
            // Reset logic
            state <= IDLE;
            bit_counter <= 3'b000;
            sample_counter <= 3'b000;
            data_out <= 7'b0000000;
            valid_out <= 1'b0;
        end else if (ena) begin
            
            case (state)
                // IDLE: Wait for start bit (rx goes HIGH in inverted UART)
                IDLE: begin
                    if (rx == 1'b0) begin  // Start bit detected (LOW in inverted UART)
                        state <= START;
                        sample_counter <= 3'b001;
                    end
                end
                
                // START: Sample middle of start bit
                START: begin
                    // Oversample start bit, change state only at end
                    if (sample_counter == 3'b111) begin
                        if (rx == 1'b0) begin       // Start bit is LOW
                            state <= DATA;
                            bit_counter <= 3'b000;
                            sample_counter <= 3'b000;
                            data_out <= 7'b0000000;     // Reset data register when entering START state
                            valid_out <= 1'b0;          // Reset valid output
                        end else begin // Invalid start bit
                            state <= IDLE;
                            sample_counter <= 3'b000;
                        end
                    end else begin
                        sample_counter <= sample_counter + 1;
                    end
                    
                end
                
                // DATA: Receive 7 data bits for Hamming(7,4) code
                DATA: begin
                    if (sample_counter == 3'b011) begin
                        data_out <= {rx, data_out[6:1]}; // LSB first
                        sample_counter <= sample_counter + 1;

                    end else if (sample_counter == 3'b111) begin
                        sample_counter <= 3'b000; // Reset counter for next bit

                        // check if all bits received
                        if (bit_counter == 3'b110) begin
                            // All 7 bits received (bit 0 through bit 6)
                            state <= STOP;
                            bit_counter <= 3'b000; // Reset bit counter for next frame
                        end else begin
                            bit_counter <= bit_counter + 1;
                        end
                    end else begin
                        sample_counter <= sample_counter + 1;
                    end
                end
                
                // STOP: Check for stop bit (should be HIGH in UART)
                STOP: begin
                    if (sample_counter == 3'b111) begin
                        state <= IDLE;
                        sample_counter <= 3'b000;
                    end else if(sample_counter == 3'b011) begin
                        valid_out <= rx; // Stop bit is HIGH
                        sample_counter <= sample_counter + 1;
                    end else begin
                        sample_counter <= sample_counter + 1;
                    end
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule