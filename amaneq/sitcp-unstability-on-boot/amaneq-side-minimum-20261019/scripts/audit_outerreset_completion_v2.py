"""Require the functional commit in addition to the completed hardware/local audit."""
import datetime,hashlib,json,subprocess
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
out=Path('outerreset-local-completion-audit-v2.json');assert not out.exists()
priorpath=Path('outerreset-local-completion-audit.json');prior=load(priorpath);assert prior['phase']=='local_completion_checks_passed'
for p,h in prior['source_sha256'].items():assert sha(p)==h,p
cp=Path('outerreset-final-source-commit.json');c=load(cp);assert c['phase']=='validated_functional_source_committed_locally'
selection=load('outerreset-result-selection.json');assert c['candidate']==selection['selected_candidate']
repo=Path(c['repository']);top=repo/'hdl/toplevel.vhd'
assert sha(top)==c['compiled_top_sha256_unchanged']
assert sha(c['compiled_top_build_proof'])==c['compiled_top_build_proof_sha256']
b=load(c['compiled_top_build_proof']);assert b['actual_exit_code']==0 and b['phase']=='build_complete_independent_review_required'
assert {h for p,h in b['source_sha256'].items() if Path(p).resolve()==top.resolve()}=={sha(top)}
def git(*args):return subprocess.check_output(['git','-C',str(repo),*args])
assert git('rev-parse','HEAD').decode().strip()==c['commit']
assert git('rev-parse','HEAD^').decode().strip()==c['parent']=='5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039'
assert git('diff','--name-only',c['parent'],c['commit']).decode().splitlines()==['hdl/toplevel.vhd']
assert git('show','HEAD:hdl/toplevel.vhd')==top.read_bytes().replace(b'\r\n',b'\n')
assert not git('diff','--cached','--name-only').strip()
extra=[Path(__file__),priorpath,cp,Path(c['compiled_top_build_proof']),Path('outerreset-study-final.md')]
result={**prior,'created':datetime.datetime.now().isoformat(),'functional_source_commit_mandatory_and_verified':True,'functional_source_commit':c['commit'],'supersedes_optional_commit_audit':str(priorpath),'source_sha256':{**prior['source_sha256'],**{str(p):sha(p) for p in extra}}}
out.write_text(json.dumps(result,indent=2));print(json.dumps({'phase':result['phase'],'cohorts':result['cohort_reports_checked'],'source_commit_mandatory':True,'commit':c['commit']}))
