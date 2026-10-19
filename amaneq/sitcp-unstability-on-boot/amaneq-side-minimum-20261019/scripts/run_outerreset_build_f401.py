"""Full source offline build. Hardware programming requires separate review."""
import datetime,hashlib,json,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prep=Path('outerreset-f401-preparation.json');r0=json.loads(prep.read_text());sim=Path('experiments/outerreset-f401-sim/result.json');s=json.loads(sim.read_text());assert s['passed']
repo=Path(r0['repo']);ref=Path('lrtdc-longhold-f310/build/longhold-f310/lrtdc-longhold-f310.dcp')
sources={**r0['source_sha256'],**s['source_sha256'],**{str(p):sha(p) for p in [Path(__file__),prep,sim,ref]}}
assert all(sha(p)==h for p,h in sources.items())
query="Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'vivado.exe' -and $_.CommandLine -match '-mode batch' } | Select-Object -ExpandProperty ProcessId | ConvertTo-Json -Compress"
assert not subprocess.check_output(['powershell.exe','-NoProfile','-Command',query],text=True).strip()
assert not Path('I:/').exists();subprocess.run(['subst','I:',str(repo.resolve())],check=True,capture_output=True)
out=Path('outerreset-f401-build.json');assert not out.exists();report={'started':datetime.datetime.now().isoformat(),'phase':'offline_full_source_build','hardware_operations':False,'source_sha256':sources};out.write_text(json.dumps(report,indent=2))
try:
 with Path('outerreset-f401-build.console.txt').open('xb') as stream:c=subprocess.run([r'C:\Xilinx\Vivado\2023.2\bin\vivado.bat','-mode','batch','-source','build-outerreset-f401.tcl','-log','outerreset-f401-build.log','-journal','outerreset-f401-build.jou'],cwd='I:/',stdout=stream,stderr=subprocess.STDOUT,creationflags=0x08000000)
 report['actual_exit_code']=c.returncode;assert c.returncode==0;assert all(sha(p)==h for p,h in sources.items())
 report['artifacts']={str(p):sha(p) for p in (repo/'build/outerreset-f401').iterdir() if p.is_file()};report['phase']='build_complete_independent_review_required'
except BaseException as e:report.update(phase='STOPPED_NEEDS_INSPECTION',error=type(e).__name__+':'+str(e));raise
finally:report['finished']=datetime.datetime.now().isoformat();out.write_text(json.dumps(report,indent=2));print(json.dumps({'phase':report['phase']}),flush=True)
