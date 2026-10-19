"""Run after observed capture/keepawake exits and completed board restoration."""
import argparse,ctypes,datetime,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--capture-exit-code',type=int,required=True);p.add_argument('--keepawake-exit-code',type=int,required=True);a=p.parse_args()
out=Path('outerreset-resource-cleanup.json');assert not out.exists()
restore=Path('outerreset-restoration.json');r=json.loads(restore.read_text());assert r['phase']=='both_restored_full_readback_cold3_network_EEPROM_verified_power_on'
assert a.keepawake_exit_code==0 and a.capture_exit_code in [0,1]
assert Path('outerreset-stop-keepawake').exists()
query="""Get-CimInstance Win32_Process | Where-Object { ($_.Name -eq 'dumpcap.exe' -and $_.CommandLine -match 'outerreset-20261019') -or ($_.Name -eq 'python.exe' -and $_.CommandLine -match 'outerreset_keepawake|outerreset_final_soak|run_outerreset_|outerreset_cold|flash_firmware\\.py|run_deepreset_factory_reverse') -or ($_.Name -eq 'vivado.exe' -and $_.CommandLine -match '-mode batch') } | Select-Object -ExpandProperty ProcessId | ConvertTo-Json -Compress"""
assert not subprocess.check_output(['powershell.exe','-NoProfile','-Command',query],text=True).strip(),'Workers still active'
capture=Path('outerreset-20261019.pcapng');assert capture.stat().st_size>0
c=subprocess.run([r'C:\Program Files\Wireshark\capinfos.exe',str(capture)],capture_output=True,text=True);assert c.returncode==0
metadata=Path('outerreset-final-capinfos.txt');assert not metadata.exists();metadata.write_text(c.stdout,encoding='utf-8')
kernel=ctypes.WinDLL('kernel32',use_last_error=True)
kernel.QueryDosDeviceW.argtypes=[ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_uint32];kernel.QueryDosDeviceW.restype=ctypes.c_uint32
def mapping(drive):
 buffer=ctypes.create_unicode_buffer(32768)
 if kernel.QueryDosDeviceW(drive,buffer,len(buffer)):return buffer.value
 assert ctypes.get_last_error()==2,'Unexpected drive lookup error'
 return None
owned={'I:':'lrtdc-outerreset-f401','J:':'lrtdc-outerreset-f402','K:':'lrtdc-outerreset-f403'}
mapped={drive:mapping(drive) for drive in owned}
for drive,folder in owned.items():
 expected='\\??\\'+str(Path(folder).resolve())
 assert mapped[drive] is None or mapped[drive].casefold()==expected.casefold(),'Unexpected mapping; do not remove:'+drive
for drive in owned:
 if mapped[drive] is not None:
  subprocess.run(['subst',drive,'/D'],check=True,capture_output=True)
  assert mapping(drive) is None
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
result={'created':datetime.datetime.now().isoformat(),'phase':'capture_closed_sleep_inhibition_released_no_workers','capture':str(capture),'capture_sha256':sha(capture),'capture_bytes':capture.stat().st_size,'capture_observed_actual_exit_code':a.capture_exit_code,'keepawake_observed_actual_exit_code':a.keepawake_exit_code,'capinfos_actual_exit_code':c.returncode,'metadata':str(metadata),'metadata_sha256':sha(metadata),'restoration_sha256':sha(restore),'script_sha256':sha(__file__),'limits':['Capture exit code 1 can follow an explicit interrupt; valid capture was independently parsed by capinfos.','No dropped-packet claim unless capture termination output explicitly reports it.']}
result['owned_temporary_drive_mappings_removed']=mapped
out.write_text(json.dumps(result,indent=2));print(json.dumps({'phase':result['phase'],'capture_bytes':result['capture_bytes']}))
