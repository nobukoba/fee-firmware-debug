import datetime,hashlib,json,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=Path('outerreset-f403-build.json');r=json.loads(b.read_text());assert r['phase']=='build_complete_independent_review_required' and r['actual_exit_code']==0
for p,h in {**r['source_sha256'],**r['artifacts']}.items():assert sha(p)==h,p
out=Path('outerreset-f403-inspection.json');assert not out.exists();t=Path('inspect-outerreset-f403.tcl')
with Path('outerreset-f403-inspection.console.txt').open('xb') as stream:
 c=subprocess.run([r'C:\Xilinx\Vivado\2023.2\bin\vivado.bat','-mode','batch','-source',str(t),'-log','outerreset-f403-inspection.log','-journal','outerreset-f403-inspection.jou'],stdout=stream,stderr=subprocess.STDOUT,creationflags=0x08000000)
assert c.returncode==0
out.write_text(json.dumps({'created':datetime.datetime.now().isoformat(),'phase':'fresh_physical_reset_clock_and_counter_export_complete','actual_exit_code':c.returncode,'source_sha256':{str(p):sha(p) for p in [Path(__file__),b,t,Path('lrtdc-outerreset-f403/build/outerreset-f403/lrtdc-outerreset-f403.dcp')]}}))
print('F403 independent physical inspection exported')
