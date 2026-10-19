"""Check published patches against a temporary index at the pinned upstream base."""
import datetime,hashlib,json,os,subprocess
from pathlib import Path
out=Path('outerreset-patch-application-check.json');assert not out.exists();root=Path('experiments/outerreset-apply-check');assert not root.exists();root.mkdir(parents=True)
base='5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039';cases=[]
for candidate,expected in [('f401',(9,1)),('f402',(6,1))]:
 repo=Path('lrtdc-outerreset-'+candidate);patch=Path('outerreset-functional-'+candidate+'.patch');index=root/('index-'+candidate);env={**os.environ,'GIT_INDEX_FILE':str(index.resolve())}
 commands=[['git','-C',str(repo),'read-tree',base],['git','-C',str(repo),'apply','--cached','--check',str(patch.resolve())]];codes=[]
 for cmd in commands:
  c=subprocess.run(cmd,env=env,capture_output=True,text=True);codes.append(c.returncode);assert c.returncode==0,c.stderr
 c=subprocess.run(['git','-C',str(repo),'diff','--check',base,'--','hdl/toplevel.vhd'],capture_output=True,text=True);assert c.returncode==0,c.stderr
 fields=subprocess.check_output(['git','-C',str(repo),'diff','--numstat',base,'--','hdl/toplevel.vhd'],text=True).split();assert tuple(map(int,fields[:2]))==expected
 cases.append({'candidate':candidate,'base_commit':base,'patch':str(patch),'patch_sha256':hashlib.sha256(patch.read_bytes()).hexdigest(),'temporary_index_read_tree_actual_exit_code':codes[0],'cached_patch_check_actual_exit_code':codes[1],'whitespace_check_actual_exit_code':c.returncode,'git_added_lines':expected[0],'git_deleted_lines':expected[1],'top_sha256':hashlib.sha256((repo/'hdl/toplevel.vhd').read_bytes()).hexdigest()})
r={'created':datetime.datetime.now().isoformat(),'phase':'both_functional_patches_apply_cleanly_to_pinned_upstream_base','hardware_operations':False,'cases':cases,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limits':['Temporary Git index only. No candidate working-tree source or real repository index was changed.','Clean patch application does not imply hardware success; qualification and boot cohorts are separate.']}
out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase']}))
