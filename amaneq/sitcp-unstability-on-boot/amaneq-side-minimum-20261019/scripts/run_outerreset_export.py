"""Offline matched image export, after independent base and fresh netlist review."""
import argparse,datetime,hashlib,json,subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--candidate',choices=['f401','f402'],required=True);a=ap.parse_args();tag='outerreset-'+a.candidate
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=Path(tag+'-base-review.json');r=json.loads(base.read_text());assert r['phase']=='base_review_passed_fresh_routed_netlist_review_required'
cfgpath=Path(tag+'-netlist-config.json');cfg=json.loads(cfgpath.read_text());assert cfg['phase']=='fresh_netlist_configuration_reviewed' and cfg['candidate']==a.candidate
for p,h in {**r['source_sha256'],**cfg['source_sha256']}.items():assert sha(p)==h,p
out=Path(tag+'-export.json');assert not out.exists()
query="Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'vivado.exe' -and $_.CommandLine -match '-mode batch' } | Select-Object -ExpandProperty ProcessId | ConvertTo-Json -Compress"
assert not subprocess.check_output(['powershell.exe','-NoProfile','-Command',query],text=True).strip()
files=[Path(__file__),base,cfgpath,Path(tag+'-netlist-config.tcl'),Path('export-outerreset-matched.tcl'),Path('deepreset_column_audit.tcl'),Path(cfg['dcp'])]
sources={str(p):sha(p) for p in files};report={'started':datetime.datetime.now().isoformat(),'phase':'offline_matched_export_active','hardware_operations':False,'source_sha256':sources};out.write_text(json.dumps(report,indent=2))
try:
 with Path(tag+'-export.console.txt').open('xb') as stream:c=subprocess.run([r'C:\Xilinx\Vivado\2023.2\bin\vivado.bat','-mode','batch','-source','export-outerreset-matched.tcl','-log',tag+'-export.log','-journal',tag+'-export.jou','-tclargs',tag+'-netlist-config.tcl'],stdout=stream,stderr=subprocess.STDOUT,creationflags=0x08000000)
 report['actual_exit_code']=c.returncode;assert c.returncode==0;assert all(sha(p)==h for p,h in sources.items())
 report['artifacts']={str(p):sha(p) for p in Path(cfg['root']).rglob('*') if p.is_file()};report['phase']='matched_export_complete_independent_review_required'
except BaseException as e:report.update(phase='STOPPED_NEEDS_INSPECTION',error=type(e).__name__+':'+str(e));raise
finally:report['finished']=datetime.datetime.now().isoformat();out.write_text(json.dumps(report,indent=2));print(json.dumps({'phase':report['phase']}),flush=True)
