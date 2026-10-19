"""Create a local one-file functional commit only after reviewed tests and restoration."""
import argparse,datetime,hashlib,json,subprocess
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--candidate',choices=['f401','f402','f403'],required=True);a=ap.parse_args();repo=Path('lrtdc-outerreset-'+a.candidate);out=Path('outerreset-final-source-commit.json');assert not out.exists()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert load('outerreset-restoration.json')['phase']=='both_restored_full_readback_cold3_network_EEPROM_verified_power_on'
assert load('outerreset-resource-cleanup.json')['phase']=='capture_closed_sleep_inhibition_released_no_workers'
selection=load('outerreset-result-selection.json');assert selection['phase']=='final_results_reviewed_after_restoration' and selection['selected_candidate']==a.candidate
review=load('outerreset-'+a.candidate+'-independent-review.json');assert review['phase']=='independent_review_passed_ready_for_hardware'
summary=load('outerreset-cohort-summary-final.json');chosen=[r for r in summary['cases'] if r['candidate']==a.candidate and r['variant']=='enabled']
assert {r['host'] for r in chosen}=={'192.168.10.16','192.168.10.17'} and all(r['successes']==r['trials'] for r in chosen)
assert all(sum(r['trials'] for r in chosen if r['host']==host)>=3 for host in ['192.168.10.16','192.168.10.17'])
base='5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039';assert git('rev-parse','HEAD').decode().strip()==base and not git('diff','--cached','--name-only').strip()
fields=git('diff','--numstat',base,'--','hdl/toplevel.vhd').decode().split();assert tuple(map(int,fields[:2]))==(review['functional_added_lines'],review['functional_deleted_lines'])
subprocess.run(['git','-C',str(repo),'diff','--check',base,'--','hdl/toplevel.vhd'],check=True,capture_output=True)
top=repo/'hdl/toplevel.vhd';before=sha(top)
buildpath=Path('outerreset-'+a.candidate+'-build.json');build=load(buildpath)
assert build['phase']=='build_complete_independent_review_required' and build['actual_exit_code']==0
compiled_hashes={h for p,h in build['source_sha256'].items() if Path(p).resolve()==top.resolve()}
assert compiled_hashes=={before},'Functional top differs from the source actually compiled'
branch='codex/amaneq-sitcp-minimal-reset';subprocess.run(['git','-C',str(repo),'checkout','-b',branch],check=True,capture_output=True)
subprocess.run(['git','-C',str(repo),'add','hdl/toplevel.vhd'],check=True,capture_output=True);assert git('diff','--cached','--name-only').decode().splitlines()==['hdl/toplevel.vhd']
subprocess.run(['git','-C',str(repo),'commit','-m','Adjust Ethernet startup reset without generated IP edits'],check=True,capture_output=True)
head=git('rev-parse','HEAD').decode().strip();assert git('rev-parse','HEAD^').decode().strip()==base and sha(top)==before
assert git('diff','--name-only',base,head).decode().splitlines()==['hdl/toplevel.vhd'];assert git('show','HEAD:hdl/toplevel.vhd')==top.read_bytes().replace(b'\r\n',b'\n')
r={'created':datetime.datetime.now().isoformat(),'phase':'validated_functional_source_committed_locally','candidate':a.candidate,'repository':str(repo),'branch':branch,'commit':head,'parent':base,'committed_files':['hdl/toplevel.vhd'],'git_added_lines':review['functional_added_lines'],'git_deleted_lines':review['functional_deleted_lines'],'compiled_top_sha256_unchanged':before,'script_sha256':sha(__file__),'test_version_and_build_scripts_kept_separate':True,'upstream_public_push_performed':False,'limits':['Local functional commit only. Study patch/source/evidence are published separately to the authorized private fee-firmware-debug repository.','Test firmware version ID and study build scripts are separate from this one-file functional source change.']}
r['compiled_top_build_proof']=str(buildpath);r['compiled_top_build_proof_sha256']=sha(buildpath)
out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase'],'commit':head,'branch':branch}))
