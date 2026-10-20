# Generate the upstream project.tcl first. Run from the StrHrTdcBase clone.
open_project build/StrHrTdcBase.xpr
report_ip_status -file build/baseline-ip-status.txt
set locked_ips [get_ips -filter {IS_LOCKED == 1}]
if {[llength $locked_ips] > 0} {
    upgrade_ip $locked_ips
}
generate_target all [get_ips]
update_compile_order -fileset sources_1
launch_runs synth_1 -jobs 2
wait_on_run synth_1
puts "STUDY_SYNTH_STATUS [get_property STATUS [get_runs synth_1]]"
if {![string match {*Complete*} [get_property STATUS [get_runs synth_1]]]} {
    error "Baseline synthesis failed"
}
launch_runs impl_1 -to_step write_bitstream -jobs 2
wait_on_run impl_1
puts "STUDY_IMPL_STATUS [get_property STATUS [get_runs impl_1]]"
if {![string match {*Complete*} [get_property STATUS [get_runs impl_1]]]} {
    error "Baseline implementation failed"
}
open_run impl_1
report_timing_summary -file build/baseline-timing-summary.txt
report_drc -file build/baseline-drc.txt
close_project
