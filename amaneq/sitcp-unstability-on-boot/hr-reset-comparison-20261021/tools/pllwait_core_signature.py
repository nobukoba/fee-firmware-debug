"""Tcl for a read-only routed Ethernet-core signature."""
def commands(output):
 return 'set sig [open {'+output+'} w]\n'+r'''
foreach c [lsort [get_cells -hier -filter {IS_PRIMITIVE == 1 && NAME =~ gen_pcspma*}]] {
 puts $sig [join [list CELL $c [get_property REF_NAME $c] [get_property LOC $c] [get_property BEL $c]] "\t"]
}
foreach n [lsort [get_nets -hier -filter {NAME =~ gen_pcspma*}]] {
 if {[regexp {/<const[01]>$} $n]} {puts $sig [join [list SKIP $n shared_constant_route] "\t"]; continue}
 set route [regsub -all {\s+} [get_property ROUTE $n] { }]
 set pins [join [lsort [get_pins -leaf -of_objects $n]] { }]
 puts $sig [join [list NET $n $route $pins] "\t"]
}
close $sig
'''
