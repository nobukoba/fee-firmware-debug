library ieee;
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
