"""Read-only two-board soak after full, verified restoration."""
import argparse,datetime,hashlib,json,time
from pathlib import Path
import outerreset_hw_guard_v2
import network_boot_stress as n
out=Path('outerreset-final-soak-summary.json');assert not out.exists()
parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=int,default=600);args=parser.parse_args();assert 60<=args.seconds<=1800 and args.seconds%30==0
restore=Path('outerreset-restoration.json');r=json.loads(restore.read_text());assert r['phase']=='both_restored_full_readback_cold3_network_EEPROM_verified_power_on'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
sources={str(p):sha(p) for p in [Path(__file__),restore,Path('outerreset_hw_guard_v2.py'),Path('network_boot_stress.py'),Path('boot_test.py')]}
versions={'192.168.10.16':0x60c4f202,'192.168.10.17':0x60c4020a}
result={'started':datetime.datetime.now().isoformat(),'source_sha256':sources,'requested_seconds':args.seconds,'phase':'read_only_soak_active','samples':[],'counts':{h:{'RBCP_checks':0,'RBCP_pass':0,'TCP_checks':0,'TCP_pass':0,'failures':0} for h in versions},'limits':['Read-only control/TCP checks; no automatic recovery or power/reset/program/EEPROM writes.','Not a TDC external-input performance or calibration test.']}
def save():out.write_text(json.dumps(result,indent=2))
start=time.monotonic();save()
try:
 for index in range(args.seconds//30):
  outerreset_hw_guard_v2.assert_exclusive()
  assert all(sha(p)==h for p,h in sources.items())
  tcp=index%10==0
  for host,version in versions.items():
   n.HOST=host;v=n.validate(version,tcp=tcp);c=result['counts'][host]
   c['RBCP_checks']+=1;c['RBCP_pass']+=int(v['rbcp'] is True);c['failures']+=int(not v['success'])
   if tcp:c['TCP_checks']+=1;c['TCP_pass']+=int(v['tcp24'] is True)
   result['samples'].append({'time':datetime.datetime.now().isoformat(),'host':host,'elapsed_seconds':round(time.monotonic()-start,3),'tcp_requested':tcp,'result':v});save()
   assert v['success'],'Failure preserved; no automatic recovery'
  target=start+(index+1)*30
  while time.monotonic()<target:time.sleep(min(1,max(0,target-time.monotonic())))
 result.update(phase='read_only_soak_completed_both_healthy',finished=datetime.datetime.now().isoformat(),elapsed_seconds=round(time.monotonic()-start,3));save();print(json.dumps({'phase':result['phase'],'counts':result['counts']}),flush=True)
except BaseException as e:result.update(phase='STOPPED_NEEDS_INSPECTION',error=type(e).__name__+':'+str(e));save();raise
