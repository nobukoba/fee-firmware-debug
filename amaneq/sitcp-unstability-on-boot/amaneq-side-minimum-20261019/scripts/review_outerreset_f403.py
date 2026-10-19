"""Independent source/STA/DRC/native-IP and physical reset routing qualification."""
import datetime,difflib,hashlib,importlib.util,json,os,re,subprocess,sys,tempfile
from pathlib import Path
import flash_firmware
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
out=Path('outerreset-f403-independent-review.json');assert not out.exists()
bp=Path('outerreset-f403-build.json');b=load(bp);assert b['phase']=='build_complete_independent_review_required' and b['actual_exit_code']==0
for p,h in {**b['source_sha256'],**b['artifacts']}.items():assert sha(p)==h,p
ip=Path('outerreset-f403-inspection.json');inspection=load(ip);assert inspection['actual_exit_code']==0
for p,h in inspection['source_sha256'].items():assert sha(p)==h,p
init=Path('outerreset-f403-timer-init-audit.json');assert load(init)['phase']=='physical_timer_counter_and_reset_output_initial_values_verified'
repo=Path('lrtdc-outerreset-f403');folder=repo/'build/outerreset-f403';files=[Path(__file__),bp,ip,init]
before=(repo/'patch-check/toplevel-before.vhd').read_text();after=(repo/'hdl/toplevel.vhd').read_text();old='        reset                => pwr_on_reset';assert before.count(old)==1 and after==before.replace(old,'        reset                => raw_pwr_on_reset')
patch=Path('outerreset-functional-f403.patch');assert patch.read_text()==''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/hdl/toplevel.vhd',tofile='b/hdl/toplevel.vhd'))
assert 'u_PcsWait' not in after
base='5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039'
assert subprocess.check_output(['git','-C',str(repo),'diff','--numstat',base,'--','hdl/toplevel.vhd'],text=True).split()[:2]==['1','1']
subprocess.run(['git','-C',str(repo),'diff','--check',base,'--','hdl/toplevel.vhd'],check=True,capture_output=True)
fd,tmp=tempfile.mkstemp(prefix='outerreset-f403-index-');os.close(fd);Path(tmp).unlink();env={**os.environ,'GIT_INDEX_FILE':tmp}
try:
 subprocess.run(['git','-C',str(repo),'read-tree',base],env=env,check=True,capture_output=True)
 subprocess.run(['git','-C',str(repo),'apply','--cached','--check',str(patch.resolve())],env=env,check=True,capture_output=True)
finally:
 if Path(tmp).exists():Path(tmp).unlink()
application=Path('outerreset-f403-patch-application-check.json');assert not application.exists();application.write_text(json.dumps({'phase':'patch_applies_to_clean_base_and_git_whitespace_passed','base':base,'git_added_lines':1,'git_deleted_lines':1,'source_sha256':{str(p):sha(p) for p in [Path(__file__),patch,repo/'hdl/toplevel.vhd']}}));files += [application,patch,repo/'hdl/toplevel.vhd',repo/'hdl/defBusAddressMap.vhd']
# Actual compile file list must contain new top and version, with every other HDL
# byte-identical to the pinned independent source checkout.
compiled=(folder/'compiled-files.txt').read_text().splitlines();seen=[];cached=[]
for name in compiled:
 p=Path(name).resolve();assert p.exists(),name;files.append(p)
 if p.suffix.lower()=='.dcp':
  assert sha(p) in set(b['source_sha256'].values()),'IP product differs from protected pre-build input:'+name
  cached.append(str(p))
 if '/hdl/' in name:
  rel=name.split('/hdl/',1)[1];q=repo/'hdl'/rel;assert p.read_bytes()==q.read_bytes(),name
  if rel in ['toplevel.vhd','defBusAddressMap.vhd']:assert name.startswith('K:/'),name;seen.append(rel)
