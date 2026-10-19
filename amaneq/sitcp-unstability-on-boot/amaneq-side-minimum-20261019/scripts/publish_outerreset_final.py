"""Publish a whitelisted completed study after safe restoration and local audit."""
import ast,datetime,hashlib,json,re,subprocess
from pathlib import Path
import outerreset_private_repo
repo=Path('fee-firmware-debug');relative='amaneq/sitcp-unstability-on-boot/amaneq-side-minimum-20261019';root=repo/relative;assert not root.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
assert not git('status','--porcelain').strip()
assert load('outerreset-restoration.json')['phase']=='both_restored_full_readback_cold3_network_EEPROM_verified_power_on'
assert load('outerreset-resource-cleanup.json')['phase']=='capture_closed_sleep_inhibition_released_no_workers'
assert load('outerreset-local-completion-audit-v2.json')['phase']=='local_completion_checks_passed' and load('outerreset-local-completion-audit-v2.json')['functional_source_commit_mandatory_and_verified']
selection=load('outerreset-result-selection.json');assert selection['phase']=='final_results_reviewed_after_restoration'
commit=load('outerreset-final-source-commit.json');assert commit['phase']=='validated_functional_source_committed_locally' and commit['candidate']==selection['selected_candidate']
readme=Path('outerreset-study-final.md');text=readme.read_text(encoding='utf-8');assert '調査中の草稿' not in text and '## 最終結果' in text
privacy=outerreset_private_repo.metadata();assert privacy['isPrivate'] and privacy['default_branch']=='main'
def clean(v):
 if isinstance(v,str):return v.replace(str(Path.cwd())+'\\','WORKSPACE/').replace(str(Path.cwd()),'WORKSPACE').replace('\\','/')
 if isinstance(v,list):return [clean(x) for x in v]
 if isinstance(v,dict):return {clean(k):clean(x) for k,x in v.items()}
 return v
# Never export controller credentials, raw EEPROM, packet payload, flash image or DCP.
secret_values=[]
for node in ast.walk(ast.parse(Path('boot_test.py').read_text(encoding='utf-8'))):
 if isinstance(node,ast.Assign) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str):
  names=[t.id for t in node.targets if isinstance(t,ast.Name)]
  if any(re.search(r'PASS|SECRET|TOKEN|AUTH',n,re.I) for n in names) and len(node.value.value)>=6:secret_values.append(node.value.value.encode())
root.mkdir(parents=True);manifest=[]
def export(p,relative_path,json_data=False):
 p=Path(p);q=root/relative_path;assert not q.exists();q.parent.mkdir(parents=True,exist_ok=True)
 data=(json.dumps(clean(load(p)),ensure_ascii=False,indent=2)+'\n').encode() if json_data else p.read_bytes().replace(b'\r\n',b'\n')
 assert all(secret not in data for secret in secret_values),'Credential-like value blocked; inspect locally without printing'
 q.write_bytes(data);manifest.append({'source':str(p),'source_sha256':sha(p),'export':q.relative_to(root).as_posix(),'export_sha256':sha(q)})
reports=sorted(p for p in Path('.').glob('outerreset-*.json') if p.name not in ['outerreset-session-state.json','outerreset-publication-verification.json'])
reports += [Path('deepreset-native-outerfact16a.json'),Path('deepreset-native-outerfact16a-cold3.json')]
for p in reports:export(p,'evidence/'+p.name,True)
for p in sorted(Path('.').glob('outerreset-cohort-*.json')):
 if p.name.startswith('outerreset-cohort-summary-'):
  assert load(p)['phase']=='all_completed_outerreset_cohorts_checked'
  continue
 f=Path(load(p)['flash_report']);destination='evidence/'+f.name
 if not (root/destination).exists():export(f,destination,True)
for b in load('outerreset-restoration.json')['boards'].values():
 f=Path(b['flash_report']);destination='evidence/'+f.name
 if not (root/destination).exists():export(f,destination,True)
scripts=set()
for pattern in ['run_outerreset*.py','prepare_outerreset*.py','configure_outerreset*.py','finalize_outerreset*.py','write_outerreset*.py','review_outerreset*.py','simulate_outerreset*.py','audit_outerreset*.py','analyze_outerreset*.py','summarize_outerreset*.py','outerreset_hw_guard*.py','outerreset_cold*.py','outerreset_keepawake.py','outerreset_final_soak.py','inspect-outerreset*.tcl','export-outerreset*.tcl','build-outerreset-*.tcl','outerreset-*-netlist-config.tcl']:
 scripts.update(Path('.').glob(pattern))
scripts.update([Path(__file__),Path('verify_outerreset_publication.py'),Path('outerreset_private_repo.py')])
for p in sorted(scripts):export(p,'scripts/'+p.name)
for candidate in ['f401','f402','f403']:
 repo_source=Path('lrtdc-outerreset-'+candidate)
 export('outerreset-functional-'+candidate+'.patch','patches/outerreset-functional-'+candidate+'.patch')
 export(repo_source/'hdl/toplevel.vhd','source/'+candidate+'/toplevel.vhd')
 export(repo_source/'hdl/defBusAddressMap.vhd','source/'+candidate+'/defBusAddressMap.vhd')
 export(repo_source/('build-outerreset-'+candidate+'.tcl'),'source/'+candidate+'/build.tcl')
 sim=Path('experiments/outerreset-'+candidate+'-sim')
 if candidate!='f403':
  for name in ['result.json','timer.vhd','tb.vhd']:export(sim/name,'simulation/'+candidate+'/'+name,name.endswith('.json'))
 for p in [Path('outerreset-'+candidate+'-netlist-inspection.txt'),Path('outerreset-'+candidate+'-matched/fresh-clock-reset-audit.txt')]:
  if p.exists():export(p,'evidence/'+candidate+'-'+p.name)
 if candidate=='f403':
  for name in ['fresh-clock-reset-audit.txt','fresh-clock-reset-extra.txt','compiled-files.txt','reused-ip-runs.txt']:
   p=repo_source/'build/outerreset-f403'/name
   if p.exists():export(p,'evidence/f403-'+name)
export(readme,'README.md');export('outerreset-result-selection.json','result-summary.json',True)
manifest_path=root/'final-manifest.json';manifest_path.write_bytes((json.dumps({'state':'COMPLETED_RESTORED','created':datetime.datetime.now().isoformat(),'files':manifest},indent=2)+'\n').encode())
index=repo/'amaneq/sitcp-unstability-on-boot/README.md';s=index.read_text(encoding='utf-8');s+='\n\n最新の追加記録：[AMANEQ側だけの最小修正と実機比較（2026-10-19）](amaneq-side-minimum-20261019/)。差分・全起動結果・比較対照・最終復元は同記録を参照。\n';index.write_bytes(s.encode())
subprocess.run(['git','-C',str(repo),'add',relative,'amaneq/sitcp-unstability-on-boot/README.md'],check=True)
subprocess.run(['git','-C',str(repo),'commit','-m','Record minimum AMANEQ-side startup reset experiments and verified restoration'],check=True)
subprocess.run(['git','-C',str(repo),'push','origin','main'],check=True)
print(json.dumps({'published_files':len(manifest),'study':relative}))
