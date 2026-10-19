import argparse,datetime,hashlib,json,subprocess,sys
from pathlib import Path
import outerreset_hw_guard_v2
ap=argparse.ArgumentParser();ap.add_argument('--host',choices=['192.168.10.16','192.168.10.17'],required=True);ap.add_argument('--candidate',choices=['factory','f401','f402','f403'],required=True);ap.add_argument('--variant',choices=['enabled','bypass','early','hold'],default='enabled');ap.add_argument('--label',required=True);ap.add_argument('--count',type=int,default=3);ap.add_argument('--off-schedule',default='5');ap.add_argument('--early',action='store_true');ap.add_argument('--existing-flash-report',type=Path);a=ap.parse_args();assert a.label.replace('-','').isalnum() and len(a.label)<=20 and 1<=a.count<=30
out=Path('outerreset-cohort-'+a.label+'.json');assert not out.exists();serial={'192.168.10.16':'210299BBCDDA','192.168.10.17':'210299BDCF8E'}[a.host]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
if a.candidate=='factory':
 assert a.variant=='enabled';v={'runtime':'0x60C4020A','mcs':'factory-v2a-backup/factory-v2a.mcs','mcs_sha256':'b1010ec6dc37e7223758d544ce9f30aa30549c29acfd9146675b3a7f17a6c2c0','expected_full_flash_sha256':'7dd784de31ff8b3b2cbae4602274faf3e2f587f1bc2185a89ad3ba5e7de48a13'};review=[]
else:
 p=Path('outerreset-'+a.candidate+'-independent-review.json');r=json.loads(p.read_text());assert r['phase']=='independent_review_passed_ready_for_hardware';v={**r['variants'][a.variant],'runtime':r['runtime']};review=[p]
assert sha(v['mcs'])==v['mcs_sha256']
files=[Path(__file__),*review,*map(Path,['outerreset_hw_guard_v2.py','outerreset_cold_v2.py','flash_firmware.py','boot_test.py','network_boot_stress.py','deepreset_neighbor.py','deepreset_fresh_wait.py','deepreset_fresh_wait_v2.py']),Path(v['mcs'])]
if a.existing_flash_report:files.append(a.existing_flash_report)
sources={str(p):sha(p) for p in files};report={'started':datetime.datetime.now().isoformat(),'host':a.host,'serial':serial,'candidate':a.candidate,'variant':a.variant,'runtime':v['runtime'],'review_report':str(review[0]) if review else None,'source_sha256':sources,'events':[],'trials':[],'limits':['Enabled is the source-built candidate; f403 is raw-reset routing without a one-shot. hold/early are diagnostic controls. No late-fault watchdog.','TargetedneighborAPI maystillbackoff; actualARPpacketswillbecompared fornegativeoutcomes.','Powercontrolack notmeasuredphysicalpoweredge.']}
def save(phase,**kw):
 report['phase']=phase;report['events'].append({'time':datetime.datetime.now().isoformat(),'event':phase,**kw});out.write_text(json.dumps(report,indent=2));print(json.dumps(report['events'][-1]),flush=True)
def guard():
 outerreset_hw_guard_v2.assert_exclusive();assert not Path('outerreset-stop-experiments').exists();assert all(sha(p)==h for p,h in sources.items())
def child(args,label,timeout):
 guard();p=Path('outerreset-cohort-'+a.label+'-'+label+'.console.txt');assert not p.exists()
 with p.open('xb') as stream:c=subprocess.run([sys.executable,'-E','-B',*args],stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
 report[label+'_actual_exit_code']=c.returncode;assert c.returncode==0,'Inspect '+str(p)+'; do not recover silently'
try:
 guard()
 if a.existing_flash_report:fp=a.existing_flash_report;save('reusing_previous_full_readback_same_target_no_new_flash')
 else:
  assert not list(Path('.').glob('flash-'+a.label+'-*-result.json'));save('programming_candidate_must_not_powercycle')
  child(['flash_firmware.py','--mcs',v['mcs'],'--sha256',v['mcs_sha256'],'--serial',serial,'--label',a.label],'flash',1800)
  found=list(Path('.').glob('flash-'+a.label+'-*-result.json'));assert len(found)==1;fp=found[0]
 f=json.loads(fp.read_text());assert f['success'] and f['image_matches'] and f['target_serial']==serial and f['mcs_sha256']==v['mcs_sha256'] and f['readback_sha256']==v['expected_full_flash_sha256']
 report.update(flash_report=str(fp),flash_report_sha256=sha(fp),full_flash_sha256=f['readback_sha256'],flash_reused=bool(a.existing_flash_report));save('cold_trials')
 cold=Path('outerreset-'+a.label+'-cold.json');assert not cold.exists();args=['outerreset_cold_v2.py','--host',a.host,'--version',v['runtime'],'--log',str(cold),'--off-schedule',a.off_schedule,'--repeat',str(a.count)]
 if a.early:args.append('--early')
 schedule=[int(s) for s in a.off_schedule.split(',')]*a.count
 child(args,'cold',sum(schedule)+len(schedule)*150+120)
 r=json.loads(cold.read_text());assert len(r['trials'])==len(schedule);report.update(cold_log=str(cold),cold_sha256=sha(cold),trials=r['trials'],successes=sum(t['success'] for t in r['trials']));guard();save('cohort_complete_power_on',successes=report['successes'],trials=len(schedule))
except BaseException as e:report['error']=type(e).__name__+':'+str(e);save('STOPPED_NEEDS_INSPECTION');raise
