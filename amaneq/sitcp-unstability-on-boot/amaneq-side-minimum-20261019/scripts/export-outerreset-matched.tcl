# Configuration is prepared only after fresh routed gate/clock inspection.
if {$argc!=1} {error "Expected reviewed candidate configuration Tcl"}
source [lindex $argv 0]
foreach key {candidate dcp root gate reference enabled_init variants drivers timer_clocks timer_drivers} {if {![dict exists $cfg $key]} {error "Missing $key"}}
set root [dict get $cfg root]
if {[file exists $root]} {error "Refuse overwrite"}
source deepreset_column_audit.tcl
open_checkpoint [dict get $cfg dcp]
set gate [get_cells [dict get $cfg gate]]
if {[llength $gate]!=1 || [get_property REF_NAME $gate] ne [dict get $cfg reference]} {error "Gate identity mismatch"}
if {[get_property INIT $gate] ne [dict get $cfg enabled_init]} {error "Source enabled truth table mismatch"}
foreach {pin expected} [dict get $cfg drivers] {
 set p [get_pins $gate/$pin]
 set found [lsort [get_pins -leaf -of_objects [get_nets -segments -of_objects $p] -filter {DIRECTION == OUT}]]
 if {$found ne $expected} {error "Gate input source mismatch $pin: $found"}
}
file mkdir $root
set f [open $root/fresh-clock-reset-audit.txt w]
foreach {pin expected_period} [dict get $cfg timer_clocks] {
 set clocks [get_clocks -of_objects [get_pins $pin]]
 if {[llength $clocks]!=1 || abs([get_property PERIOD $clocks]-$expected_period)>0.00001} {error "Timer clock mismatch $pin"}
 puts $f "TIMER_CLOCK $pin $clocks PERIOD [get_property PERIOD $clocks]"
 set found [lsort [get_pins -leaf -of_objects [get_nets -segments -of_objects [get_pins $pin]] -filter {DIRECTION == OUT}]]
 if {$found ne [dict get $cfg timer_drivers $pin]} {error "Unexpected SYS clock driver $pin: $found"}
 puts $f "TIMER_CLOCK_DRIVER $pin $found"
}
foreach pin [get_pins -of_objects $gate] {
 set net [get_nets -segments -of_objects $pin]
 puts $f "GATE_PIN [get_property REF_PIN_NAME $pin] DRIVERS [get_pins -leaf -of_objects $net -filter {DIRECTION == OUT}]"
 if {[get_property DIRECTION $pin] eq "OUT"} {puts $f "RESET_SINKS [get_pins -leaf -of_objects $net -filter {DIRECTION == IN}]"}
}
foreach gt [get_cells -hier -filter {REF_NAME == GTXE2_CHANNEL}] {
 puts $f "GT $gt"
 foreach property {CPLL_FBDIV CPLL_FBDIV_45 CPLL_REFCLK_DIV RXOUT_DIV TXOUT_DIV RX_DATA_WIDTH RX_INT_DATAWIDTH RXCDR_CFG} {puts $f "$property [get_property $property $gt]"}
 foreach pin {RXSYSCLKSEL[0] RXSYSCLKSEL[1] TXSYSCLKSEL[0] TXSYSCLKSEL[1] RXCDRHOLD GTRXRESET RXPMARESET RXUSERRDY CPLLRESET} {
  set p [get_pins -quiet $gt/$pin]
  if {[llength $p]} {puts $f "GT_PIN $pin NET [get_nets -segments -of_objects $p]"}
 }
}
close $f
foreach {variant init} [dict get $cfg variants] {
 set folder $root/$variant;file mkdir $folder
 set_property INIT $init $gate
 deepreset_write_primitives $folder/all-primitives.tsv
 report_timing_summary -file $folder/timing-summary.rpt
 report_bus_skew -warn_on_violation -file $folder/bus-skew.rpt
 report_drc -file $folder/drc.rpt
 write_checkpoint $folder/lrtdc-[dict get $cfg candidate].dcp
 write_bitstream $folder/lrtdc-[dict get $cfg candidate].bit
 write_cfgmem -format mcs -size 16 -interface SPIx4 -loadbit "up 0x0 $folder/lrtdc-[dict get $cfg candidate].bit" -file $folder/lrtdc-[dict get $cfg candidate].mcs
 puts "OUTERRESET_MATCHED_EXPORTED $variant $init"
}
close_design
exit
