define_corners ff tt ss
read_liberty -corner tt pdk_files/sky130_fd_sc_hd__tt_025C_1v80.lib
read_liberty -corner ss pdk_files/sky130_fd_sc_hd__ss_n40C_1v76.lib
read_liberty -corner ff pdk_files/sky130_fd_sc_hd__ff_n40C_1v76.lib

# Read the synthesized netlist (gate-level Verilog) instead of RTL
read_verilog src/tt_um_ultrasword_jonz9.v

# Link the correct design name
link_design tt_um_ultrasword_jonz9

# Read the SPEF file (parasitic extraction)
read_spef src/tt_um_ultrasword_jonz9.nom.spef

# Debug: Check what ports exist
puts "=== DEBUG: All ports ==="
foreach port [get_ports *] {
    puts "Port: [get_name $port]"
}

# 50MHz clock = 20ns period
create_clock -name clk -period 20 [get_ports clk]

set_clock_uncertainty 0.1 [all_clocks]
set_clock_transition  0.1 [all_clocks]

# Set timing constraints for UART operation
# Input delay for ui_in[0] (UART RX signal) - accounting for 8 clock cycle hold time
set_input_delay  -min  1.0 -clock [get_clocks clk] [get_ports {ui_in[0]}]
set_input_delay  -max  2.0 -clock [get_clocks clk] [get_ports {ui_in[0]}]

# Other inputs - specify each one individually
foreach input_port [get_ports {ui_in[1] ui_in[2] ui_in[3] ui_in[4] ui_in[5] ui_in[6] ui_in[7] uio_in[0] uio_in[1] uio_in[2] uio_in[3] uio_in[4] uio_in[5] uio_in[6] uio_in[7] ena rst_n}] {
    set_input_delay  -min  0.5 -clock [get_clocks clk] $input_port
    set_input_delay  -max  0.5 -clock [get_clocks clk] $input_port
}

# Output delays for critical UART outputs
# uo_out[1] = uart_valid
set_output_delay -min -1.0 -clock [get_clocks clk] [get_ports {uo_out[1]}]
set_output_delay -max -0.5 -clock [get_clocks clk] [get_ports {uo_out[1]}]

# uo_out[6:2] = decode_out[3:0] (4-bit decoded data)
set_output_delay -min -1.0 -clock [get_clocks clk] [get_ports {uo_out[2]}]
set_output_delay -max -0.5 -clock [get_clocks clk] [get_ports {uo_out[2]}]
set_output_delay -min -1.0 -clock [get_clocks clk] [get_ports {uo_out[3]}]
set_output_delay -max -0.5 -clock [get_clocks clk] [get_ports {uo_out[3]}]
set_output_delay -min -1.0 -clock [get_clocks clk] [get_ports {uo_out[5]}]
set_output_delay -max -0.5 -clock [get_clocks clk] [get_ports {uo_out[5]}]
set_output_delay -min -1.0 -clock [get_clocks clk] [get_ports {uo_out[6]}]
set_output_delay -max -0.5 -clock [get_clocks clk] [get_ports {uo_out[6]}]

# Other outputs - specify individually
foreach output_port [get_ports {uo_out[0] uo_out[4] uo_out[7] uio_out[0] uio_out[1] uio_out[2] uio_out[3] uio_out[4] uio_out[5] uio_out[6] uio_out[7] uio_oe[0] uio_oe[1] uio_oe[2] uio_oe[3] uio_oe[4] uio_oe[5] uio_oe[6] uio_oe[7]}] {
    set_output_delay -min -2.5 -clock [get_clocks clk] $output_port
    set_output_delay -max -2.5 -clock [get_clocks clk] $output_port
}

set_propagated_clock [all_clocks]

puts "=== TIMING ANALYSIS FOR UART TEST ==="
puts "Clock: 50MHz (20ns period)"
puts "Test sequence: 2 high bits + 1111111"
puts "Expected: 8 clock cycles per bit"
puts "Monitoring: uo_out\[1\] (uart_valid), uo_out\[6,5,3,2\] (decode_out)"

puts "=== DEBUG: Clocks created ==="
foreach clk [all_clocks] {
    puts "Clock: [get_name $clk] Period: [get_property $clk period]ns"
}

puts "=== DEBUG: Critical paths ==="
puts "Input: ui_in\[0\] (UART RX)"
puts "Outputs: uo_out\[1\] (uart_valid), uo_out\[6,5,3,2\] (decode_out\[3:0\])"

puts "Marker A"

# Focus on setup and hold timing for UART signals
report_checks -from [get_ports {ui_in[0]}] -to [get_ports {uo_out[1] uo_out[2] uo_out[3] uo_out[5] uo_out[6]}]

# Check clock skew and hold violations
report_clock_skew -hold 
report_annotated_check -hold 

# Overall timing analysis
report_checks -path_delay min_max
report_checks -corner tt

# Check for any unconstrained paths
report_checks -unconstrained

puts "=== UART TIMING SUMMARY ==="
puts "At 50MHz with 8 cycles per bit:"
puts "Bit period = 8 * 20ns = 160ns"
puts "UART baud rate = 6.25MHz / 8 = 781.25 kbaud"