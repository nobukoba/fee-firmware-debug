"""One hardware mutation owner; offline builds/capture remain independent."""
import os,subprocess
def assert_exclusive():
 pattern=r'(?:run_outerreset_(?:cohort|action|restore)(?:_v\d+)?|outerreset_final_soak|run_deepreset_(?:cohort|matched_cohort|factory_reverse|hold_cohort|hold_action|tx_meter)(?:_v\d+)?|restore_deepreset_study(?:_v\d+)?|deepreset_cold_extended(?:_v\d+)?|deepreset_soak|deepreset_final_soak|flash_firmware|dual_board_cold|run_minpma_cohort|run_minpma_native16|run_resetwidth_cohort)\.py'
 command=f"Get-CimInstance Win32_Process | Where-Object {{ $_.Name -eq 'python.exe' -and $_.ProcessId -ne {os.getpid()} -and $_.CommandLine -match '{pattern}' }} | Select-Object -ExpandProperty ProcessId | ConvertTo-Json -Compress"
 assert not subprocess.check_output(['powershell.exe','-NoProfile','-Command',command],text=True).strip(),'Another hardware/soak owner active'
