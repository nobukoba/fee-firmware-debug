library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Diagnostic candidate: one sequential-mode PMA request after each SOFT reset.
-- The normal GTRESETSEL=0 and all native GTX/FSM reset connections are retained.
entity day2_autopma is
 generic (QUIET_CYCLES : positive := 200000000;
          ACK_TIMEOUT : positive := 200000;
          RECOVERY_TIMEOUT : positive := 1000000);
 port (sysclk, rxclk, soft_reset : in std_logic;
       cpll_lock, tx_done, rx_done, native_rx_reset, native_tx_reset, native_pll_reset : in std_logic;
       pma_reset : out std_logic;
       debug : out std_logic_vector(7 downto 0));
end entity;

architecture rtl of day2_autopma is
 signal ready_s1, ready_s2 : std_logic_vector(5 downto 0) := (others=>'0');
 signal req, req_s1, req_s2, serviced, ack, ack_s1, ack_s2 : std_logic := '0';
 signal pulse : std_logic := '0';
 signal remaining : integer range 0 to 16 := 0;
 signal state : integer range 0 to 3 := 0;
 signal quiet_count : integer range 0 to QUIET_CYCLES := 0;
 signal ack_count : integer range 0 to ACK_TIMEOUT := 0;
 signal recovery_count : integer range 0 to RECOVERY_TIMEOUT := 0;
 signal saw_rx_low, finished, timed_out : std_logic := '0';
 attribute ASYNC_REG : string;
 attribute ASYNC_REG of ready_s1, ready_s2, req_s1, req_s2, ack_s1, ack_s2 : signal is "TRUE";
 attribute DONT_TOUCH : string;
 attribute DONT_TOUCH of pulse, saw_rx_low, finished, timed_out : signal is "TRUE";
begin
 pma_reset <= pulse;
 debug <= timed_out & finished & saw_rx_low & ack_s2 & req & pulse & std_logic_vector(to_unsigned(state,2));

 process(rxclk)
 begin
  if rising_edge(rxclk) then
   req_s1 <= req; req_s2 <= req_s1;
   if remaining > 0 then
    if remaining = 1 then
     remaining <= 0; pulse <= '0'; ack <= '1';
    else remaining <= remaining-1;
    end if;
   elsif req_s2='0' then
    serviced <= '0'; ack <= '0'; pulse <= '0';
   elsif serviced='0' then
    serviced <= '1'; pulse <= '1'; remaining <= 16;
   end if;
  end if;
 end process;

 process(sysclk)
 begin
  if rising_edge(sysclk) then
   ready_s1 <= cpll_lock & tx_done & rx_done & native_rx_reset & native_tx_reset & native_pll_reset;
   ready_s2 <= ready_s1;
   ack_s1 <= ack; ack_s2 <= ack_s1;
   if soft_reset='1' then
    state<=0;req<='0';quiet_count<=0;ack_count<=0;recovery_count<=0;
    saw_rx_low<='0';finished<='0';timed_out<='0';
   else
    case state is
     when 0 =>
      if ready_s2="111000" then
       if quiet_count=QUIET_CYCLES-1 then req<='1';state<=1;ack_count<=0;
       else quiet_count<=quiet_count+1;
       end if;
      else quiet_count<=0;
      end if;
     when 1 =>
      if ready_s2(3)='0' then saw_rx_low<='1';end if;
      if ack_s2='1' then req<='0';state<=2;recovery_count<=0;
      elsif ack_count=ACK_TIMEOUT-1 then req<='0';timed_out<='1';state<=3;
      else ack_count<=ack_count+1;
      end if;
     when 2 =>
      if ready_s2(3)='0' then saw_rx_low<='1';end if;
      if saw_rx_low='1' and ready_s2(3)='1' then finished<='1';state<=3;
      elsif recovery_count=RECOVERY_TIMEOUT-1 then timed_out<='1';state<=3;
      else recovery_count<=recovery_count+1;
      end if;
     when others => req<='0';
    end case;
   end if;
  end if;
 end process;
end architecture;
