# AMANEQ top-level-only one-shot reset. Native RX FSM is not patched.
set f [open hdl/defBusAddressMap.vhd r];set version_source [read $f];close $f
if {![regexp -nocase {60c4f401} $version_source]} {error "Candidate version/workspace mismatch"}
if {[file exists build/outerreset-f401/lrtdc-outerreset-f401.mcs]} {error "Refuse overwrite completed candidate"}
proc patch_file {path pattern replacement expected} {
    set f [open $path r]; set data [read $f]; close $f
    regsub -all -- $pattern $data $replacement data
    if {![regexp -- $expected $data]} {error "Patch verification failed: $path"}
    set f [open $path w]; puts -nonewline $f $data; close $f
}
if {![file exists build/StrLrTdc.xpr]} {
    set f [open project.tcl r]; set script [read $f]; close $f
    regsub {exit\s*$} $script {} script
    eval $script
} else {
    open_project build/StrLrTdc.xpr
}
set_param project.defaultIPCacheSetting none
file mkdir build/outerreset-f401
if {![file exists build/outerreset-f401/ip-prepared]} {
    foreach ip [get_ips] {set_property IS_MANAGED true [get_files ${ip}.xci]}
    upgrade_ip [get_ips]
    generate_target all [get_ips]
    set_property IS_MANAGED false [get_files gig_ethernet_pcs_pma.xci]
    set eth_dir ip/gig_ethernet_pcs_pma/synth
    patch_file $eth_dir/transceiver/gig_ethernet_pcs_pma_gtwizard_gt.vhd {CPLL_FBDIV_45(\s*=>\s*)\(5\)} {CPLL_FBDIV_45\1(4)} {CPLL_FBDIV_45\s*=>\s*\(4\)}
    patch_file $eth_dir/gig_ethernet_pcs_pma_ooc.xdc {(-name gtrefclk -period )8\.000} {\16.400} {-name gtrefclk -period 6\.400}
    patch_file $eth_dir/gig_ethernet_pcs_pma.xdc {-period 16\.000} {-period 12.800} {-period 12\.800}
    foreach ip [get_ips] {create_ip_run $ip}
    report_ip_status -file build/outerreset-f401/ip-status.rpt
    close [open build/outerreset-f401/ip-prepared w]
}
set f [open ip/gig_ethernet_pcs_pma/synth/transceiver/gig_ethernet_pcs_pma_rx_startup_fsm.vhd r];set rx_source [read $f];close $f
if {![regexp {constant STARTUP_DELAY\s*:\s*integer\s*:=\s*500;} $rx_source] || ![regexp {signal\s+gtrxreset_i\s*:\s*std_logic\s*:=\s*'0';} $rx_source]} {error "Native RX FSM changed"}
set f [open ip/gig_ethernet_pcs_pma/synth/transceiver/gig_ethernet_pcs_pma_gtwizard.vhd r];set gt_source [read $f];close $f
if {![regexp {STABLE_CLOCK_PERIOD\s*=>\s*5\s*,} $gt_source]} {error "Unexpected stable-clock period"}

if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {
    if {[string match *ERROR* [get_property STATUS [get_runs synth_1]]]} {reset_run synth_1}
    launch_runs synth_1 -jobs 2
    wait_on_run synth_1
    if {[get_property PROGRESS [get_runs synth_1]] ne "100%"} {error "Synthesis failed"}
}
set_property AUTO_INCREMENTAL_CHECKPOINT 0 [get_runs impl_1]
set_property INCREMENTAL_CHECKPOINT [file normalize Y:/lrtdc-longhold-f310/build/longhold-f310/lrtdc-longhold-f310.dcp] [get_runs impl_1]
if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {
    if {[string match *ERROR* [get_property STATUS [get_runs impl_1]]]} {reset_run impl_1}
    launch_runs impl_1 -to_step write_bitstream -jobs 2
    wait_on_run impl_1
    if {[get_property PROGRESS [get_runs impl_1]] ne "100%"} {error "Implementation failed"}
}
open_run impl_1
if {[catch {report_incremental_reuse -file build/outerreset-f401/incremental-reuse.rpt} msg]} {puts "INCREMENTAL_REUSE_REPORT_UNAVAILABLE $msg"}
report_timing_summary -file build/outerreset-f401/timing-summary.rpt
report_bus_skew -warn_on_violation -file build/outerreset-f401/bus-skew.rpt
report_drc -file build/outerreset-f401/drc.rpt
report_utilization -file build/outerreset-f401/utilization.rpt
write_checkpoint -force build/outerreset-f401/lrtdc-outerreset-f401.dcp
file copy -force build/StrLrTdc.runs/impl_1/toplevel.bit build/outerreset-f401/lrtdc-outerreset-f401.bit
write_cfgmem -force -format mcs -size 16 -interface SPIx4 -loadbit "up 0x0 build/outerreset-f401/lrtdc-outerreset-f401.bit" -file build/outerreset-f401/lrtdc-outerreset-f401.mcs
close_project
exit
