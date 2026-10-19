"""Version future tools without altering any controller already used in a cohort."""
from pathlib import Path
p=Path('run_outerreset_cohort_v3.py');assert not p.exists()
s=Path('run_outerreset_cohort_v2.py').read_text();s=s.replace("choices=['factory','f401','f402']","choices=['factory','f401','f402','f403']").replace('Only enabled is the production one-shot; hold/early are diagnostic controls. None is a late-fault watchdog.','Enabled is the source-built candidate; f403 is raw-reset routing without a one-shot. hold/early are diagnostic controls. No late-fault watchdog.')
p.write_text(s)
p=Path('audit_outerreset_timer_init_v3.py');assert not p.exists()
s=Path('audit_outerreset_timer_init.py').read_text().replace("choices=['f401','f402']","choices=['f401','f402','f403']")
s=s.replace("root=Path('outerreset-'+a.candidate+'-matched/enabled');", "root=(Path('lrtdc-outerreset-f403/build/outerreset-f403') if a.candidate=='f403' else Path('outerreset-'+a.candidate+'-matched/enabled'));")
s=s.replace("if a.candidate=='f401':expected", "if a.candidate=='f403':expected={'u_KeepPwrOnRst':268435455}\nif a.candidate=='f401':expected")
s=s.replace("Path('outerreset-'+a.candidate+'-export.json')", "Path('outerreset-'+a.candidate+('-inspection.json' if a.candidate=='f403' else '-export.json'))")
p.write_text(s)
