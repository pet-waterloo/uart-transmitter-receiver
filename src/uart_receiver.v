`default_nettype none

module tt_um_uart_receiver (
    // Input signals
    input  wire clk,      // clock
    input  wire rst_n,    // reset_n - low to reset
    input  wire ena,      // enable signal (active high)
    input  wire rx,       // UART receive line

    // Output signals
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

    assign state_out = state; // Output current state

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
            // Default: valid_out is normally low except when explicitly set
            valid_out <= 1'b0;
            
            case (state)

                // IDLE: Wait for start bit (rx goes LOW in standard UART)
                IDLE: begin
                    if (rx == 1'b0) begin  // Start bit detected (LOW)
                        state <= START;
                        sample_counter <= 3'b000;
                    end
                end
                
                // START: Sample middle of start bit
                //        read 0 for 8 cycles to ensure stable start bit
                START: begin
                    // sample at middle of oversampling period
                    if (sample_counter == 3'b100) begin
                        // Verify it's still low at the middle of the bit
                        if (rx == 1'b0) begin
                            // valid start bit detected
                            bit_counter <= 3'b000;
                        end else if (sample_counter == 3'b111) begin
                            // change state when done sampling
                            state <= DATA;
                            sample_counter <= 3'b000;
                        end else begin
                            // False start, go back to IDLE
                            state <= IDLE;
                        end
                    end 
                    sample_counter <= sample_counter + 1;
                end
                
                // DATA: Receive 7 data bits for Hamming(7,4) code
                DATA: begin
                    if (sample_counter == 3'b100) begin
                        // Sample at middle of bit
                        data_out <= {rx, data_out[6:1]}; // LSB first
                    end else if (sample_counter == 3'b111) begin
                        // Finished sampling a bit
                        if (bit_counter == 3'b111) begin
                            // All 7 bits received (bit 0 through bit 6)
                            state <= STOP;
                        end else begin
                            bit_counter <= bit_counter + 1;
                        end

                        // Reset sample counter for next bit
                        sample_counter <= 3'b000;
                    end
                    sample_counter <= sample_counter + 1;
                end
                
                // STOP: Check for stop bit 
                STOP: begin
                    if (sample_counter == 3'b100) begin
                        if (rx == 1'b1) begin  // Stop bit is HIGH
                            // Valid stop bit detected
                            valid_out <= 1'b1;
                        end
                        // Return to IDLE regardless of stop bit
                        state <= IDLE;
                    end 
                    sample_counter <= sample_counter + 1;
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule