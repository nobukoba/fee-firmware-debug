library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

library mylib;

entity RstDelayTimer is
  generic(
    constant kWidthCounter : integer:= 32
  );
  port (
    rstIn         : in std_logic;
    preSetVal     : in std_logic_vector(kWidthCounter-1 downto 0);
    clk           : in std_logic;
    readyOut      : out std_logic;
    delayRstOut   : out std_logic
    );
end RstDelayTimer;

architecture RTL of RstDelayTimer is

  -- System --

  -- signal decralation -----------------------------------------------------
  signal reg_reset    : std_logic:= '1';
  signal reg_counter  : std_logic_vector(kWidthCounter-1 downto 0);

begin
  -- ====================== body ============================= --
  delayRstOut <= reg_reset;
  readyOut    <= not reg_reset;

  process(clk, rstIn)
  begin
    if(rstIn = '1') then
      reg_reset     <= '1';
      reg_counter   <= preSetVal;
    elsif(clk'event and clk = '1') then
      if(unsigned(reg_counter) = 0) then
        reg_reset     <= '0';
      else
        reg_reset     <= '1';
        reg_counter   <= std_logic_vector(unsigned(reg_counter) -1);
      end if;
    end if;
  end process;

end RTL;
