"""Read-only candidate soak under the same single hardware-owner exclusion."""
import argparse,datetime,hashlib,json,time
from pathlib import Path
import outerreset_hw_guard_v2
import network_boot_stress as n
ap=argparse.ArgumentParser();ap.add_argument('--proof16',type=Path,required=True);ap.add_argument('--proof17',type=Path,required=True);ap.add_argument('--label',required=True);ap.add_argument('--seconds',type=int,default=900);a=ap.parse_args();assert a.label.replace('-','').isalnum() and len(a.label)<=24 and 60<=a.seconds<=3600 and a.seconds%30==0
out=Path('outerreset-soak-'+a.label+'.json');assert not out.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
versions={};proofs={}
for suffix,p in [('16',a.proof16),('17',a.proof17)]:
 r=json.loads(p.read_text());host='192.168.10.'+suffix;assert r['host']==host and r['phase']=='cohort_complete_power_on' and r['successes']==len(r['trials'])>0
 assert sha(r['cold_log'])==r['cold_sha256'] and sha(r['flash_report'])==r['flash_report_sha256'];versions[host]=int(r['runtime'],0);proofs[host]=str(p)
sources={str(p):sha(p) for p in [Path(__file__),a.proof16,a.proof17,*map(Path,['outerreset_hw_guard_v2.py','network_boot_stress.py','boot_test.py','eeprom-before-startup.bin','eeprom-dual17-before.bin'])]}
r={'started':datetime.datetime.now().isoformat(),'phase':'read_only_candidate_soak_active','requested_seconds':a.seconds,'proofs':proofs,'versions':{k:hex(v) for k,v in versions.items()},'source_sha256':sources,'samples':[],'counts':{h:{'RBCP_checks':0,'RBCP_pass':0,'TCP_checks':0,'TCP_pass':0,'failures':0} for h in versions},'limits':['No power/reset/program/setpoint/EEPROM writes and no automatic recovery.','Endpoint/EEPROM soak, not external-input TDC performance validation.','Last programmed variant is established by serialized cohort history, not runtime version alone.']}
def save():out.write_text(json.dumps(r,indent=2))
def guard():outerreset_hw_guard_v2.assert_exclusive();assert all(sha(p)==h for p,h in sources.items())
def eeprom_checks():
 result={}
 for host in versions:
  n.HOST=host;v=n.rbcp_read(0xfffffc00,128,79);p=Path('eeprom-before-startup.bin' if host.endswith('.16') else 'eeprom-dual17-before.bin');assert v==p.read_bytes();result[host]=hashlib.sha256(v).hexdigest()
 return result
start=time.monotonic();save()
try:
 guard();r['EEPROM_start_sha256']=eeprom_checks();save()
 for index in range(a.seconds//30):
  guard();assert not Path('outerreset-stop-experiments').exists();tcp=index%10==0
  for host,version in versions.items():
   n.HOST=host;v=n.validate(version,tcp=tcp);c=r['counts'][host];c['RBCP_checks']+=1;c['RBCP_pass']+=int(v['rbcp'] is True);c['failures']+=int(not v['success'])
   if tcp:c['TCP_checks']+=1;c['TCP_pass']+=int(v['tcp24'] is True)
   r['samples'].append({'time':datetime.datetime.now().isoformat(),'host':host,'elapsed_seconds':round(time.monotonic()-start,3),'tcp_requested':tcp,'result':v});save();assert v['success'],'Failure preserved; no recovery'
  target=start+(index+1)*30
  while time.monotonic()<target:time.sleep(min(1,max(0,target-time.monotonic())));assert not Path('outerreset-stop-experiments').exists()
 guard();r['EEPROM_end_sha256']=eeprom_checks();r.update(phase='read_only_candidate_soak_completed_both_healthy',finished=datetime.datetime.now().isoformat(),elapsed_seconds=round(time.monotonic()-start,3));save();print(json.dumps({'phase':r['phase'],'counts':r['counts']}),flush=True)
except BaseException as e:r.update(phase='STOPPED_NEEDS_INSPECTION',error=type(e).__name__+':'+str(e));save();raise
