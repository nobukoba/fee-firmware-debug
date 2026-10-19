"""Why existing global ready/reset outputs alone do not supply another timed phase."""
import datetime,hashlib,json,re
from pathlib import Path
timer=Path('lrtdc-outerreset-f402/hdl/common/main/RstDelayTimer.vhd');top=Path('lrtdc-outerreset-f402/hdl/toplevel.vhd')
s=timer.read_text();t=top.read_text()
assert re.search(r'delayRstOut\s*<=\s*reg_reset\s*;',s)
assert re.search(r'readyOut\s*<=\s*not\s+reg_reset\s*;',s)
assert 'port map(raw_pwr_on_reset, X"0FFFFFFF", clk_sys, module_ready, pwr_on_reset)' in t
states=[{'raw':1,'global_POR':1},{'raw':0,'global_POR':1},{'raw':0,'global_POR':0}]
out=Path('outerreset-existing-timer-output-analysis.json');assert not out.exists()
r={'created':datetime.datetime.now().isoformat(),'phase':'existing_global_timer_outputs_are_exact_complements','facts':['Global module_ready is not pwr_on_reset; both come from the same registered signal.','These two outputs provide no separate counter threshold or delayed endpoint.','During ideal monotonic startup, raw/globalPOR pass through only the three listed logical states. With initial reset asserted and final reset released, a combinational function of only these signals chooses either early release or original delayed release, not two finite reset cycles.','F402 adds one existing timer instance for the intermediate1s threshold and reuses global POR for the final endpoint.'],'ideal_startup_states':states,'limits':['Does not exclude other designs using additional existing state or different interfaces. Not a mathematical global line-count minimum.','Propagation glitches are not treated as a reliable additional reset phase.','Hardware efficacy must come from separate complete cold/soak evidence.'],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),timer,top]}}
out.write_text(json.dumps(r,indent=2));print(r['phase'])
