"""Verify whitelisted source/export hashes and every tracked study byte against remote main."""
import argparse,datetime,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--require-final',action='store_true');a=p.parse_args();assert not a.output.exists()
repo=Path('fee-firmware-debug');relative='amaneq/sitcp-unstability-on-boot/amaneq-side-minimum-20261019';root=repo/relative
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
sources=[];exports=[];manifests=[]
for path in sorted(root.glob('*manifest.json')):
 r=json.loads(path.read_text());assert isinstance(r['files'],list);manifests.append({'path':str(path),'sha256':sha(path)})
 for item in r['files']:
  original=Path(item['source']);target=root/item['export'];assert target.resolve().is_relative_to(root.resolve())
  assert sha(original)==item['source_sha256'],str(original)
  assert sha(target)==item['export_sha256'],str(target)
  sources.append(str(original));exports.append(str(target))
assert sources and len(exports)==len(set(exports))
if a.require_final:
 restore=json.loads(Path('outerreset-restoration.json').read_text());assert restore['phase']=='both_restored_full_readback_cold3_network_EEPROM_verified_power_on'
 cleanup=json.loads(Path('outerreset-resource-cleanup.json').read_text());assert cleanup['phase']=='capture_closed_sleep_inhibition_released_no_workers' and sha(cleanup['capture'])==cleanup['capture_sha256']
 local=json.loads(Path('outerreset-local-completion-audit-v2.json').read_text());assert local['phase']=='local_completion_checks_passed' and local['functional_source_commit_mandatory_and_verified']
 assert all(v['cold_successes']==3 for v in restore['boards'].values())
subprocess.run(['git','-C',str(repo),'fetch','origin','main'],check=True,capture_output=True)
head=git('rev-parse','HEAD').decode().strip();tracking=git('rev-parse','origin/main').decode().strip();remote=git('ls-remote','origin','refs/heads/main').decode().split()[0]
assert head==tracking==remote and not git('status','--porcelain').strip()
tracked=git('ls-files','--',relative).decode().splitlines();assert tracked
if a.require_final:tracked.append('amaneq/sitcp-unstability-on-boot/README.md')
for path in tracked:assert git('show','HEAD:'+path)==(repo/path).read_bytes(),path
r={'created':datetime.datetime.now().isoformat(),'phase':'publication_verified_after_safe_restoration' if a.require_final else 'checkpoint_verified_study_in_progress','git_HEAD':head,'origin_main':tracking,'remote_main':remote,'worktree_clean':True,'tracked_study_files_verified':len(tracked),'source_export_pairs_verified':len(sources),'manifests':manifests,'source_files':sources,'export_files':exports,'verification_script_sha256':sha(__file__),'final_restoration_required':a.require_final}
a.output.write_text(json.dumps(r,indent=2));print(json.dumps({k:r[k] for k in ['phase','git_HEAD','tracked_study_files_verified','source_export_pairs_verified']}))
