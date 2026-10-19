"""Read private repository metadata using the same Git credential helper as fetch.

Credentials remain in memory and are never logged, serialized or exported.
"""
import json,subprocess,urllib.request
from pathlib import Path

def metadata():
 repo=Path('fee-firmware-debug')
 c=subprocess.run(['git','-C',str(repo),'credential','fill'],input='protocol=https\nhost=github.com\npath=nobukoba/fee-firmware-debug\n\n',capture_output=True,text=True,timeout=30)
 assert c.returncode==0,'Credential helper failed; its output must not be logged'
 values=dict(line.split('=',1) for line in c.stdout.splitlines() if '=' in line)
 assert values.get('password'),'No existing GitHub credential available'
 request=urllib.request.Request('https://api.github.com/repos/nobukoba/fee-firmware-debug',headers={'Authorization':'Bearer '+values['password'],'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'AMANEQ-firmware-study'})
 with urllib.request.urlopen(request,timeout=30) as response:result=json.load(response)
 assert result['full_name'].casefold()=='nobukoba/fee-firmware-debug'
 return {'full_name':result['full_name'],'isPrivate':result['private'],'default_branch':result['default_branch']}

if __name__=='__main__':print(json.dumps(metadata()))
