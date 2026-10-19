"""Source facts behind the early-release hypothesis, not analog causal proof."""
import datetime,hashlib,json,re
from pathlib import Path
root=Path('lrtdc-outerreset-f402/ip/gig_ethernet_pcs_pma/synth/transceiver')
rx=root/'gig_ethernet_pcs_pma_rx_startup_fsm.vhd';tx=root/'gig_ethernet_pcs_pma_tx_startup_fsm.vhd';trans=root/'gig_ethernet_pcs_pma_transceiver.vhd';top=Path('lrtdc-outerreset-f403/hdl/toplevel.vhd')
r=rx.read_text();t=tx.read_text();tr=trans.read_text();s=top.read_text()
assert re.search(r"if \(SOFT_RESET = '1' \) then\s+rx_state\s*<= INIT;\s+RXUSERRDY\s*<= '0';\s+gtrxreset_i\s*<= '0';",r)
assert re.search(r"when ASSERT_ALL_RESETS =>.*?gtrxreset_i\s*<= '1';",r,re.S)
assert re.search(r"if\(SOFT_RESET = '1'\) then.*?tx_state\s*<= INIT;.*?gttxreset_i\s*<= '0';",t,re.S)
assert re.search(r"when ASSERT_ALL_RESETS =>.*?gttxreset_i\s*<= '1';",t,re.S)
assert re.search(r'soft_reset_rx_in\s*=>\s*pmareset',tr,re.I) and re.search(r'soft_reset_tx_in\s*=>\s*pmareset',tr,re.I)
assert 'raw_pwr_on_reset  <= (not clk_sys_locked)' in s and 'port map(raw_pwr_on_reset, X"0FFFFFFF", clk_sys, module_ready, pwr_on_reset)' in s
out=Path('outerreset-native-reset-sequence-analysis.json');assert not out.exists()
result={'created':datetime.datetime.now().isoformat(),'phase':'native_reset_source_facts_crosschecked_before_F403_hardware','facts':['Public PCS reset is synchronized into pmareset, which drives both TX and RX startup FSM SOFT_RESET.','While SOFT_RESET is 1, RX FSM stays INIT with GTRXRESET=0; TX stays INIT with GTTXRESET=0. Public reset held does not imply GT reset pins held high.','After SOFT_RESET releases, native approximately500ns startup wait runs, then ASSERT_ALL_RESETS drives GTRXRESET/GTTXRESET high. Native500ns logic is unchanged.','Original PCS public reset follows global268435455-cycle SYS POR, nominal2.14748364seconds at125MHz.','F403 public PCS reset follows not SYS_LOCKED. Existing synchronization and native startup wait remain; global SiTCP POR is unchanged.'],'hypothesis':'Shorten the interval before the first actual GT reset sequence instead of adding another reset later. This may prevent an unfavorable RX/PMA-CDR startup state formed while the native FSM is held in INIT with GTRXRESET low.','limits':['Source-derived ordering, not a measured power-on GT waveform.','Does not identify the rail, reference-clock behavior, analog component, or board variation initiating failure.','A successful independent F403 source trial is required; F402 early diagnostic alone retains unused timer.'],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),rx,tx,trans,top]}}
out.write_text(json.dumps(result,indent=2));print(json.dumps({'phase':result['phase']}))
