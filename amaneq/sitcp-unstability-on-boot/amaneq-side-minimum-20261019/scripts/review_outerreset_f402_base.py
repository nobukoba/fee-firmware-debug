"""Offline source, timing and image review; does not authorize hardware alone."""
import datetime,difflib,hashlib,importlib.util,json,re,sys
from pathlib import Path
import flash_firmware
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=Path('outerreset-f402-base-review.json');assert not out.exists()
bp=Path('outerreset-f402-build.json');b=json.loads(bp.read_text());assert b['phase']=='build_complete_independent_review_required' and b['actual_exit_code']==0
for p,h in {**b['source_sha256'],**b['artifacts']}.items():assert sha(p)==h,p
repo=Path('lrtdc-outerreset-f402');folder=repo/'build/outerreset-f402'
before=(repo/'patch-check/toplevel-before.vhd').read_text();after=(repo/'hdl/toplevel.vhd').read_text()
assert after==(repo/'patch-check/toplevel-after.vhd').read_text()
patch=''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/hdl/toplevel.vhd',tofile='b/hdl/toplevel.vhd'))
assert patch==Path('outerreset-functional-f402.patch').read_text()
added=sum(x.startswith('+') and not x.startswith('+++') for x in patch.splitlines());deleted=sum(x.startswith('-') and not x.startswith('---') for x in patch.splitlines());assert (added,deleted)==(6,1)
base=Path('lrtdc-startdelay-f305/ip/gig_ethernet_pcs_pma/synth');generated=repo/'ip/gig_ethernet_pcs_pma/synth';core={}
for p in base.rglob('*.vhd'):
 rel=p.relative_to(base);q=generated/rel
 reference=Path('lrtdc-minimal-inithold/build/minimal-inithold-f304/rx-startup-before-patch.vhd') if rel.name=='gig_ethernet_pcs_pma_rx_startup_fsm.vhd' else p
 assert q.read_text()==reference.read_text(),'Generated GT startup HDL changed:'+str(rel)
 core[str(rel)]=sha(q)
assert len(core)==13
simpath=Path('experiments/outerreset-f402-sim/result.json');sim=json.loads(simpath.read_text());assert sim['passed']
for p,h in sim['source_sha256'].items():assert sha(p)==h
timing=(folder/'timing-summary.rpt').read_text();assert 'All user specified timing constraints are met.' in timing
for name in ['no_clock','unconstrained_internal_endpoints','multiple_clock','loops']:assert re.search(r'checking '+name+r' \(0\)',timing)
values=re.search(r'WNS\(ns\).*?\n\s*-+[^\n]*\n\s*([^\n]+)',timing,re.S).group(1).split();wns,whs=float(values[0]),float(values[4]);assert wns>=0 and whs>=0
skews=re.findall(r'Slack \((MET|VIOLATED)\)\s*:\s*(-?[\d.]+)ns',(folder/'bus-skew.rpt').read_text());assert skews and all(t=='MET' and float(v)>=0 for t,v in skews)
rows=re.findall(r'\|\s*([A-Z]+-\d+)\s*\|\s*(Warning|Critical Warning|Error)\s*\|[^|]*\|\s*(\d+)\s*\|',(folder/'drc.rpt').read_text());limits={'CHECK-3':1,'DPIP-1':384,'REQP-1839':12,'REQP-1840':20,'RTSTAT-10':1,'PDCN-1569':1};assert rows
for name,severity,count in rows:assert severity=='Warning' and name in limits and int(count)<=limits[name],(name,severity,count)
spec=importlib.util.spec_from_file_location('outerreset_inspector',flash_firmware.INSPECTOR);module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
mcs=folder/'lrtdc-outerreset-f402.mcs';image=module.inspect_file(mcs);assert image.payload==module.inspect_file(folder/'lrtdc-outerreset-f402.bit').payload and image.idcode&0xfffffff==0x0364c093
r={'created':datetime.datetime.now().isoformat(),'phase':'base_review_passed_fresh_routed_netlist_review_required','runtime':'0x60C4F402','functional_added_lines':added,'functional_deleted_lines':deleted,'wns_ns':wns,'whs_ns':whs,'drc':rows,'core_VHDL_sha256':core,'mcs_sha256':sha(mcs),'expected_full_flash_sha256':hashlib.sha256(image.payload.ljust(16777216,b'\xff')).hexdigest(),'source_sha256':{str(p):sha(p) for p in [Path(__file__),bp,simpath,Path('outerreset-functional-f402.patch'),folder/'timing-summary.rpt',folder/'bus-skew.rpt',folder/'drc.rpt']},'limits':['Full-source build with native RX FSM; common board156.25MHz CPLL/XDC settings retained.','Timer simulation uses scaled counts, does not model analog CDR.','Fresh physical netlist and matched enabled/bypass qualification still required before hardware.']}
out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase'],'WNS':wns,'WHS':whs}))
