"""Prevent system sleep only while this investigation runs; no persistent settings."""
import ctypes,datetime,time
from pathlib import Path
stop=Path('outerreset-stop-keepawake');assert not stop.exists()
deadline=datetime.datetime.fromisoformat('2026-10-19T11:30:00')
assert ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
print('Temporary system-sleep inhibition active until investigation stop or deadline',flush=True)
try:
 while datetime.datetime.now()<deadline and not stop.exists():time.sleep(2)
finally:
 ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
 print('Temporary system-sleep inhibition released',flush=True)
