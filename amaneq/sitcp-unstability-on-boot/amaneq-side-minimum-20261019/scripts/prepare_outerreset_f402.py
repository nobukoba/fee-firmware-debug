"""Further minimization experiment: reuse the existing global POR timer as window end."""
import datetime,difflib,hashlib,json,re,shutil,subprocess
from pathlib import Path
repo=Path('lrtdc-outerreset-f402');assert not repo.exists()
base='5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039'
subprocess.run(['git','clone','--shared','--no-hardlinks','lrtdc-startup-fix',str(repo)],check=True,capture_output=True)
subprocess.run(['git','-C',str(repo),'checkout','--detach',base],check=True,capture_output=True)
for name in ['utility','common','strtdc','mikumari','laccp','bbt-sitcp-core']:
 shutil.copytree(Path('lrtdc-minimal-inithold/hdl')/name,repo/'hdl'/name,ignore=shutil.ignore_patterns('.git'),dirs_exist_ok=True)
p=repo/'hdl/toplevel.vhd';before=p.read_text();anchor='  signal pcs_pma_status       : std_logic_vector(15 downto 0);';assert before.count(anchor)==1
after=before.replace(anchor,anchor+'\n  signal pcs_wait : std_logic;')
anchor='  -- SFP transceiver -------------------------------------------------------------------\n';assert after.count(anchor)==1
control='''  -- Reuse the global POR timer: release PCS, then reset again from 1s until POR ends.
  u_PcsWait : entity mylib.RstDelayTimer
    port map(raw_pwr_on_reset, std_logic_vector(to_unsigned(125000000, 32)), clk_sys, open, pcs_wait);

'''
after=after.replace(anchor,control+anchor)
old='        reset                => pwr_on_reset';assert after.count(old)==1
after=after.replace(old,'        reset                => raw_pwr_on_reset or ((not pcs_wait) and pwr_on_reset)');p.write_text(after)
p=repo/'hdl/defBusAddressMap.vhd';s=p.read_text();assert len(re.findall('60c4020a',s,re.I))==1;p.write_text(re.sub('60c4020a','60C4F402',s,flags=re.I))
folder=repo/'patch-check';folder.mkdir();(folder/'toplevel-before.vhd').write_text(before);(folder/'toplevel-after.vhd').write_text(after)
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/hdl/toplevel.vhd',tofile='b/hdl/toplevel.vhd'));pp=Path('outerreset-functional-f402.patch');assert not pp.exists();pp.write_bytes(patch.encode())
build=Path('lrtdc-outerreset-f401/build-outerreset-f401.tcl').read_text().replace('outerreset-f401','outerreset-f402').replace('60c4f401','60c4f402').replace('Y:/lrtdc-longhold-f310/build/longhold-f310/lrtdc-longhold-f310.dcp','Y:/lrtdc-outerreset-f401/build/outerreset-f401/lrtdc-outerreset-f401.dcp')
(repo/'build-outerreset-f402.tcl').write_text(build)
added=sum(x.startswith('+') and not x.startswith('+++') for x in patch.splitlines());deleted=sum(x.startswith('-') and not x.startswith('---') for x in patch.splitlines());assert (added,deleted)==(6,1)
files=[Path(__file__),repo/'hdl/toplevel.vhd',p,pp,folder/'toplevel-before.vhd',folder/'toplevel-after.vhd',repo/'build-outerreset-f402.tcl',repo/'hdl/common/main/RstDelayTimer.vhd']
r={'created':datetime.datetime.now().isoformat(),'phase':'source_prepared_not_built_or_hardware_tested','base_commit':base,'repo':str(repo),'runtime':'0x60C4F402','functional_added_lines':added,'functional_deleted_lines':deleted,'new_HDL_modules':0,'existing_timer_instances_added':1,'SYS_clock_MHz':125,'new_preset':125000000,'existing_global_POR_preset':268435455,'nominal_second_reset_seconds':(268435455-125000000)/125000000,'hypothesis':'Early PCS release followed by one delayed reset while global SiTCP POR still asserted. Reuse existing global POR endpoint, remove second timer and reset-assignment signal.','limits':['Not yet simulated/built/tested. Does not establish efficacy.','Initial public PCS reset releases before original global POR, so native GT startup may begin earlier; matched comparison must preserve raw/global POR drivers explicitly.','No recovery for late failure. Additional reset ends at original global POR end.','Added lines include a comment and blank line; independent version/build files excluded.'],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
Path('outerreset-f402-preparation.json').write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase'],'added':added,'deleted':deleted}))
