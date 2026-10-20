# Read FPGA configuration status without programming or resetting either board.
open_hw_manager
connect_hw_server -url localhost:3121
set target_index 0
foreach target [get_hw_targets] {
    incr target_index
    current_hw_target $target
    if {[catch {open_hw_target} message]} {
        puts "STUDY_CONFIG target=$target_index open_failed"
        continue
    }
    foreach device [get_hw_devices] {
        if {[catch {refresh_hw_device -update_hw_probes false $device} message]} {
            puts "STUDY_CONFIG target=$target_index refresh_failed"
            continue
        }
        foreach property [list_property $device] {
            if {[regexp {^(PROGRAM.IS_PROGRAMMED|REGISTER.(CONFIG_STATUS|BOOT_STATUS|USR_ACCESS|IDCODE))$} $property]} {
                puts "STUDY_CONFIG target=$target_index $property=[get_property $property $device]"
            }
        }
    }
    close_hw_target
}
disconnect_hw_server
close_hw_manager
