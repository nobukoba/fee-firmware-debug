"""Independent source/route/truth-table/timing/image qualification before hardware."""
import argparse,collections,datetime,hashlib,importlib.util,json,re,sys,tkinter,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
import flash_firmware
ap=argparse.ArgumentParser();ap.add_argument('--candidate',choices=['f401','f402'],required=True);a=ap.parse_args();tag='outerreset-'+a.candidate
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=Path(tag+'-independent-review.json');assert not out.exists();bp=Path(tag+'-export.json');b=json.loads(bp.read_text());assert b['phase']=='matched_export_complete_independent_review_required' and b['actual_exit_code']==0
for p,h in {**b['source_sha256'],**b['artifacts']}.items():assert sha(p)==h,p
basepath=Path(tag+'-base-review.json');base=json.loads(basepath.read_text());assert base['phase']=='base_review_passed_fresh_routed_netlist_review_required'
for p,h in base['source_sha256'].items():assert sha(p)==h,p
cfgpath=Path(tag+'-netlist-config.json');cfg=json.loads(cfgpath.read_text());assert cfg['phase']=='fresh_netlist_configuration_reviewed';root=Path(cfg['root']);variants={};reference=None;routes=None
spec=importlib.util.spec_from_file_location('outerreset_matched_inspector',flash_firmware.INSPECTOR);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
gate=cfg['gate'];pins=cfg['input_roles'];inversions=cfg['input_inversions'];assert set(pins)==set(inversions)=={'I0','I1','I2'} and all(type(v) is bool for v in inversions.values())
assert set(pins.values())==({'por','wait','end'} if a.candidate=='f401' else {'raw','wait','por'})
allowed={'enabled','bypass','hold'} if a.candidate=='f401' else {'enabled','bypass','early'}
assert {'enabled','bypass'}.issubset(cfg['variant_inits_decimal']) and set(cfg['variant_inits_decimal']).issubset(allowed)
expected_inits={}
for variant in cfg['variant_inits_decimal']:
 value=0
 for index in range(8):
  v={role:((index>>int(pin[1:]))&1)^int(inversions[pin]) for pin,role in pins.items()}
  enabled=(v['por'] or ((not v['wait']) and v['end'])) if a.candidate=='f401' else (v['raw'] or ((not v['wait']) and v['por']))
  bit=enabled if variant=='enabled' else (v['por'] if variant=='bypass' else (v['end'] if variant=='hold' else v['raw']))
  value|=int(bool(bit))<<index
 expected_inits[variant]=value
assert expected_inits==cfg['variant_inits_decimal']
for name,expected in expected_inits.items():
 folder=root/name;parser=tkinter.Tcl()
 def column(label,count=None):
  raw=(folder/label).read_text();return [raw.rstrip('\r\n')] if count==1 else list(parser.splitlist(raw))
 names,refs,locs,bels=[column('primitive-'+key+'.tcllist') for key in ['NAME','REF_NAME','LOC','BEL']]
 assert len(names)==len(set(names))==len(refs)==len(locs)==len(bels)
 inits={};counts=collections.Counter(refs)
 for kind in column('init-types.tcllist'):
  ns=column('init-'+kind+'-NAME.tcllist',counts[kind]);vs=column('init-'+kind+'-INIT.tcllist',counts[kind]);assert len(ns)==len(vs)
  for cell,value in zip(ns,vs):assert cell not in inits;inits[cell]=value
 indexed={cell:[ref,loc,bel,inits.get(cell,'')] for cell,ref,loc,bel in zip(names,refs,locs,bels)}
 assert indexed[gate][0]=='LUT3' and int(indexed[gate][-1].split("'h")[1],16)==expected
 normalized={k:v[:-1]+['MATCHED_RESET_GATE'] if k==gate else v for k,v in indexed.items()}
 with zipfile.ZipFile(folder/('lrtdc-'+a.candidate+'.dcp')) as archive:
  description=ET.fromstring(archive.read('dcp.xml'));members={item.attrib['Type']:item.attrib['Name'] for item in description.findall('File')}
  physical={key:{'member':members[key],'sha256':hashlib.sha256(archive.read(members[key])).hexdigest()} for key in ['PHYSDB_ROUTE','PHYSDB_DEVICE_NAME_STORE','PHYSDB_NEW_NETLIST_NAME_STORE','PHYSDB_CLOCK_DATA','SHAPE']}
 if reference is None:reference=normalized;routes=physical
 else:assert normalized==reference and physical==routes,'Primitive LOC/BEL/INIT or exact physical route mismatch'
 timing=(folder/'timing-summary.rpt').read_text();assert 'All user specified timing constraints are met.' in timing
 for category in ['no_clock','unconstrained_internal_endpoints','multiple_clock','loops']:assert re.search(r'checking '+category+r' \(0\)',timing)
 values=re.search(r'WNS\(ns\).*?\n\s*-+[^\n]*\n\s*([^\n]+)',timing,re.S).group(1).split();wns,whs=float(values[0]),float(values[4]);assert wns>=0 and whs>=0
 skews=re.findall(r'Slack \((MET|VIOLATED)\)\s*:\s*(-?[\d.]+)ns',(folder/'bus-skew.rpt').read_text());assert skews and all(t=='MET' and float(v)>=0 for t,v in skews)
 rows=re.findall(r'\|\s*([A-Z]+-\d+)\s*\|\s*(Warning|Critical Warning|Error)\s*\|[^|]*\|\s*(\d+)\s*\|',(folder/'drc.rpt').read_text());limits={'CHECK-3':1,'DPIP-1':384,'REQP-1839':12,'REQP-1840':20,'RTSTAT-10':1,'PDCN-1569':1};assert rows
 for key,severity,count in rows:assert severity=='Warning' and key in limits and int(count)<=limits[key],(key,severity,count)
 mcs=folder/('lrtdc-'+a.candidate+'.mcs');bit=folder/('lrtdc-'+a.candidate+'.bit');image=module.inspect_file(mcs);assert image.payload==module.inspect_file(bit).payload and image.idcode&0xfffffff==0x0364c093
 variants[name]={'mcs':str(mcs),'mcs_sha256':sha(mcs),'expected_full_flash_sha256':hashlib.sha256(image.payload.ljust(16777216,b'\xff')).hexdigest(),'gate_INIT':expected,'wns_ns':wns,'whs_ns':whs,'drc':rows}
