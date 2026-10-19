# Save a separate project with qualified IP run products. Never edit the source project.
open_project J:/build/StrLrTdc.xpr
if {[file exists K:/build/StrLrTdcF403.xpr]} {error "Refuse overwrite"}
save_project_as StrLrTdcF403 K:/build
if {[string tolower [file normalize [get_property DIRECTORY [current_project]]]] ne [string tolower [file normalize K:/build]]} {error "SaveAs directory mismatch"}
file mkdir K:/build/outerreset-f403
set audit [open K:/build/outerreset-f403/reused-ip-runs.txt w]
foreach run [get_runs -filter {IS_SYNTHESIS == 1}] {
 if {$run ne "synth_1"} {
  puts $audit "BEFORE $run [get_property PROGRESS $run] [get_property STATUS $run] [get_property DIRECTORY $run]"
  if {[get_property PROGRESS $run] ne "100%"} {error "Incomplete cached IP: $run"}
 }
}
foreach name {toplevel.vhd defBusAddressMap.vhd} {
 set oldfiles [get_files -all -filter "NAME =~ */$name"]
 if {[llength $oldfiles]!=1} {error "Ambiguous source: $name $oldfiles"}
 set old [lindex $oldfiles 0]
 set library [get_property LIBRARY $old]
 set kind [get_property FILE_TYPE $old]
 remove_files $old
 add_files -norecurse K:/hdl/$name
 set new [get_files K:/hdl/$name]
 set_property LIBRARY $library $new
 set_property FILE_TYPE $kind $new
}
update_compile_order -fileset sources_1
set sources [open K:/build/outerreset-f403/compiled-files.txt w]
foreach f [get_files -compile_order sources -used_in synthesis] {puts $sources [file normalize $f]}
close $sources
reset_run synth_1
launch_runs synth_1 -jobs 2
wait_on_run synth_1
if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Fresh top synthesis failed"}
foreach run [get_runs -filter {IS_SYNTHESIS == 1}] {
 if {$run ne "synth_1"} {puts $audit "AFTER $run [get_property PROGRESS $run] [get_property STATUS $run] [get_property DIRECTORY $run]"}
}
close $audit
set_property AUTO_INCREMENTAL_CHECKPOINT 0 [get_runs impl_1]
set_property INCREMENTAL_CHECKPOINT [file normalize J:/build/outerreset-f402/lrtdc-outerreset-f402.dcp] [get_runs impl_1]
launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
open_run impl_1
report_timing_summary -file K:/build/outerreset-f403/timing-summary.rpt
report_bus_skew -warn_on_violation -file K:/build/outerreset-f403/bus-skew.rpt
report_drc -file K:/build/outerreset-f403/drc.rpt
report_utilization -file K:/build/outerreset-f403/utilization.rpt
report_incremental_reuse -file K:/build/outerreset-f403/incremental-reuse.rpt
set f [open K:/build/outerreset-f403/fresh-clock-reset-audit.txt w]
if {[llength [get_cells -hier -quiet -filter {NAME =~ *u_PcsWait*}]]} {error "Unexpected extra timer"}
foreach cell [get_cells -hier -quiet -filter {NAME =~ gen_pcspma*core_resets_i/pma_reset_pipe_reg*}] {
 set pre [get_pins -quiet $cell/PRE]
 if {[llength $pre]} {
  set drivers [get_pins -leaf -of_objects [get_nets -segments -of_objects $pre] -filter {DIRECTION == OUT}]
  puts $f "PUBLIC_RESET_SINK $pre DRIVERS $drivers"
  if {[llength $drivers]!=1} {error "Reset driver ambiguous"}
  set drv [lindex $drivers 0];set gate [get_cells -of_objects $drv]
  puts $f "DRIVER_CELL $gate REF [get_property REF_NAME $gate] INIT [get_property INIT $gate]"
  foreach pin [get_pins -of_objects $gate -filter {DIRECTION == IN}] {
   puts $f "DRIVER_INPUT $pin DRIVERS [get_pins -leaf -of_objects [get_nets -segments -of_objects $pin] -filter {DIRECTION == OUT}]"
  }
 }
}
foreach gt [get_cells -hier -filter {REF_NAME == GTXE2_CHANNEL}] {
 foreach prop {CPLL_FBDIV CPLL_FBDIV_45 CPLL_REFCLK_DIV RXOUT_DIV TXOUT_DIV} {puts $f "GT $prop [get_property $prop $gt]"}
}
set lock [get_pins u_ClkMan_Inst/inst/mmcm_adv_inst/LOCKED]
puts $f "SYS_LOCK $lock"
close $f
write_checkpoint -force K:/build/outerreset-f403/lrtdc-outerreset-f403.dcp
write_bitstream -force K:/build/outerreset-f403/lrtdc-outerreset-f403.bit
write_cfgmem -force -format mcs -size 16 -interface SPIx4 -loadbit "up 0x0 K:/build/outerreset-f403/lrtdc-outerreset-f403.bit" -file K:/build/outerreset-f403/lrtdc-outerreset-f403.mcs
close_project
exit
