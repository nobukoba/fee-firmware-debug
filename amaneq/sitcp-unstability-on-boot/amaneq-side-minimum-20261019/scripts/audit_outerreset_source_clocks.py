"""Static clock/reset dependency audit for both top-level-only candidates."""
import datetime,hashlib,json,re
from pathlib import Path
out=Path('outerreset-source-clock-audit.json');assert not out.exists();sources={};cases=[]
def source(p):
 p=Path(p);sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return p.read_text()
for candidate in ['f401','f402']:
 root=Path('lrtdc-outerreset-'+candidate);top=source(root/'hdl/toplevel.vhd');wrapper=source(root/'hdl/common/gig_ethernet_pcs_pma/GbEPcsPma.vhd');resets=source(root/'hdl/common/gig_ethernet_pcs_pma/gig_ethernet_pcs_pma_resets.vhd');timer=source(root/'hdl/common/main/RstDelayTimer.vhd')
 assert re.search(r'raw_pwr_on_reset\s*<=\s*\(not clk_sys_locked\)',top)
 assert 'port map(raw_pwr_on_reset, X"0FFFFFFF", clk_sys, module_ready, pwr_on_reset)' in top
 wizard=top[top.index('u_ClkSys_Inst'):] if 'u_ClkSys_Inst' in top else top[top.index('clk_wiz_sys',top.index('begin')):]
 assert all(x in wizard for x in ['BASE_CLKP','BASE_CLKN','clk_sys_locked','clk_sys','clk_gbe'])
 assert re.search(r'process\(reset, independent_clock_bufg\)',resets) and 'pma_reset_pipe <= "1111"' in resets
 assert "pma_reset_pipe <= pma_reset_pipe(2 downto 0) & reset" in resets
 assert 'attribute ASYNC_REG of pma_reset_pipe : signal is "TRUE"' in resets
 assert re.search(r'core_resets_i.*?reset\s*=>\s*reset.*?independent_clock_bufg\s*=>\s*independent_clock',wrapper,re.S)
 assert 'process(clk, rstIn)' in timer and "if(rstIn = '1') then" in timer
 if candidate=='f401':assert 'pwr_on_reset or ((not pcs_wait) and pcs_wait_end)' in top
 else:assert 'raw_pwr_on_reset or ((not pcs_wait) and pwr_on_reset)' in top
 cases.append({'candidate':candidate,'SYS_timer_clock':'Independent board BASE_CLK -> clk_wiz_sys -> clk_sys125MHz','GT_independent_clock':'Same SYS clock wizard -> clk_gbe200MHz','feedback_from_RX_recovered_clock':False,'public_reset_CDC':'Existing four-stage ASYNC_REG PMA reset pipeline, async assert and independent-clock synchronous release','initial_POR_dependency':'SYS clock wizard lock, not Ethernet link/MMCM lock','late_recovery':False})
sources[str(Path(__file__))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
r={'created':datetime.datetime.now().isoformat(),'phase':'static_clock_reset_dependencies_checked_fresh_physical_audit_still_required','cases':cases,'source_sha256':sources,'limits':['Source path audit only; physical clock nets must be checked after implementation.','No new crossing outside the pre-existing public core asynchronous reset interface. Existing vendor reset crossings/constraints remain.','No claim to validate analog PLL/CDR behavior or external TDC performance.']}
out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase']}))
