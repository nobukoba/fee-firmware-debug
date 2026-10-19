"""Independent one-line source candidate; reuse already qualified, identical IP products."""
import datetime,difflib,hashlib,json,re,shutil,subprocess
from pathlib import Path
repo=Path('lrtdc-outerreset-f403');assert not repo.exists()
base='5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039'
subprocess.run(['git','clone','--shared','--no-hardlinks','lrtdc-startup-fix',str(repo)],check=True,capture_output=True)
subprocess.run(['git','-C',str(repo),'checkout','--detach',base],check=True,capture_output=True)
for name in ['utility','common','strtdc','mikumari','laccp','bbt-sitcp-core']:
 shutil.copytree(Path('lrtdc-outerreset-f402/hdl')/name,repo/'hdl'/name,ignore=shutil.ignore_patterns('.git'),dirs_exist_ok=True)
p=repo/'hdl/toplevel.vhd';before=p.read_text();old='        reset                => pwr_on_reset';assert before.count(old)==1
after=before.replace(old,'        reset                => raw_pwr_on_reset');p.write_text(after)
v=repo/'hdl/defBusAddressMap.vhd';s=v.read_text();assert len(re.findall('60c4020a',s,re.I))==1;v.write_text(re.sub('60c4020a','60C4F403',s,flags=re.I))
folder=repo/'patch-check';folder.mkdir();(folder/'toplevel-before.vhd').write_text(before);(folder/'toplevel-after.vhd').write_text(after)
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/hdl/toplevel.vhd',tofile='b/hdl/toplevel.vhd'));pp=Path('outerreset-functional-f403.patch');assert not pp.exists();pp.write_bytes(patch.encode())
assert sum(x.startswith('+') and not x.startswith('+++') for x in patch.splitlines())==1
files=[Path(__file__),p,v,pp,folder/'toplevel-before.vhd',folder/'toplevel-after.vhd']
r={'created':datetime.datetime.now().isoformat(),'phase':'source_prepared_not_built_or_hardware_tested','base_commit':base,'repo':str(repo),'runtime':'0x60C4F403','functional_added_lines':1,'functional_deleted_lines':1,'new_HDL_modules':0,'existing_timer_instances_added':0,'hypothesis':'PCS reset follows raw SYS lock rather than delayed global POR; permits native Ethernet startup during SiTCP POR. No additional reset pulse or watchdog.','limits':['Diagnostic F402 early passed3/3 but retained unused timer; this independent source build must be separately qualified.','Fresh top synthesis/implementation, unchanged qualified IP OOC products reused through Vivado save_project_as.'],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
Path('outerreset-f403-preparation.json').write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase'],'added':1,'deleted':1}))
