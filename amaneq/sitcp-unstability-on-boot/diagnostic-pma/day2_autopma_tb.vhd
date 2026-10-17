library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.env.all;
entity day2_autopma_tb is end;
architecture test of day2_autopma_tb is
 signal sysclk,rxclk : std_logic := '0';
 signal soft : std_logic := '1';
 signal ready,rx_done,pulse : std_logic := '0';
 signal debug : std_logic_vector(7 downto 0);
 signal pulse_count : integer := 0;
begin
 sysclk<=not sysclk after 2.5 ns;
 rxclk<=not rxclk after 8 ns;
 dut:entity work.day2_autopma
 generic map(QUIET_CYCLES=>100,ACK_TIMEOUT=>1000,RECOVERY_TIMEOUT=>1000)
 port map(sysclk=>sysclk,rxclk=>rxclk,soft_reset=>soft,cpll_lock=>ready,
 tx_done=>ready,rx_done=>rx_done,native_rx_reset=>'0',native_tx_reset=>'0',native_pll_reset=>'0',pma_reset=>pulse,debug=>debug);
 pulse_check:process
  variable started:time;
 begin
  wait until rising_edge(pulse);started:=now;pulse_count<=pulse_count+1;
  wait until falling_edge(pulse);
  assert now-started=256 ns report "PMA pulse not exactly16 RX cycles" severity failure;
 end process;
 rx_model:process
 begin
  wait until ready='1';rx_done<='1';
  wait until pulse='1';rx_done<='0';
  wait until pulse='0';wait for 200 ns;rx_done<='1';
  wait until ready='0';rx_done<='0';
 end process;
 stimulus:process
 begin
  wait for 100 ns;soft<='0';
  wait for 200 ns;assert pulse_count=0 severity failure;ready<='1';
  wait for 480 ns;assert pulse_count=0 report "Pulse before quiet interval" severity failure;
  wait until debug(6)='1';wait for 50 ns;
  assert debug(7)='0' and debug(5)='1' and pulse_count=1 report "First request did not finish cleanly" severity failure;
  wait for 3 us;assert pulse_count=1 report "Repeated unrequested reset" severity failure;
  soft<='1';ready<='0';wait for 100 ns;soft<='0';
  wait for 1500 ns;assert pulse_count=1 and debug(6)='0' report "Reset emitted before readiness" severity failure;
  ready<='1';wait until debug(6)='1';wait for 50 ns;
  assert debug(7)='0' and pulse_count=2 report "SOFT reset did not rearm exactly once" severity failure;
  wait for 3 us;assert pulse_count=2 severity failure;
  report "DAY2_AUTOPMA_CONTRACT_PASS" severity note;stop;wait;
 end process;
 watchdog:process begin wait for 30 us;assert false report "Simulation timeout" severity failure;end process;
end architecture;
