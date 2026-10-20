"""Compare the named internal PCS/PMA subset, not whole-image equivalence."""
import json,hashlib,datetime
from pathlib import Path
def load(v):
 p=Path(f'lrtdc-pllwait-{v}/build/pllwait-{v}/core-signature.tsv')
 d={}
 with p.open() as f:
  for line in f:
   kind,name,*values=line.rstrip('\n').split('\t')
   if kind=='NET' and len(values[0])>100000:
    kind='SKIP';values=['shared_global_route_over_100000_characters']
   if kind=='NET':
    values=[hashlib.sha256(values[0].encode()).hexdigest(),hashlib.sha256(values[1].encode()).hexdigest()]
   key=(kind,name);assert key not in d;d[key]=values
 assert sum(k[0]=='CELL' for k in d)>100
 canonical=json.dumps([(k,d[k]) for k in sorted(d) if k[0] in ('CELL','NET')],separators=(',',':')).encode()
 return d,hashlib.sha256(canonical).hexdigest()
a,ha=load('f500');b,hb=load('f503');out={}
for kind in ['CELL','NET']:
 ka={k for k in a if k[0]==kind};kb={k for k in b if k[0]==kind};common=ka&kb
 changed=[dict(name=k[1],native=a[k],early=b[k]) for k in sorted(common) if a[k]!=b[k]]
 out[kind]=dict(native=len(ka),early=len(kb),common=len(common),identical=sum(a[k]==b[k] for k in common),
                only_native=[k[1] for k in sorted(ka-kb)],only_early=[k[1] for k in sorted(kb-ka)],changed=changed)
out.update(recorded=datetime.datetime.now().isoformat(),signature_sha256=dict(f500=ha,f503=hb),
 skipped_global_or_constant_nets=dict(f500=sum(k[0]=='SKIP' for k in a),f503=sum(k[0]=='SKIP' for k in b)),
 scope='Named gen_pcspma subset: primitive type/LOC/BEL and net ROUTE/pin hashes. Excludes explicitly named shared constants and shared/global ROUTE strings over100000characters, external reset nets, clocks outside this hierarchy, and analog behavior. Signature SHA256 covers canonical compared CELL/NET records only; not complete image equivalence.')
Path('pllwait-study/core-comparison-f500-f503.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:{q:v for q,v in out[k].items() if q in ['native','early','common','identical']} for k in ['CELL','NET']}))
