"""Owned by run_outerreset_cohort; target power only, restore ON even on OFF-check error."""
import argparse,datetime,hashlib,json,time
from pathlib import Path
import boot_test as b
import network_boot_stress as n
import deepreset_fresh_wait,deepreset_fresh_wait_v2
ap=argparse.ArgumentParser();ap.add_argument('--host',choices=['192.168.10.16','192.168.10.17'],required=True);ap.add_argument('--version',type=lambda x:int(x,0),required=True);ap.add_argument('--log',type=Path,required=True);ap.add_argument('--off-schedule',default='5');ap.add_argument('--repeat',type=int,default=3);ap.add_argument('--early',action='store_true');a=ap.parse_args()
schedule=[int(x) for x in a.off_schedule.split(',')]*a.repeat;assert 1<=len(schedule)<=50 and all(x in [5,30,120,600] for x in schedule);assert not a.log.exists()
sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in map(Path,[__file__,'boot_test.py','network_boot_stress.py','deepreset_neighbor.py','deepreset_fresh_wait.py','deepreset_fresh_wait_v2.py'])}
b.LOG=a.log;b.report={'started':datetime.datetime.now().isoformat(),'host':a.host,'expected_version':hex(a.version),'source_sha256':sources,'neighbor_protocol':'early targeted resolution' if a.early else '12s quiet then targeted resolution','topology':'Kikusui16;ezOutlet17;switchalwaysON;noEEPROM/setpointwrites','events':[],'trials':[]}
n.HOST=a.host;control=b.power if a.host.endswith('.16') else lambda state=None:b.outlet(None if state is None else ('ON' if state else 'OFF'))
assert b.outlet().upper()=='ON';p=b.power();assert p['output'] in ('1','ON') and abs(float(p['voltage_set'])-30)<.01 and abs(float(p['current_set'])-1)<.01
wait=deepreset_fresh_wait_v2.wait_ready if a.early else deepreset_fresh_wait.wait_ready
for index,seconds in enumerate(schedule,1):
 assert not Path('outerreset-stop-experiments').exists()
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in sources.items())
 b.event('cold_start',number=index,off_seconds=seconds);off_start=time.monotonic()
 try:
  control(0);off_start=time.monotonic()
  while time.monotonic()-off_start<seconds and not Path('outerreset-stop-experiments').exists():time.sleep(min(1,max(0,seconds-(time.monotonic()-off_start))))
  absence=n.validate(a.version,tcp=False);b.event('off_absence',**absence)
 finally:control(1);b.event('power_on',number=index,actual_off_seconds=round(time.monotonic()-off_start,3))
 assert not absence['rbcp'],'Selected board still responds while powerOFF'
 assert not Path('outerreset-stop-experiments').exists(),'Stop requested; powerrestoredON'
 ok,samples=wait(a.version,90);first=next((s['elapsed_seconds'] for s in samples if s['success']),None)
 b.report['trials'].append({'number':index,'off_seconds':seconds,'success':ok,'first_ready_seconds':first,'samples':samples});b.event('cold_result',number=index,success=ok,first_ready_seconds=first)
b.event('complete_power_on',successes=sum(t['success'] for t in b.report['trials']),trials=len(schedule))
