"""Aggregate only cohort parents; preserve separately named aggregate checkpoints."""
import argparse,datetime,hashlib,json
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists();cases=[];sources={};aggregates=[]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p in sorted(Path('.').glob('outerreset-cohort-*.json')):
 r=json.loads(p.read_text())
 if p.name.startswith('outerreset-cohort-summary-'):
  assert r['phase']=='all_completed_outerreset_cohorts_checked' and 'cases' in r and 'totals' in r
  aggregates.append(str(p));sources[str(p)]=sha(p);continue
 assert r['phase']=='cohort_complete_power_on',p
 assert r['cold_actual_exit_code']==0 and sha(r['cold_log'])==r['cold_sha256'] and sha(r['flash_report'])==r['flash_report_sha256']
 cold=json.loads(Path(r['cold_log']).read_text());assert cold['trials']==r['trials'];f=json.loads(Path(r['flash_report']).read_text());assert f['success'] and f['image_matches'] and f['target_serial']==r['serial'] and f['readback_sha256']==r['full_flash_sha256']
 for q,h in r['source_sha256'].items():assert sha(q)==h,(p,q)
 if not r['flash_reused']:assert r['flash_actual_exit_code']==0
 cases.append({'report':str(p),'host':r['host'],'candidate':r['candidate'],'variant':r['variant'],'runtime':r['runtime'],'full_flash_sha256':r['full_flash_sha256'],'successes':r['successes'],'trials':len(r['trials']),'off_seconds':[v['off_seconds'] for v in r['trials']],'first_ready_seconds':[v['first_ready_seconds'] for v in r['trials']],'neighbor_protocol':cold['neighbor_protocol'],'flash_reused':r['flash_reused']});sources[str(p)]=sha(p)
totals={}
for c in cases:
 key=c['candidate']+'/'+c['variant']+'/'+c['host'];v=totals.setdefault(key,{'successes':0,'trials':0,'reports':[]});v['successes']+=c['successes'];v['trials']+=c['trials'];v['reports'].append(c['report'])
r={'created':datetime.datetime.now().isoformat(),'phase':'all_completed_outerreset_cohorts_checked','cases':cases,'totals':totals,'excluded_aggregate_checkpoints':aggregates,'source_sha256':{str(Path(__file__)):sha(__file__),**sources},'limits':['Only aggregate-namespaced files with their verified summary schema are excluded from cohort classification. Failed/incomplete real cohorts still fail this audit.','Original early native16 baseline and final restored cold3 are separate from standardized candidate cohort parents.','Observed boots, not a universal failure-rate bound.','Runtime alone does not distinguish matched controls; full-flash readback SHA does.','12s delayed active probing does not imply wire silence.']}
a.output.write_text(json.dumps(r,indent=2));print(json.dumps(totals))
