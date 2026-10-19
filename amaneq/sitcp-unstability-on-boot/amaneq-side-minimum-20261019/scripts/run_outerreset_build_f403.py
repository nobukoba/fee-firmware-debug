"""Fresh one-line top build; preserve and hash unchanged qualified IP inputs."""
import datetime,hashlib,json,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=Path('outerreset-f403-preparation.json');r0=json.loads(prep.read_text());repo=Path(r0['repo'])
query="Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'vivado.exe' -and $_.CommandLine -match '-mode batch' } | Select-Object -ExpandProperty ProcessId | ConvertTo-Json -Compress"
assert not subprocess.check_output(['powershell.exe','-NoProfile','-Command',query],text=True).strip()
assert not Path('K:/').exists();subprocess.run(['subst','K:',str(repo.resolve())],check=True,capture_output=True)
script=Path('build-outerreset-f403.tcl');target=repo/'build-outerreset-f403.tcl';target.write_bytes(script.read_bytes())
original=Path('lrtdc-outerreset-f402');protected=list((original/'ip').rglob('*.vhd'))+list((original/'ip').rglob('*.xdc'))+[original/'hdl/toplevel.vhd',original/'hdl/defBusAddressMap.vhd',original/'build/StrLrTdc.xpr']
protected += [p for p in (original/'build/StrLrTdc.runs').glob('*/*.dcp') if p.parent.name not in ['synth_1','impl_1']]
sources={**r0['source_sha256'],**{str(p):sha(p) for p in [Path(__file__),prep,script,target,*protected]}}
assert all(sha(p)==h for p,h in sources.items());out=Path('outerreset-f403-build.json');assert not out.exists()
r={'started':datetime.datetime.now().isoformat(),'phase':'offline_fresh_top_source_build_reusing_identical_qualified_IP','hardware_operations':False,'source_sha256':sources};out.write_text(json.dumps(r,indent=2))
try:
 with Path('outerreset-f403-build.console.txt').open('xb') as stream:
  c=subprocess.run([r'C:\Xilinx\Vivado\2023.2\bin\vivado.bat','-mode','batch','-source',str(script.resolve()),'-log','outerreset-f403-build.log','-journal','outerreset-f403-build.jou'],stdout=stream,stderr=subprocess.STDOUT,creationflags=0x08000000)
 r['actual_exit_code']=c.returncode;assert c.returncode==0;assert all(sha(p)==h for p,h in sources.items())
 r['artifacts']={str(p):sha(p) for p in (repo/'build/outerreset-f403').iterdir() if p.is_file()};r['phase']='build_complete_independent_review_required'
except BaseException as e:r.update(phase='STOPPED_NEEDS_INSPECTION',error=type(e).__name__+':'+str(e));raise
finally:r['finished']=datetime.datetime.now().isoformat();out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase']}),flush=True)
