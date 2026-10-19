"""Exercise existing timer one-shot with scaled periods; count-based real duration proof."""
import datetime,hashlib,json,re,subprocess
from pathlib import Path
folder=Path('experiments/outerreset-f401-sim');assert not folder.exists();folder.mkdir(parents=True)
timer=Path('lrtdc-outerreset-f401/hdl/common/main/RstDelayTimer.vhd');(folder/'timer.vhd').write_bytes(timer.read_bytes())
tb='''library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity outerreset_tb is end;
architecture sim of outerreset_tb is
 signal clk:std_logic:='0'; signal por:std_logic:='1';
 signal a,b,r:std_logic;signal pulses:natural:=0;
begin
 clk<=not clk after4 ns;
 wait_a:entity work.RstDelayTimer port map(por,std_logic_vector(to_unsigned(8,32)),clk,open,a);
 wait_b:entity work.RstDelayTimer port map(por,std_logic_vector(to_unsigned(12,32)),clk,open,b);
 r<=por or((not a)and b);
 process variable t:time;begin
  wait until por='0';wait for1 ns;assert r='0' report"No reset-free gap" severity failure;
  wait until r='1';t:=now;pulses<=pulses+1;
  assert a='0' and b='1' report"Wrong timerwindow" severity failure;
  wait until r='0';assert now-t=32 ns report"Pulse not4 SYS cycles" severity failure;
  wait for200 ns;assert r='0' report"Unexpected repeat" severity failure;
  wait until por='1';wait for1 ns;assert r='1' report"Parent reset notforwarded" severity failure;
  wait until por='0';wait until r='1';t:=now;pulses<=pulses+1;
  wait until r='0';assert now-t=32 ns report"Rearmed pulse wrongwidth" severity failure;
  wait for200 ns;assert r='0' and pulses=2 report"One pulse perPOR notrespected" severity failure;
  report"OUTERRESET_F401_CONTRACT_PASS" severity note;std.env.stop;wait;
 end process;
 process begin wait for21 ns;por<='0';wait for400 ns;por<='1';wait for19 ns;por<='0';wait;end process;
 process begin wait for2 us;assert false report"Watchdog" severity failure;end process;
end;
'''
# Avoid relying on permissive lexical parsing of adjacent VHDL tokens.
tb=re.sub(r'\bafter(?=\d)','after ',tb);tb=re.sub(r'\bfor(?=\d)','for ',tb)
(folder/'tb.vhd').write_text(tb)
commands=[[r'C:\Xilinx\Vivado\2023.2\bin\xvhdl.bat','--2008','timer.vhd','tb.vhd'],[r'C:\Xilinx\Vivado\2023.2\bin\xelab.bat','outerreset_tb','-s','outerreset_sim'],[r'C:\Xilinx\Vivado\2023.2\bin\xsim.bat','outerreset_sim','-runall']]
report={'created':datetime.datetime.now().isoformat(),'passed':False,'commands':[],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),timer,folder/'timer.vhd',folder/'tb.vhd']},'real_design_math':{'clock_MHz':125,'first_preset':125000000,'second_preset':137500000,'reset_free_SYS_edges_before_pulse':125000001,'pulse_width_SYS_cycles':12500000,'pulse_seconds':.1},'limits':['Scaled-period simulation checks logic,asynchronousPOR,reset-freegap,pulsewidth,rearming,andnoautonomousrepeat. Realpresets checkedarithmetically.','No analogGTX,PCS orhardware efficacy model.']}
try:
 for i,cmd in enumerate(commands):
  with (folder/f'{i}.console.txt').open('xb') as stream:c=subprocess.run(cmd,cwd=folder,stdout=stream,stderr=subprocess.STDOUT,timeout=240,creationflags=0x08000000)
  report['commands'].append({'command':cmd,'actual_exit_code':c.returncode});assert c.returncode==0
 text=(folder/'2.console.txt').read_text();assert 'OUTERRESET_F401_CONTRACT_PASS' in text and not re.search(r'^(Failure|Fatal|ERROR):',text,re.M);report['passed']=True
finally:(folder/'result.json').write_text(json.dumps(report,indent=2));print(json.dumps({'passed':report['passed']}),flush=True)
