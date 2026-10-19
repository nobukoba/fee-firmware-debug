"""Clean upstream source: AMANEQ top-level-only delayed one-shot reset."""
import datetime,difflib,hashlib,json,re,shutil,subprocess
from pathlib import Path
repo=Path('lrtdc-outerreset-f401');assert not repo.exists() and not Path('I:/').exists()
base='5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039'
subprocess.run(['git','clone','--shared','--no-hardlinks','lrtdc-startup-fix',str(repo)],check=True,capture_output=True)
subprocess.run(['git','-C',str(repo),'checkout','--detach',base],check=True,capture_output=True)
for name in ['utility','common','strtdc','mikumari','laccp','bbt-sitcp-core']:
 shutil.copytree(Path('lrtdc-minimal-inithold/hdl')/name,repo/'hdl'/name,ignore=shutil.ignore_patterns('.git'),dirs_exist_ok=True)
p=repo/'hdl/toplevel.vhd';before=p.read_text();assert 'EthernetPcsStartupRecovery' not in before
anchor='  signal pcs_pma_status       : std_logic_vector(15 downto 0);';assert before.count(anchor)==1
after=before.replace(anchor,anchor+'\n  signal pcs_wait, pcs_wait_end, pcs_reset_once : std_logic;')
anchor='  -- SFP transceiver -------------------------------------------------------------------\n';assert after.count(anchor)==1
control='''  -- clk_sys=125MHz: after pwr_on_reset, wait1s then reset Ethernet for100ms once.
  u_PcsWait : entity mylib.RstDelayTimer
    port map(pwr_on_reset, std_logic_vector(to_unsigned(125000000, 32)), clk_sys, open, pcs_wait);
  u_PcsWaitEnd : entity mylib.RstDelayTimer
    port map(pwr_on_reset, std_logic_vector(to_unsigned(137500000, 32)), clk_sys, open, pcs_wait_end);
  pcs_reset_once <= pwr_on_reset or ((not pcs_wait) and pcs_wait_end);

'''
after=after.replace(anchor,control+anchor)
old='        reset                => pwr_on_reset';assert after.count(old)==1
after=after.replace(old,'        reset                => pcs_reset_once');p.write_text(after)
p=repo/'hdl/defBusAddressMap.vhd';s=p.read_text();assert len(re.findall('60c4020a',s,re.I))==1;p.write_text(re.sub('60c4020a','60C4F401',s,flags=re.I))
folder=repo/'patch-check';folder.mkdir();(folder/'toplevel-before.vhd').write_text(before);(folder/'toplevel-after.vhd').write_text(after)
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/hdl/toplevel.vhd',tofile='b/hdl/toplevel.vhd'))
pp=Path('outerreset-functional-f401.patch');assert not pp.exists();pp.write_bytes(patch.encode())
build=Path('lrtdc-longhold-f310/build-longhold-f310.tcl').read_text()
build=build.replace('# Candidate functional change is applied by patch-rx-longhold.tcl after generation.','# AMANEQ top-level-only one-shot reset. Native RX FSM is not patched.')
build=build.replace('longhold-f310','outerreset-f401').replace('60c4f310','60c4f401')
build=build.replace('source patch-rx-longhold.tcl\n','')
build=re.sub(r'^    apply_rx_longhold_patch[^\n]*\n','',build,flags=re.M)
build=build.replace('K:/build/clockhold-f30c/lrtdc-clockhold-f30c.dcp','Y:/lrtdc-longhold-f310/build/longhold-f310/lrtdc-longhold-f310.dcp')
assert 'apply_rx_' not in build and 'patch-rx' not in build
(repo/'build-outerreset-f401.tcl').write_text(build)
added=sum(x.startswith('+') and not x.startswith('+++') for x in patch.splitlines());deleted=sum(x.startswith('-') and not x.startswith('---') for x in patch.splitlines())
files=[Path(__file__),p,pp,folder/'toplevel-before.vhd',folder/'toplevel-after.vhd',repo/'build-outerreset-f401.tcl',repo/'hdl/common/main/RstDelayTimer.vhd',Path('outerreset-initial-status.json')]
report={'created':datetime.datetime.now().isoformat(),'phase':'source_prepared_not_built','base_commit':base,'repo':str(repo),'runtime':'0x60C4F401','functional_patch':str(pp),'functional_added_lines':added,'functional_deleted_lines':deleted,'functional_files':['hdl/toplevel.vhd'],'new_HDL_modules':0,'existing_timer_instances_added':2,'SYS_clock_MHz':125,'delay_cycles':125000000,'pulse_cycles':12500000,'first_timer_preset':125000000,'second_timer_preset':137500000,'baseline':'Native factory RX FSM; no generated IP functional edits. ExistingAMANEQ156.25MHz CPLL andXDC corrections retained.','hypothesis':'After initial pwr_on_reset release, allow1s ofEthernet startup then usepublicreset for100ms once. ReuseexistingRstDelayTimer. No conditionalretry,linkqualification ornewFSM.','limits':['No hardwareverificationyet. Publicreset reinitializesPCS/PMA andisnot identicaltoGTXPMA-onlypulse.','Timer output falls afterN+1 SYSedges; pulsewidth exactlydifferenceofpresets (12,500,000cycles).','pwr_on_reset reassertion re-armsboth timers. No recovery forlatefailures afterone-shot.','Linecount includesreadablecomment/blankline; versionID/buildautomation excluded.'],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
Path('outerreset-f401-preparation.json').write_text(json.dumps(report,indent=2));print(json.dumps({'phase':report['phase'],'added':added,'deleted':deleted}))
