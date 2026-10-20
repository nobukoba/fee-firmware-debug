open_hw_manager
connect_hw_server -url localhost:3121
foreach target [get_hw_targets] {
    puts "STUDY_TARGET $target"
    current_hw_target $target
    if {[catch {open_hw_target} message]} {
        puts "STUDY_OPEN_ERROR $message"
        continue
    }
    foreach device [get_hw_devices] {
        puts "STUDY_DEVICE $device PART=[get_property PART $device]"
    }
    close_hw_target
}
disconnect_hw_server
close_hw_manager