assert sorted(seen)==['defBusAddressMap.vhd','toplevel.vhd']
assert len(cached)==15
generated=Path('lrtdc-outerreset-f402/ip/gig_ethernet_pcs_pma/synth');reference=Path('lrtdc-startdelay-f305/ip/gig_ethernet_pcs_pma/synth');core={}
for p in reference.rglob('*.vhd'):
 rel=p.relative_to(reference);q=generated/rel;ref=Path('lrtdc-minimal-inithold/build/minimal-inithold-f304/rx-startup-before-patch.vhd') if rel.name=='gig_ethernet_pcs_pma_rx_startup_fsm.vhd' else p
 assert q.read_text()==ref.read_text(),rel;core[str(rel)]=sha(q);files.append(q)
assert len(core)==13
for name in ['gig_ethernet_pcs_pma.xdc','gig_ethernet_pcs_pma_ooc.xdc']:
 assert (generated/name).read_text()==(reference/name).read_text();files.append(generated/name)
clockpath=Path('outerreset-f403-board-clock-audit.json');assert not clockpath.exists();clockpath.write_text(json.dumps({'phase':'generated_board_clock_settings_match_common_baseline','candidate':'f403','GT_reference_MHz':156.25,'GT_CPLL_FBDIV':4,'GT_CPLL_FBDIV_45':4,'compiled_generated_directory':str(generated),'qualified_IP_products_reused':True,'source_sha256':{str(p):sha(p) for p in [Path(__file__),*(generated/n for n in ['gig_ethernet_pcs_pma.xdc','gig_ethernet_pcs_pma_ooc.xdc'])]}}));files.append(clockpath)
timing=(folder/'timing-summary.rpt').read_text();assert 'All user specified timing constraints are met.' in timing
new_synth=repo/'build/StrLrTdcF403.runs/synth_1/runme.log';old_synth=Path('lrtdc-outerreset-f402/build/StrLrTdc.runs/synth_1/runme.log')
critical=lambda p:re.findall(r'^CRITICAL WARNING: ([^\n]+)',p.read_text(encoding='utf-8',errors='replace'),re.M)
assert sorted(critical(new_synth))==sorted(critical(old_synth)),'New synthesis critical warning requires review'
files.extend([new_synth,old_synth])
for name in ['no_clock','unconstrained_internal_endpoints','multiple_clock','loops']:assert re.search(r'checking '+name+r' \(0\)',timing)
vals=re.search(r'WNS\(ns\).*?\n\s*-+[^\n]*\n\s*([^\n]+)',timing,re.S).group(1).split();wns,whs=float(vals[0]),float(vals[4]);assert wns>=0 and whs>=0
skews=re.findall(r'Slack \((MET|VIOLATED)\)\s*:\s*(-?[\d.]+)ns',(folder/'bus-skew.rpt').read_text());assert skews and all(t=='MET' and float(v)>=0 for t,v in skews)
rows=re.findall(r'\|\s*([A-Z]+-\d+)\s*\|\s*(Warning|Critical Warning|Error)\s*\|[^|]*\|\s*(\d+)\s*\|',(folder/'drc.rpt').read_text());limits={'CHECK-3':1,'DPIP-1':384,'REQP-1839':12,'REQP-1840':20,'RTSTAT-10':1};assert rows
for name,severity,count in rows:assert severity=='Warning' and name in limits and int(count)<=limits[name],(name,severity,count)
audit=(folder/'fresh-clock-reset-audit.txt').read_text();sinks=re.findall(r'^PUBLIC_RESET_SINK (.*?) DRIVERS (.*?)$',audit,re.M);assert len(sinks)==4
assert len(set(driver for sink,driver in sinks))==1
for sink,driver in sinks:assert '/core_resets_i/pma_reset_pipe_reg[' in sink and sink.endswith('/PRE')
drivercells=re.findall(r'^DRIVER_CELL (.*?) REF (.*?) INIT (.*?)$',audit,re.M);assert len(drivercells)==4 and all(ref=='LUT1' and val=="2'h1" for cell,ref,val in drivercells),drivercells
inputs=re.findall(r'^DRIVER_INPUT (.*?) DRIVERS (.*?)$',audit,re.M);assert len(inputs)==4 and all(driver=='u_ClkMan_Inst/inst/mmcm_adv_inst/LOCKED' for pin,driver in inputs),inputs
for prop,value in [('CPLL_FBDIV',4),('CPLL_FBDIV_45',4),('CPLL_REFCLK_DIV',1),('RXOUT_DIV',4),('TXOUT_DIV',4)]:assert f'GT {prop} {value}\n' in audit
extra=(folder/'fresh-clock-reset-extra.txt').read_text();assert 'clk_sys 8.000' in extra and 'GLOBAL_TIMER_CLOCK_DRIVER u_ClkMan_Inst/inst/clkout1_buf/O' in extra
stages=re.findall(r'^RESET_SYNC_STAGE (.*?) ASYNC_REG (.*?)$',extra,re.M);assert len(stages)==4 and all(value.upper() in ['TRUE','1'] for cell,value in stages)
syncclocks=re.findall(r'^RESET_SYNC_CLOCK (.*?) (\S+) ([\d.]+)$',extra,re.M);assert len(syncclocks)==4 and all(clock=='clk_indep' and float(period)==5.0 for pin,clock,period in syncclocks)
for prop,value in [('CPLL_FBDIV',4),('CPLL_FBDIV_45',4),('CPLL_REFCLK_DIV',1),('RXOUT_DIV',4),('TXOUT_DIV',4)]:assert f'PCS_GT_PROPERTY {prop} {value}\n' in extra
for pin in ['RXPMARESET','RXCDRHOLD','RXSYSCLKSEL[0]','RXSYSCLKSEL[1]','TXSYSCLKSEL[0]','TXSYSCLKSEL[1]']:assert re.search(r'^PCS_GT_PIN '+re.escape(pin)+r' NET .*<const0>$',extra,re.M)
assert 'MGT_RESET.SYNC_ASYNC_RESET/reset_sync1/PRE' in extra and 'tx_elastic_buffer_inst/gen_rd_reset/reset_sync1/PRE' in extra
files += [folder/n for n in ['compiled-files.txt','reused-ip-runs.txt','timing-summary.rpt','bus-skew.rpt','drc.rpt','fresh-clock-reset-audit.txt','fresh-clock-reset-extra.txt']]
spec=importlib.util.spec_from_file_location('outerreset_f403_inspector',flash_firmware.INSPECTOR);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
mcs=folder/'lrtdc-outerreset-f403.mcs';image=module.inspect_file(mcs);assert image.payload==module.inspect_file(folder/'lrtdc-outerreset-f403.bit').payload and image.idcode&0xfffffff==0x0364c093
v={'mcs':str(mcs),'mcs_sha256':sha(mcs),'expected_full_flash_sha256':hashlib.sha256(image.payload.ljust(16777216,b'\xff')).hexdigest(),'wns_ns':wns,'whs_ns':whs,'drc':rows}
r={'created':datetime.datetime.now().isoformat(),'phase':'independent_review_passed_ready_for_hardware','runtime':'0x60C4F403','functional_added_lines':1,'functional_deleted_lines':1,'variants':{'enabled':v},'core_VHDL_sha256':core,'source_sha256':{str(p):sha(p) for p in files},'limits':['Independent source-built single existing-line reset route change; no extra timer, no forced PMA pulse, no late-fault watchdog.','Unchanged native IP OOC products reused; top synthesis and implementation rerun with incremental reference allowed.','F402 matched early/bypass isolates timing; F403 is separately built and physically implemented. No claim of identical route between F403 and factory.','No analog power/clock waveform measured; no external-input TDC calibration test.']}
r['qualified_IP_DCP_inputs']={p:sha(p) for p in cached}
out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase'],'wns':wns,'whs':whs}))
