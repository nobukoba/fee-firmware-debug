"""Verify copied submodule inputs against clean pinned upstream checkouts."""
import datetime,hashlib,json,subprocess
from pathlib import Path
out=Path('outerreset-source-input-audit.json');assert not out.exists();base='5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039';modules={}
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['utility','common','strtdc','mikumari','laccp','bbt-sitcp-core']:
 reference=Path('lrtdc-startup-fix/hdl')/name;expected=git('lrtdc-outerreset-f401','ls-tree','HEAD','hdl/'+name).decode().split()[2]
 assert git(reference,'rev-parse','HEAD').decode().strip()==expected
 assert not git(reference,'status','--porcelain').strip(),name
 files=git(reference,'ls-files','-z').decode().strip('\0').split('\0');verified={}
 for relative in files:
  p=reference/relative;assert p.is_file(),'Nested gitlink requires explicit review:'+str(p)
  h=sha(p)
  for candidate in ['f401','f402']:assert sha(Path('lrtdc-outerreset-'+candidate)/'hdl'/name/relative)==h,(candidate,name,relative)
  verified[relative]=h
 modules[name]={'pinned_commit':expected,'reference_clean':True,'files_sha256':verified}
for candidate in ['f401','f402']:
 repo=Path('lrtdc-outerreset-'+candidate);assert git(repo,'rev-parse','HEAD').decode().strip()==base
 # Compare project inputs outside the functional top/version files, using committed blobs.
 for relative in ['project.tcl','user-setting.tcl','.gitmodules']:
  text=(repo/relative).read_text();assert text==git(repo,'show','HEAD:'+relative).decode().replace('\r\n','\n'),(candidate,relative)
r={'created':datetime.datetime.now().isoformat(),'phase':'both_candidates_use_clean_pinned_submodule_sources','upstream':'https://github.com/AMANEQ-official/StrLrTdc','base_commit':base,'submodules':modules,'script_sha256':sha(__file__),'limits':['Generated IP outputs are checked separately after each build. Common156.25MHz board settings are baseline, not a new functional startup patch.','Source provenance check, not a substitute for STA/DRC or physical tests.']}
out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase'],'modules':{k:len(v['files_sha256']) for k,v in modules.items()}}))
