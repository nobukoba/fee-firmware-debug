open_checkpoint K:/build/outerreset-f403/lrtdc-outerreset-f403.dcp
set root K:/build/outerreset-f403
foreach kind {FDPE FDCE} {
 set cells [get_cells -hier -filter "REF_NAME == $kind"]
 foreach prop {NAME INIT} {
  set f [open $root/init-$kind-$prop.tcllist w]
  puts -nonewline $f [get_property $prop $cells]
  close $f
 }
}
set f [open $root/fresh-clock-reset-extra.txt w]
foreach cell [get_cells -hier -quiet -filter {NAME =~ gen_pcspma*core_resets_i/pma_reset_pipe_reg*}] {
 puts $f "RESET_SYNC_STAGE $cell ASYNC_REG [get_property ASYNC_REG $cell]"
 set pin [get_pins $cell/C]
 foreach clk [get_clocks -of_objects $pin] {puts $f "RESET_SYNC_CLOCK $pin $clk [get_property PERIOD $clk]"}
 puts $f "RESET_SYNC_CLOCK_DRIVER [get_pins -leaf -of_objects [get_nets -segments -of_objects $pin] -filter {DIRECTION == OUT}]"
}
set gts [get_cells -hier -filter {REF_NAME == GTXE2_CHANNEL && NAME =~ gen_pcspma*}]
if {[llength $gts]!=1} {error "PCS GT channel ambiguous"}
foreach gt $gts {
 puts $f "PCS_GT $gt"
 foreach prop {CPLL_FBDIV CPLL_FBDIV_45 CPLL_REFCLK_DIV RXOUT_DIV TXOUT_DIV} {puts $f "PCS_GT_PROPERTY $prop [get_property $prop $gt]"}
 foreach name {RXPMARESET RXCDRHOLD RXSYSCLKSEL[0] RXSYSCLKSEL[1] TXSYSCLKSEL[0] TXSYSCLKSEL[1]} {
  set pin [get_pins -of_objects $gt -filter "REF_PIN_NAME == $name"]
  puts $f "PCS_GT_PIN $name NET [get_nets -of_objects $pin]"
 }
}
foreach pin [get_pins -hier -filter {NAME =~ *u_KeepPwrOnRst/reg_reset_reg/C}] {
 foreach clk [get_clocks -of_objects $pin] {puts $f "GLOBAL_TIMER_CLOCK $pin $clk [get_property PERIOD $clk]"}
 puts $f "GLOBAL_TIMER_CLOCK_DRIVER [get_pins -leaf -of_objects [get_nets -segments -of_objects $pin] -filter {DIRECTION == OUT}]"
}
foreach net [get_nets -hier -quiet -filter {NAME =~ *raw_pwr_on_reset*}] {
 puts $f "RAW_RESET_NET $net"
 puts $f "RAW_RESET_DRIVERS [get_pins -leaf -of_objects [get_nets -segments $net] -filter {DIRECTION == OUT}]"
 puts $f "RAW_RESET_SINKS [get_pins -leaf -of_objects [get_nets -segments $net] -filter {DIRECTION == IN}]"
}
close $f
close_design
exit
