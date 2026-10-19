"""Capture completed same-route timing contrast before independent F403 hardware."""
import datetime,hashlib,json
from pathlib import Path
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
reviewpath=Path('outerreset-f402-independent-review.json');review=load(reviewpath);assert review['phase']=='independent_review_passed_ready_for_hardware'
for p,h in review['source_sha256'].items():assert sha(p)==h
sources=[Path(__file__),reviewpath,Path('outerreset-f402-netlist-config.json'),Path('outerreset-packets-f402bypass-interim.json')];cases=[]
for label,variant,successes in [('outerf40216raw','early',3),('outerf40216a','enabled',3),('outerf40216by','bypass',0)]:
 p=Path('outerreset-cohort-'+label+'.json');r=load(p);assert r['phase']=='cohort_complete_power_on' and r['host']=='192.168.10.16' and r['variant']==variant and r['successes']==successes and len(r['trials'])==3
 assert sha(r['cold_log'])==r['cold_sha256'] and sha(r['flash_report'])==r['flash_report_sha256'] and r['full_flash_sha256']==review['variants'][variant]['expected_full_flash_sha256']
 sources.extend([p,Path(r['cold_log']),Path(r['flash_report'])]);cases.append({'variant':variant,'successes':successes,'trials':3,'report':str(p),'full_flash_sha256':r['full_flash_sha256']})
packets=load('outerreset-packets-f402bypass-interim.json');assert all(c['success'] or c['request_frames'] for c in packets['cases'])
out=Path('outerreset-f402-causal-contrast.json');assert not out.exists()
out.write_text(json.dumps({'created':datetime.datetime.now().isoformat(),'phase':'completed_same_route_early_enabled_bypass_comparison','cases':cases,'observed_order':['early3/3','enabled3/3','bypass0/3'],'interpretation':['For this F402 placed/routed netlist, raw early release alone passed whereas original delayed POR did not.','A second reset is not necessary in the F402 early diagnostic, although F401 second reset also recovers.','Qualifies a reset-order/timing dependence and motivates one-line independent source F403.'],'limits':['Early diagnostic retains unused timer/counter. Does not establish standalone one-line source efficacy.','No unique physical initiating cause or manufacturer-wide defect proved.','Long OFF, final reversal and independent F403 outcomes are separate later records.'],'source_sha256':{str(p):sha(p) for p in sources}},indent=2));print('F402 source-independent diagnostic contrast recorded')
