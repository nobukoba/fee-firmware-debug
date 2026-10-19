"""Final local integrity and safe-state audit before private publication."""
import datetime,hashlib,json
from pathlib import Path
out=Path('outerreset-local-completion-audit.json');assert not out.exists()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8'))
restore=Path('outerreset-restoration.json');r=load(restore);assert r['phase']=='both_restored_full_readback_cold3_network_EEPROM_verified_power_on'
cleanup=Path('outerreset-resource-cleanup.json');c=load(cleanup);assert c['phase']=='capture_closed_sleep_inhibition_released_no_workers' and sha(c['capture'])==c['capture_sha256']
final=Path(r['final_status']);assert sha(final)==r['final_status_sha256'];f=load(final)
for host,baseline in [('192.168.10.16','341c5c207c91e51c634ba3e3090fea4689e4e5ae07725e4996a3e568b504c887'),('192.168.10.17','0657876d036a1b9c1ba34903bbf577d490741c851af11916d91efed7f1a1521e')]:
 b=f['boards'][host];assert b['first']['success'] and b['confirmation']['success'] and b['eeprom_matches_baseline'] and b['eeprom_sha256']==baseline
for target in r['targets']:
 b=r['boards'][target['suffix']];assert b['cold_successes']==3 and b['full_readback_sha256']==target['full_sha256']
 assert sha(b['flash_report'])==b['flash_report_sha256'] and sha(b['cold_log'])==b['cold_sha256']
 flash=load(b['flash_report']);assert flash['success'] and flash['image_matches'] and flash['readback_sha256']==target['full_sha256'] and flash['target_serial']==target['serial'] and sha(target['mcs'])==target['mcs_sha256']
 assert len(load(b['cold_log'])['trials'])==3
summary=Path('outerreset-cohort-summary-final.json');s=load(summary);assert s['phase']=='all_completed_outerreset_cohorts_checked'
for p,h in s['source_sha256'].items():assert sha(p)==h
for case in s['cases']:
 if case['candidate']=='factory':continue
 review=load('outerreset-'+case['candidate']+'-independent-review.json');assert review['phase']=='independent_review_passed_ready_for_hardware' and review['variants'][case['variant']]['expected_full_flash_sha256']==case['full_flash_sha256']
 for p,h in review['source_sha256'].items():assert sha(p)==h
packets=Path('outerreset-packets-final.json');pk=load(packets);assert pk['phase']=='closed_capture_boot_packet_correlation_complete' and pk['capture_sha256']==c['capture_sha256'] and not pk['skipped_incomplete']
for p,h in pk['source_sha256'].items():assert sha(p)==h
soaks=list(Path('.').glob('outerreset-soak-*.json'))+[Path('outerreset-final-soak-summary.json')];negative_soaks=[]
for p in soaks:
 t=load(p)
 for q,h in t['source_sha256'].items():assert sha(q)==h
 if t['phase']=='STOPPED_NEEDS_INSPECTION':
  assert p.name!='outerreset-final-soak-summary.json' and t['error'];negative_soaks.append(str(p))
  assert all(0<=v['RBCP_pass']<=v['RBCP_checks'] and 0<=v['TCP_pass']<=v['TCP_checks'] for v in t['counts'].values())
 else:
  assert t['phase'] in ['read_only_candidate_soak_completed_both_healthy','read_only_soak_completed_both_healthy'] and t['elapsed_seconds']>=t['requested_seconds']
  assert all(v['failures']==0 and v['RBCP_checks']==v['RBCP_pass']==t['requested_seconds']//30 and v['TCP_checks']==v['TCP_pass'] for v in t['counts'].values())
evidence=[Path(__file__),restore,cleanup,final,summary,packets,*soaks]
selection=load('outerreset-result-selection.json')
timer_path=Path('outerreset-'+selection['selected_candidate']+'-timer-init-audit.json')
timer=load(timer_path)
assert timer['phase']=='physical_timer_counter_and_reset_output_initial_values_verified'
for p,h in timer['source_sha256'].items():assert sha(p)==h
evidence.extend([Path('outerreset-result-selection.json'),timer_path])
for name in ['outerreset-native-reset-sequence-analysis.json','outerreset-f402-causal-contrast.json','outerreset-existing-timer-output-analysis.json','outerreset-board17-regression-reversal.json']:
 p=Path(name);record=load(p)
 for q,h in record['source_sha256'].items():assert sha(q)==h
 evidence.append(p)
commit=Path('outerreset-final-source-commit.json')
if commit.exists():
 source=load(commit);assert source['phase']=='validated_functional_source_committed_locally' and sha(Path(source['repository'])/'hdl/toplevel.vhd')==source['compiled_top_sha256_unchanged'];evidence.append(commit)
result={'created':datetime.datetime.now().isoformat(),'phase':'local_completion_checks_passed','restored_both_cold3_full_flash_EEPROM_runtime_network':True,'capture_valid_closed_and_sleep_inhibition_released':True,'cohort_reports_checked':len(s['cases']),'packet_boot_windows_checked':len(pk['cases']),'negative_boots_without_actual_ARP':sum(not v['success'] and not v['request_frames'] for v in pk['cases']),'soaks_checked':len(soaks),'negative_candidate_soaks_preserved':negative_soaks,'source_sha256':{str(p):sha(p) for p in evidence},'limits':['Negative endpoint outcomes remain recorded, including any without a transmitted ARP request. They are not silently reclassified as analog receiver failures.','Not external-input TDC calibration/performance validation.','Separate remote publication verification required after commit and push.']}
out.write_text(json.dumps(result,indent=2));print(json.dumps({'phase':result['phase'],'cohorts':len(s['cases'])}))
