# Read-only fresh routed netlist inspection before designing matched control.
if {[file exists outerreset-f401-netlist-inspection.txt]} {error "Refuse overwrite"}
open_checkpoint I:/build/outerreset-f401/lrtdc-outerreset-f401.dcp
set f [open outerreset-f401-netlist-inspection.txt w]
foreach pattern {*pcs_reset_once* *pcs_wait* *raw_pwr_on_reset* *pwr_on_reset*} {
 puts $f "PATTERN $pattern"
 foreach net [get_nets -hier -quiet -filter [format {NAME =~ %s} $pattern]] {
  puts $f "NET $net"
  puts $f "DRIVERS [get_pins -leaf -of_objects [get_nets -segments $net] -filter {DIRECTION == OUT}]"
  puts $f "SINKS [get_pins -leaf -of_objects [get_nets -segments $net] -filter {DIRECTION == IN}]"
 }
}
set candidates [get_cells -hier -quiet -filter {NAME =~ *pcs_reset* || NAME =~ *u_PcsWait*/reg_reset_reg || NAME =~ *u_KeepPwrOnRst*/reg_reset_reg}]
foreach net [get_nets -hier -quiet -filter {NAME =~ *pcs_wait*}] {
 foreach pin [get_pins -leaf -of_objects [get_nets -segments $net] -filter {DIRECTION == IN}] {
  set cell [get_cells -of_objects $pin]
  if {[string match LUT* [get_property REF_NAME $cell]]} {lappend candidates $cell}
 }
}
foreach cell [lsort -unique $candidates] {
 puts $f "CELL $cell REF [get_property REF_NAME $cell]"
 if {[lsearch -exact [list_property $cell] INIT]>=0} {puts $f "INIT [get_property INIT $cell]"}
 foreach pin [get_pins -of_objects $cell] {
  set net [get_nets -segments -of_objects $pin]
  puts $f "PIN [get_property REF_PIN_NAME $pin] DRIVERS [get_pins -leaf -of_objects $net -filter {DIRECTION == OUT}]"
  if {[get_property REF_PIN_NAME $pin] eq "C"} {puts $f "CLOCKS [get_clocks -of_objects $pin]"}
 }
}
close $f
close_design
exit
