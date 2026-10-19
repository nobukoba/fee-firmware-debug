"""Final restoration, serial/full-flash verification, cold3 and EEPROM check."""
import argparse,datetime,hashlib,json,subprocess,sys
from pathlib import Path
import outerreset_hw_guard_v2
ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');a=ap.parse_args();assert a.execute
out=Path('outerreset-restoration.json');assert not out.exists()
targets=[
 {'suffix':'16','host':'192.168.10.16','serial':'210299BBCDDA','version':'0x60c4f202','mcs':'lrtdc-startup-fix/build/pcs-recovery-f202/lrtdc-pcs-recovery-f202.mcs','mcs_sha256':'1518696ba9f2261f1ec4f04c0a8498273e5cec9beec1b987eb54d2d05f7ddfd7','full_sha256':'19da89bf5365ceb0beb365ff6ec21d90fc80fc87f804a44a9cb0be572d1bff0b'},
 {'suffix':'17','host':'192.168.10.17','serial':'210299BDCF8E','version':'0x60c4020a','mcs':'factory-v2a-backup/factory-v2a.mcs','mcs_sha256':'b1010ec6dc37e7223758d544ce9f30aa30549c29acfd9146675b3a7f17a6c2c0','full_sha256':'7dd784de31ff8b3b2cbae4602274faf3e2f587f1bc2185a89ad3ba5e7de48a13'}]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for t in targets:assert sha(t['mcs'])==t['mcs_sha256']
files=[Path(__file__),*map(Path,['outerreset_hw_guard_v2.py','outerreset_cold_v2.py','flash_firmware.py','deepreset_fresh_wait.py','deepreset_fresh_wait_v2.py','deepreset_neighbor.py','boot_test.py','network_boot_stress.py','verify_dual_final.py','eeprom-before-startup.bin','eeprom-dual17-before.bin'])]
hashes={str(p):sha(p) for p in files}
assert hashes['eeprom-before-startup.bin']=='341c5c207c91e51c634ba3e3090fea4689e4e5ae07725e4996a3e568b504c887'
assert hashes['eeprom-dual17-before.bin']=='0657876d036a1b9c1ba34903bbf577d490741c851af11916d91efed7f1a1521e'
r={'started':datetime.datetime.now().isoformat(),'source_sha256':hashes,'targets':targets,'events':[],'boards':{},'switch_topology':'Switch alwaysON; Kikusui16, ezOutlet17. No setpoint or EEPROM writes.'}
def save(event,**kw):
 r['phase']=event;r['events'].append({'time':datetime.datetime.now().isoformat(),'event':event,**kw});out.write_text(json.dumps(r,indent=2));print(json.dumps(r['events'][-1]),flush=True)
def guard():
 outerreset_hw_guard_v2.assert_exclusive();assert all(sha(p)==h for p,h in hashes.items())
 # Offline Vivado must also finish before closing the investigation.
 q="Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'vivado.exe' -and $_.CommandLine -match '-mode batch' } | Select-Object -ExpandProperty ProcessId | ConvertTo-Json -Compress"
 assert not subprocess.check_output(['powershell.exe','-NoProfile','-Command',q],text=True).strip()
def child(args,label,timeout):
 guard();console=Path('outerreset-restore-'+label+'.console.txt');assert not console.exists()
 with console.open('xb') as stream:c=subprocess.run([sys.executable,'-E','-B',*args],stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
 r[label+'_actual_exit_code']=c.returncode;assert c.returncode==0,'Inspect '+str(console)+' before further operations'
try:
 guard();save('restoration_started_all_workers_finished')
 for t in targets:
  s=t['suffix'];label='restoreouter'+s;assert not list(Path('.').glob('flash-'+label+'-*-result.json'))
  save('programming_restore_image_must_not_powercycle',host=t['host'])
  child(['flash_firmware.py','--mcs',t['mcs'],'--sha256',t['mcs_sha256'],'--serial',t['serial'],'--label',label],s+'-flash',1800)
  found=list(Path('.').glob('flash-'+label+'-*-result.json'));assert len(found)==1;fp=found[0];f=json.loads(fp.read_text())
  assert f['success'] and f['image_matches'] and f['target_serial']==t['serial'] and f['mcs_sha256']==t['mcs_sha256'] and f['readback_sha256']==t['full_sha256']
  cold=Path('outerreset-restored-'+s+'-cold3.json');assert not cold.exists()
  r['boards'][s]={'flash_report':str(fp),'flash_report_sha256':sha(fp),'full_readback_sha256':f['readback_sha256']};save('restored_cold_trials',host=t['host'])
  child(['outerreset_cold_v2.py','--host',t['host'],'--version',t['version'],'--log',str(cold),'--repeat','3'],s+'-cold3',600)
  c=json.loads(cold.read_text());assert len(c['trials'])==3;r['boards'][s].update(cold_log=str(cold),cold_sha256=sha(cold),cold_successes=sum(v['success'] for v in c['trials']));save('board_restored_power_on',host=t['host'],cold_successes=r['boards'][s]['cold_successes'])
 final=Path('outerreset-final-status.json');assert not final.exists();save('checking_both_runtime_network_EEPROM_and_power')
 child(['verify_dual_final.py','--output',str(final)],'both-final-readonly',180)
 status=json.loads(final.read_text());assert all(v['first']['success'] and v['confirmation']['success'] and v['eeprom_matches_baseline'] for v in status['boards'].values())
 r['final_status']=str(final);r['final_status_sha256']=sha(final);assert all(v['cold_successes']==3 for v in r['boards'].values())
 save('both_restored_full_readback_cold3_network_EEPROM_verified_power_on')
except BaseException as e:r['error']=type(e).__name__+':'+str(e);save('STOPPED_NEEDS_INSPECTION');raise
