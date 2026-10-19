"""Scaled-cycle contract for the one-timer AMANEQ minimization experiment."""
import datetime,hashlib,json,re,subprocess
from pathlib import Path
folder=Path('experiments/outerreset-f402-sim');assert not folder.exists();folder.mkdir(parents=True)
timer=Path('lrtdc-outerreset-f402/hdl/common/main/RstDelayTimer.vhd');(folder/'timer.vhd').write_bytes(timer.read_bytes())
tb='''library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity outerreset_tb is end;
architecture sim of outerreset_tb is
 signal clk:std_logic:='0';signal raw:std_logic:='1';
 signal early,por,r:std_logic;signal pulses:natural:=0;
begin
 clk<=not clk after 4 ns;
 global_por:entity work.RstDelayTimer port map(raw,std_logic_vector(to_unsigned(20,32)),clk,open,por);
 wait_early:entity work.RstDelayTimer port map(raw,std_logic_vector(to_unsigned(8,32)),clk,open,early);
 r<=raw or((not early)and por);
 process variable t:time;begin
  for trial in 1 to 2 loop
   wait until raw='0';wait for 1 ns;
   assert r='0' and por='1' report "Early release must leave global POR asserted" severity failure;
   wait until r='1';t:=now;pulses<=pulses+1;
   assert early='0' and por='1' report "Wrong reset window" severity failure;
   wait until r='0';
   assert now-t=96 ns report "Pulse must equal global/new preset difference" severity failure;
   assert por='0' report "Reset must end at existing global POR release" severity failure;
   wait for 200 ns;assert r='0' report "Unexpected repeat" severity failure;
  end loop;
  assert pulses=2 report "One reset per raw POR" severity failure;
  report "OUTERRESET_F402_CONTRACT_PASS" severity note;std.env.stop;wait;
 end process;
 process begin wait for 21 ns;raw<='0';wait for 500 ns;raw<='1';wait for 1 ns;assert r='1' report "Raw reset not forwarded" severity failure;wait for 18 ns;raw<='0';wait;end process;
 process begin wait for 2 us;assert false report "Watchdog" severity failure;end process;
end;
'''
(folder/'tb.vhd').write_text(tb)
commands=[[r'C:\Xilinx\Vivado\2023.2\bin\xvhdl.bat','--2008','timer.vhd','tb.vhd'],[r'C:\Xilinx\Vivado\2023.2\bin\xelab.bat','outerreset_tb','-s','outerreset_sim'],[r'C:\Xilinx\Vivado\2023.2\bin\xsim.bat','outerreset_sim','-runall']]
r={'created':datetime.datetime.now().isoformat(),'passed':False,'commands':[],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),timer,folder/'timer.vhd',folder/'tb.vhd']},'real_design_math':{'clock_MHz':125,'new_timer_preset':125000000,'global_timer_preset':268435455,'second_reset_SYS_cycles':143435455,'second_reset_seconds':1.14748364},'limits':['Scaled count simulation checks reset-free gap, retained global POR, one-shot width, parent reset rearming and no repeat.','Native analog GT acquisition not modeled.']}
try:
 for i,cmd in enumerate(commands):
  with (folder/f'{i}.console.txt').open('xb') as stream:c=subprocess.run(cmd,cwd=folder,stdout=stream,stderr=subprocess.STDOUT,timeout=240,creationflags=0x08000000)
  r['commands'].append({'command':cmd,'actual_exit_code':c.returncode});assert c.returncode==0
 text=(folder/'2.console.txt').read_text();assert 'OUTERRESET_F402_CONTRACT_PASS' in text and not re.search(r'^(Failure|Fatal|ERROR):',text,re.M);r['passed']=True
finally:(folder/'result.json').write_text(json.dumps(r,indent=2));print(json.dumps({'passed':r['passed']}),flush=True)
