"""Check existing 156.25MHz board clock corrections against the common baseline."""
import argparse,datetime,hashlib,json,re
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--candidate',choices=['f401','f402'],required=True);a=ap.parse_args();out=Path('outerreset-'+a.candidate+'-board-clock-audit.json');assert not out.exists()
base=Path('lrtdc-startdelay-f305/ip/gig_ethernet_pcs_pma/synth');generated=Path('lrtdc-outerreset-'+a.candidate)/'ip/gig_ethernet_pcs_pma/synth';files={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['gig_ethernet_pcs_pma.xdc','gig_ethernet_pcs_pma_ooc.xdc']:
 p=generated/name;reference=base/name;assert p.read_text()==reference.read_text(),name;files[str(p)]=sha(p);files[str(reference)]=sha(reference)
assert '-name gtrefclk -period 6.400' in (generated/'gig_ethernet_pcs_pma_ooc.xdc').read_text()
assert '-period 12.800' in (generated/'gig_ethernet_pcs_pma.xdc').read_text()
p=generated/'transceiver/gig_ethernet_pcs_pma_gtwizard_gt.vhd';s=p.read_text();assert re.search(r'CPLL_FBDIV_45\s*=>\s*\(4\)',s) and re.search(r'CPLL_FBDIV\s*=>\s*\(4\)',s);files[str(p)]=sha(p)
r={'created':datetime.datetime.now().isoformat(),'phase':'generated_board_clock_settings_match_common_baseline','candidate':a.candidate,'GT_reference_MHz':156.25,'reference_period_ns':6.4,'GT_CPLL_FBDIV':4,'GT_CPLL_FBDIV_45':4,'source_sha256':{str(Path(__file__)):sha(__file__),**files},'limits':['Existing common board settings, excluded from the new functional startup-reset line count.','Unmodified XCI nominal reference settings alone are insufficient; generated GT HDL/XDC corrections are part of the established build flow.','Physical timer clock drivers and periods are checked separately from a fresh DCP.']}
out.write_text(json.dumps(r,indent=2));print(json.dumps({'phase':r['phase']}))
