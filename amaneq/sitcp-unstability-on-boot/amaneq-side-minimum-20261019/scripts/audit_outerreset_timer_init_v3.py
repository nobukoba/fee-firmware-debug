"""Verify physical FF configuration preloads, independently of RTL startup assumptions."""
import argparse,datetime,hashlib,json,re,tkinter
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--candidate',choices=['f401','f402','f403'],required=True);a=ap.parse_args();out=Path('outerreset-'+a.candidate+'-timer-init-audit.json');assert not out.exists()
root=(Path('lrtdc-outerreset-f403/build/outerreset-f403') if a.candidate=='f403' else Path('outerreset-'+a.candidate+'-matched/enabled'));t=tkinter.Tcl();values={};files=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for kind in ['FDPE','FDCE']:
 np=root/('init-'+kind+'-NAME.tcllist');vp=root/('init-'+kind+'-INIT.tcllist');files += [np,vp]
 names=t.splitlist(np.read_text());inits=t.splitlist(vp.read_text());assert len(names)==len(inits)
 for name,init in zip(names,inits):values[name]=(kind,init)
expected={'u_KeepPwrOnRst':268435455,'u_PcsWait':125000000}
if a.candidate=='f403':expected={'u_KeepPwrOnRst':268435455}
if a.candidate=='f401':expected['u_PcsWaitEnd']=137500000
cases=[]
for instance,preset in expected.items():
 bits={int(re.search(r'\[(\d+)\]',n).group(1)):(kind,int(v.split("'b")[1],2)) for n,(kind,v) in values.items() if n.startswith(instance+'/reg_counter_reg[')}
 assert set(bits)==set(range(32));actual=sum(v<<i for i,(kind,v) in bits.items());assert actual==preset
 for i,(kind,value) in bits.items():assert value==((preset>>i)&1) and kind==('FDPE' if value else 'FDCE')
 assert values[instance+'/reg_reset_reg']==('FDPE',"1'b1")
 cases.append({'instance':instance,'counter_width':32,'configured_counter_INIT_decimal':actual,'configured_counter_INIT_hex':hex(actual),'reset_output_INIT':1,'all_counter_FF_INITs_match_asynchronous_preset_or_clear_type':True})
r={'created':datetime.datetime.now().isoformat(),'phase':'physical_timer_counter_and_reset_output_initial_values_verified','candidate':a.candidate,'cases':cases,'source_sha256':{str(p):sha(p) for p in [Path(__file__),*files,Path('outerreset-'+a.candidate+('-inspection.json' if a.candidate=='f403' else '-export.json'))]},'limits':['Physical configuration INIT values, not an oscilloscope reset waveform measurement.','Rules out a zero-initialized global/new counter in these exact compiled images. It does not prove a unique physical initiating cause.','Clock periods/dependencies and live cold outcomes are checked separately.']}
out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase'],'cases':cases}))
