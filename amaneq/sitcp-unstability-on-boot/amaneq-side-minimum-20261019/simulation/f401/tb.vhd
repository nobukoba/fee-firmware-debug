library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity outerreset_tb is end;
architecture sim of outerreset_tb is
 signal clk:std_logic:='0'; signal por:std_logic:='1';
 signal a,b,r:std_logic;signal pulses:natural:=0;
begin
 clk<=not clk after 4 ns;
 wait_a:entity work.RstDelayTimer port map(por,std_logic_vector(to_unsigned(8,32)),clk,open,a);
 wait_b:entity work.RstDelayTimer port map(por,std_logic_vector(to_unsigned(12,32)),clk,open,b);
 r<=por or((not a)and b);
 process variable t:time;begin
  wait until por='0';wait for 1 ns;assert r='0' report"No reset-free gap" severity failure;
  wait until r='1';t:=now;pulses<=pulses+1;
  assert a='0' and b='1' report"Wrong timerwindow" severity failure;
  wait until r='0';assert now-t=32 ns report"Pulse not4 SYS cycles" severity failure;
  wait for 200 ns;assert r='0' report"Unexpected repeat" severity failure;
  wait until por='1';wait for 1 ns;assert r='1' report"Parent reset notforwarded" severity failure;
  wait until por='0';wait until r='1';t:=now;pulses<=pulses+1;
  wait until r='0';assert now-t=32 ns report"Rearmed pulse wrongwidth" severity failure;
  wait for 200 ns;assert r='0' and pulses=2 report"One pulse perPOR notrespected" severity failure;
  report"OUTERRESET_F401_CONTRACT_PASS" severity note;std.env.stop;wait;
 end process;
 process begin wait for 21 ns;por<='0';wait for 400 ns;por<='1';wait for 19 ns;por<='0';wait;end process;
 process begin wait for 2 us;assert false report"Watchdog" severity failure;end process;
end;
