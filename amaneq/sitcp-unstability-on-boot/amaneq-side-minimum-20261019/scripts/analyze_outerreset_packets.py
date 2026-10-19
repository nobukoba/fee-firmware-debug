"""Correlate each boot with actual on-wire ARP; metadata only, no payload export."""
import argparse,csv,datetime,hashlib,io,json,subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--live',action='store_true');a=ap.parse_args();assert not a.output.exists()
capture=Path('outerreset-20261019.pcapng');assert capture.exists()
if not a.live:assert json.loads(Path('outerreset-resource-cleanup.json').read_text())['phase']=='capture_closed_sleep_inhibition_released_no_workers'
fields=['frame.time_epoch','arp.opcode','arp.src.proto_ipv4','arp.dst.proto_ipv4','eth.src','eth.dst']
args=[r'C:\Program Files\Wireshark\tshark.exe','-r',str(capture),'-Y','arp','-T','fields','-E','header=y','-E','separator=\t','-E','occurrence=f']
for f in fields:args+=['-e',f]
c=subprocess.run(args,capture_output=True,text=True,timeout=180);assert c.returncode==0,c.stderr
rows=list(csv.DictReader(io.StringIO(c.stdout),delimiter='\t'));cases=[];skipped=[];sources={str(Path(__file__)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
reports=sorted(Path('.').glob('outerreset-*-cold.json'))+sorted(Path('.').glob('outerreset-restored-*-cold3.json'))+[Path('deepreset-native-outerfact16a-cold3.json')]
for p in reports:
 r=json.loads(p.read_text())
 if r['events'][-1]['kind'] not in ['complete_power_on','complete']:
  assert a.live,p
  skipped.append(str(p));continue
 sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();host=r['host'];starts={};ends={};current=None
 for e in r['events']:
  if e['kind']=='cold_start':current=e['number']
  if e['kind']=='power_on':starts[e['number']]=e['time']
  elif e['kind'] in ['power_status','outlet_status'] and e.get('requested') in [1,'ON'] and current is not None:starts[current]=e['time']
  if e['kind']=='cold_result':ends[e['number']]=e['time']
 for trial in r['trials']:
  n=trial['number'];start=datetime.datetime.fromisoformat(starts[n]).timestamp();end=datetime.datetime.fromisoformat(ends[n]).timestamp()
  selected=[x for x in rows if start<=float(x['frame.time_epoch'])<=end and (x['arp.src.proto_ipv4']==host or x['arp.dst.proto_ipv4']==host)]
  requests=[x for x in selected if x['arp.opcode']=='1' and x['arp.dst.proto_ipv4']==host and x['arp.src.proto_ipv4']=='192.168.10.70']
  replies=[x for x in selected if x['arp.opcode']=='2' and x['arp.src.proto_ipv4']==host]
  cases.append({'cold_log':str(p),'host':host,'trial':n,'success':trial['success'],'off_seconds':trial.get('off_seconds',5),'power_on_ack':starts[n],'end':ends[n],'request_frames':len(requests),'reply_frames':len(replies),'request_elapsed_seconds':[round(float(x['frame.time_epoch'])-start,6) for x in requests],'reply_elapsed_seconds':[round(float(x['frame.time_epoch'])-start,6) for x in replies],'negative_has_actual_request':bool(requests) if not trial['success'] else None})
r={'created':datetime.datetime.now().isoformat(),'phase':'live_capture_metadata_provisional' if a.live else 'closed_capture_boot_packet_correlation_complete','tshark_actual_exit_code':c.returncode,'capture_bytes_at_read':capture.stat().st_size,'capture_sha256':None if a.live else hashlib.sha256(capture.read_bytes()).hexdigest(),'cases':cases,'skipped_incomplete':skipped,'source_sha256':sources,'limits':['ARP API invocation is not evidence of wire transmission; actual host requests and board replies counted here.','No reply to a transmitted request supports endpoint unreachability but does not uniquely identify analog CDR failure.','Power timestamps are control acknowledgements, not measured rail edges.','No packet payload or raw capture exported.']}
a.output.write_text(json.dumps(r,indent=2));print(json.dumps({'cases':len(cases),'negative_without_requests':sum(not x['success'] and not x['request_frames'] for x in cases)}))