clockpath=Path('outerreset-source-clock-audit-v2.json');clock=json.loads(clockpath.read_text());assert clock['phase']=='static_clock_reset_dependencies_checked_fresh_physical_audit_still_required'
boardpath=Path(tag+'-board-clock-audit.json');board=json.loads(boardpath.read_text());assert board['phase']=='generated_board_clock_settings_match_common_baseline'
for p,h in board['source_sha256'].items():assert sha(p)==h
sourcepath=Path('outerreset-source-input-audit.json');provenance=json.loads(sourcepath.read_text());assert provenance['phase']=='both_candidates_use_clean_pinned_submodule_sources'
for p,h in clock['source_sha256'].items():assert sha(p)==h
audit=(root/'fresh-clock-reset-audit.txt').read_text();assert 'PERIOD 8.000' in audit or 'PERIOD 8.0' in audit;assert 'RESET_SINKS' in audit and 'pma_reset_pipe' in audit
for phrase in ['CPLL_FBDIV 4\n','CPLL_FBDIV_45 4\n','CPLL_REFCLK_DIV 1\n','RXOUT_DIV 4\n','TXOUT_DIV 4\n','RX_DATA_WIDTH 20\n',"RXCDR_CFG 72'h03000023FF10100020\n"]:assert phrase in audit,phrase
for pin in ['RXSYSCLKSEL[0]','RXSYSCLKSEL[1]','TXSYSCLKSEL[0]','TXSYSCLKSEL[1]','RXCDRHOLD','RXPMARESET']:
 row=next(line for line in audit.splitlines() if line.startswith('GT_PIN '+pin+' NET '));assert row.endswith('/<const0>'),row
r={'created':datetime.datetime.now().isoformat(),'phase':'independent_review_passed_ready_for_hardware','runtime':base['runtime'],'variants':variants,'functional_patch':tag.replace('outerreset-','outerreset-functional-')+'.patch','functional_added_lines':base['functional_added_lines'],'functional_deleted_lines':base['functional_deleted_lines'],'matched_physical_archive_members':routes,'core_VHDL_sha256':base['core_VHDL_sha256'],'fresh_gate_input_roles':pins,'fresh_gate_input_inversions':inversions,'source_sha256':{str(p):sha(p) for p in [Path(__file__),bp,basepath,cfgpath,root/'fresh-clock-reset-audit.txt',clockpath,sourcepath,boardpath]},'limits':['Public core reset restarts the existing native PCS/TX/RX startup sequencing; it is not a direct independently timed GTX RXPMARESET pulse.','Native generated-IP functional HDL unchanged; common board clock fixes retained.','Enabled/bypass/optional hold or early controls share all primitive locations, BELs and INITs except one LUT, and all five physical DCP archive members byte-for-byte.','Only enabled corresponds to the listed production source patch. Hold/early are diagnostic controls with retained timer logic; they are not independently built shorter production source candidates.','No physical pulse waveform observer in this production-minimum image. Timing follows qualified RTL/scaled simulation/netlist, not an oscilloscope observation.','12s endpoint probe delay does not guarantee wire silence; Windows background ARP can still transmit.','Cold trials and packet correlation required; this review is not a hardware success result.']}
out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase'],'variants':list(variants),'added':r['functional_added_lines'],'deleted':r['functional_deleted_lines']}))
