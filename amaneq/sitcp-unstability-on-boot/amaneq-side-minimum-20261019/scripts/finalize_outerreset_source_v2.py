"""Resume the prepared one-file commit after repo-local identity setup."""
import argparse,datetime,hashlib,json,subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--candidate',choices=['f401','f402','f403'],required=True);a=ap.parse_args();repo=Path('lrtdc-outerreset-'+a.candidate);out=Path('outerreset-final-source-commit.json');assert not out.exists()
def load(p):return json.loads(Path(p).read_text())
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert load('outerreset-restoration.json')['phase']=='both_restored_full_readback_cold3_network_EEPROM_verified_power_on'
assert load('outerreset-resource-cleanup.json')['phase']=='capture_closed_sleep_inhibition_released_no_workers'
selection=load('outerreset-result-selection.json');assert selection['selected_candidate']==a.candidate and selection['phase']=='final_results_reviewed_after_restoration'
review=load('outerreset-'+a.candidate+'-independent-review.json');assert review['phase']=='independent_review_passed_ready_for_hardware'
chosen=[r for r in load('outerreset-cohort-summary-final.json')['cases'] if r['candidate']==a.candidate and r['variant']=='enabled']
assert {r['host'] for r in chosen}=={'192.168.10.16','192.168.10.17'} and all(r['successes']==r['trials'] for r in chosen)
assert all(sum(r['trials'] for r in chosen if r['host']==h)>=3 for h in ['192.168.10.16','192.168.10.17'])
base='5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039';branch='codex/amaneq-sitcp-minimal-reset'
assert git('rev-parse','HEAD').decode().strip()==base and git('branch','--show-current').decode().strip()==branch
assert git('diff','--cached','--name-only').decode().splitlines()==['hdl/toplevel.vhd']
top=repo/'hdl/toplevel.vhd';before=sha(top);buildpath=Path('outerreset-'+a.candidate+'-build.json');build=load(buildpath)
assert build['phase']=='build_complete_independent_review_required' and build['actual_exit_code']==0
assert {h for p,h in build['source_sha256'].items() if Path(p).resolve()==top.resolve()}=={before}
assert git('show',':hdl/toplevel.vhd')==top.read_bytes().replace(b'\r\n',b'\n')
fields=git('diff','--cached','--numstat').decode().split();assert tuple(map(int,fields[:2]))==(review['functional_added_lines'],review['functional_deleted_lines'])
subprocess.run(['git','-C',str(repo),'diff','--cached','--check'],check=True,capture_output=True)
for key in ['user.name','user.email']:
 identity=subprocess.check_output(['git','-C','fee-firmware-debug','config','--get',key],text=True).strip();assert identity
 subprocess.run(['git','-C',str(repo),'config','--local',key,identity],check=True,capture_output=True)
subprocess.run(['git','-C',str(repo),'var','GIT_AUTHOR_IDENT'],check=True,capture_output=True)
subprocess.run(['git','-C',str(repo),'commit','-m','Adjust Ethernet startup reset without generated IP edits'],check=True,capture_output=True)
head=git('rev-parse','HEAD').decode().strip();assert git('rev-parse','HEAD^').decode().strip()==base and sha(top)==before
assert git('diff','--name-only',base,head).decode().splitlines()==['hdl/toplevel.vhd'] and git('show','HEAD:hdl/toplevel.vhd')==top.read_bytes().replace(b'\r\n',b'\n')
r={'created':datetime.datetime.now().isoformat(),'phase':'validated_functional_source_committed_locally','candidate':a.candidate,'repository':str(repo),'branch':branch,'commit':head,'parent':base,'committed_files':['hdl/toplevel.vhd'],'git_added_lines':review['functional_added_lines'],'git_deleted_lines':review['functional_deleted_lines'],'compiled_top_sha256_unchanged':before,'compiled_top_build_proof':str(buildpath),'compiled_top_build_proof_sha256':sha(buildpath),'script_sha256':sha(__file__),'test_version_and_build_scripts_kept_separate':True,'upstream_public_push_performed':False,'resumed_failed_commit_exit_code':128,'resumed_helper_sha256':sha('finalize_outerreset_source.py'),'identity_setup':'Repository-local user.name/email inherited from existing private study repository. No global configuration changed.','limits':['Only the tested functional top is committed; build-generated IP/XCI and test version remain separate.','Private study publication and remote verification remain separate steps.']}
out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase'],'commit':head,'branch':branch}))
