library ieee;
use ieee.std_logic_1164.all;
use std.env.all;
entity day2_autopma_fault_tb is end;
architecture test of day2_autopma_fault_tb is
 signal sysclk,rxclk : std_logic := '0';
 signal run_rx : boolean := false;
 signal soft,native_rx : std_logic := '1';
 signal pulse : std_logic;
 signal debug : std_logic_vector(7 downto 0);
 signal pulse_count : natural := 0;
begin
 sysclk<=not sysclk after 2.5 ns;
 rxclock:process begin
  wait for 8 ns;
  if run_rx then rxclk<=not rxclk;else rxclk<='0';end if;
 end process;
 dut:entity work.day2_autopma
 generic map(QUIET_CYCLES=>100,ACK_TIMEOUT=>200,RECOVERY_TIMEOUT=>200)
 port map(sysclk=>sysclk,rxclk=>rxclk,soft_reset=>soft,cpll_lock=>'1',
 tx_done=>'1',rx_done=>'1',native_rx_reset=>native_rx,native_tx_reset=>'0',
 native_pll_reset=>'0',pma_reset=>pulse,debug=>debug);
 count_pulses:process begin
  wait until rising_edge(pulse);pulse_count<=pulse_count+1;
 end process;
 stimulus:process begin
  -- No RX clock: request must time out rather than pulse indefinitely.
  wait for 100 ns;soft<='0';native_rx<='0';
  wait for 300 ns;native_rx<='1';wait for 100 ns;native_rx<='0';
  wait for 480 ns;
  assert debug(3)='0' and pulse_count=0 report "Readiness bounce did not restart quiet interval" severity failure;
  wait for 2 us;
  assert debug(7)='1' and debug(6)='0' and debug(3)='0' and pulse_count=0
    report "Missing RX clock did not end with bounded ACK timeout" severity failure;
  -- A clock arriving after the expired request must not cause a stale pulse.
  run_rx<=true;wait for 1 us;
  assert pulse_count=0 report "Expired request caused stale pulse after RX clock started" severity failure;
  -- With RX running but RXRESETDONE stuck high, physical reset may occur,
  -- but the controller must not report successful low-to-high recovery.
  soft<='1';wait for 200 ns;soft<='0';
  wait for 4 us;
  assert pulse_count=1 and debug(7)='1' and debug(6)='0' and debug(5)='0'
    report "Missing RXRESETDONE response was mistaken for success" severity failure;
  wait for 4 us;
  assert pulse_count=1 and pulse='0' and debug(3)='0'
    report "Failure caused repeated or stuck PMA reset" severity failure;
  report "DAY2_AUTOPMA_FAULT_CONTRACT_PASS" severity note;stop;wait;
 end process;
 watchdog:process begin wait for 30 us;assert false report "Fault simulation watchdog" severity failure;end process;
end architecture;
