"""Read-only fresh routed DCP inspection, isolated from hardware programming."""
import argparse,datetime,hashlib,json,subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--candidate',choices=['f401','f402'],required=True);a=ap.parse_args();tag='outerreset-'+a.candidate
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=Path(tag+'-base-review.json');b=json.loads(base.read_text());assert b['phase']=='base_review_passed_fresh_routed_netlist_review_required'
for p,h in b['source_sha256'].items():assert sha(p)==h
query="Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'vivado.exe' -and $_.CommandLine -match '-mode batch' } | Select-Object -ExpandProperty ProcessId | ConvertTo-Json -Compress"
assert not subprocess.check_output(['powershell.exe','-NoProfile','-Command',query],text=True).strip()
out=Path(tag+'-inspection.json');assert not out.exists();tcl=Path('inspect-'+tag+'.tcl');dcp=Path('lrtdc-'+tag)/'build'/tag/('lrtdc-'+tag+'.dcp');textout=Path(tag+'-netlist-inspection.txt');assert not textout.exists()
sources={str(p):sha(p) for p in [Path(__file__),base,tcl,dcp]};r={'started':datetime.datetime.now().isoformat(),'phase':'offline_fresh_netlist_inspection_active','hardware_operations':False,'source_sha256':sources};out.write_text(json.dumps(r,indent=2))
try:
 with Path(tag+'-inspection.console.txt').open('xb') as stream:c=subprocess.run([r'C:\Xilinx\Vivado\2023.2\bin\vivado.bat','-mode','batch','-source',str(tcl),'-log',tag+'-inspection.log','-journal',tag+'-inspection.jou'],stdout=stream,stderr=subprocess.STDOUT,creationflags=0x08000000)
 r['actual_exit_code']=c.returncode;assert c.returncode==0;assert all(sha(p)==h for p,h in sources.items());assert textout.stat().st_size>0
 r.update(phase='fresh_netlist_inspected_manual_configuration_required',inspection_text=str(textout),inspection_text_sha256=sha(textout))
except BaseException as e:r.update(phase='STOPPED_NEEDS_INSPECTION',error=type(e).__name__+':'+str(e));raise
finally:r['finished']=datetime.datetime.now().isoformat();out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase']}),flush=True)
