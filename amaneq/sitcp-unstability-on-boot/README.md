# AMANEQ: SiTCP instability on cold boot

**Language: English | [日本語](README.ja.md)**

**Update (October 21):** the [HR reset policy comparison in LR-TDC](hr-reset-comparison-20261021/) records the CPLL-only wait, early-PHY policy, one-line comparison, and switch power-cycle tests on `.16`. Control `.11` stayed OFF and the jitter cleaner was disabled. The physical root cause remains unresolved.

Investigation dates: 2026-10-17–18 JST. Additional comparison tests and final restoration are complete. The physical root cause remains unresolved.

This page covers results through the morning of October 18. The afternoon [minimum-reset follow-up](minimum-reset-20261018/) is recorded separately.

**Update (October 19):** the [approximately ten-hour follow-up and short-fix comparison](deep-reset-20261018/) is complete. It records a three-location fix verified over 75 boots, negative one-line results, separate TX/RX clock measurements, host ARP retry confounding, and final restoration of both boards.

## Conclusions

The issue was narrowed to **GTX recovered-receive-clock acquisition / initialization state around RX/PMA/CDR**. In the bad state, the mean recovered-clock frequency ratio differed from normal; a PMA-only reset restored the ratio, valid reception, and SiTCP communication. Changing initial RX-reset hold prevented failure in same-placement/routing controls; reverting reproduced it.

**The physical reason that the problem board enters this state more readily remains unresolved.** These results do not identify a failed component, reference-clock jitter, or supply-rail startup as the cause. They are not presented as direct measurements of failed CDR lock.

## Boards and conditions

| Board | IP | Role |
|---|---|---|
| board16 | 192.168.10.16 | Frequently fails on cold boot |
| board17 | 192.168.10.17 | Healthy control |

The switch remained ON while board power was cycled individually. Remote switch-port control was unavailable; physical cable insertion after startup was not tested. Power, cable, EEPROM settings, and other paths differ between boards, so these results alone cannot establish board-specific silicon failure. FPGA IDCODEs matched. The user reported already testing multiple power supplies and cables. This motivates prioritizing on-board power/clock interactions with initialization, but component failure remains indistinguishable from insufficient initialization margin for otherwise normal unit variation.

## Decisive experiments

### 1. Recovered-clock comparison using the same diagnostic image

GTX output with `RXOUTCLKSEL=010` was observed, corresponding to `RXOUTCLKPMA` (recovered clock) in UG476. Earlier RX-recording clocks used shared TX-derived RXUSRCLK2; the two were distinguished.

Counters in each clock domain, Gray encoding, two-stage synchronization, and atomic snapshots measured SYS/GT-reference/RX ratios. Added diagnostics may affect placement, but bad state and PMA recovery were compared within the same diagnostic image. Diagnostics are excluded from the minimal-fix candidate.

| Condition | Trials | RX / GT-reference ratio |
|---|---:|---:|
| board16 bad state, mode change only | 3 | ~0.399729 |
| One PMA reset in the same bad state | 3 | ~0.4000126 |
| board17 normal startup | 3 | ~0.4000137 |

board16's ratio changed by about 709 ppm across PMA. Assuming nominal 200 MHz SYS, mean RX was about 62.456 MHz when bad and 62.500 MHz after recovery. board17 was about 62.502 MHz, but nominal errors of independent sources affect absolute comparisons; RX/GT-reference ratios are used between boards. This is not calibrated absolute-frequency measurement.

Fresh receive errors on board16 (normal bad state → mode only → PMA → mode restored):

| Trial | Bad state | Mode only | After PMA | After restoring mode |
|---|---:|---:|---:|---:|
| 1 | 103 | 104 | 0 | 0 |
| 2 | 112 | 109 | 0 | 0 |
| 3 | 71 | 126 | 0 | 0 |

PMA was a single 16-RX-clock pulse. RESETDONE deassertion and recovery confirmed acceptance. Other whole-GT, TX, CPLL, and PCS resets remained inactive, while CPLLLOCK and TXdone stayed stable. Communication recovery was reproduced; mode changes alone did not recover it.

PMA reset may internally affect CDR and other circuitry. Reserved CDR-reset signals and DRP changes were not used. RESETDONE-low duration is not a measurement of physical CDR lock time.

### 2. Intervention and reversal of initial RX-reset hold

With the same placement/routing and only the gate LUT INIT changed:

| Condition | Successful boots |
|---|---:|
| No initial hold | 0/3 |
| Initial 3 ms hold | 3/3 |
| Continuous hold | 3/3 |
| Fully restore original condition | 0/3 |

Another factor-separation experiment improved 3/3 with initial GT-side hold, while changing only a wait timer passed 0/3. Tested delay-only and CPLL initialization-order changes did not help. A simple long full-RX reset later in startup did not give the same result as initial hold. See [experiment-matrix.csv](experiment-matrix.csv).

Top-level global reset includes an approximately 2.147-second timer at nominal 125 MHz. The original RX FSM sets `gtrxreset_i='0'` during SOFT_RESET. This path is common to healthy and bad boards and alone does not explain unit variation. Initial 3 ms hold also worked, so holding for the entire 2.147 seconds has not been shown necessary. The 500 ns condition immediately after configuration has not been measured as an actual waveform.

### 3. Packet corroboration

In three separate single-PMA controls, host ARP requests appeared during the bad-state windows with no board response frames; ARP/RBCP/TCP responses followed PMA. Another control kept MAC/SiTCP reset asserted: fresh receive errors became zero after PMA and communication recovered after releasing that hold.

These are host-NIC captures, not switch mirroring or physical-signal measurements. Response latency includes host ARP retry waits and is not physical recovery time. Final capture-drop statistics were not yet established in these records. Raw PCAP is not included.

## Minimal candidate F304

The functional change consists of two assignments in the RX startup FSM:

```vhdl
-- Declaration initializer
signal gtrxreset_i : std_logic := '1'; -- Previously '0'

-- SOFT_RESET branch
gtrxreset_i <= '1';                  -- Previously '0'
```

Existing transitions/timers are reused; no monitoring/retry circuit is added. Version and build scripts also change, so the entire repository diff is not two lines. See the [generated HDL patch](minimal-f304.patch).

Comparison builds used Vivado 2023.2 and a shared post-regeneration procedure aligning GT attributes, including `CPLL_FBDIV_45=4`, and clock constraints with the existing Ethernet core. Reproduction must retain this consistency. Line counts refer to functional HDL after that shared procedure.

### Why was the original value 0, and what remains unresolved?

In the original vendor-generated FSM, SOFT_RESET returns the FSM to INIT; it is distinct from GTX GTRXRESET. INIT waits about 500 ns, ASSERT_ALL_RESETS first raises GTRXRESET, PLL lock is checked, and VERIFY_RECCLK_STABLE returns it to 0. The original 0 cannot therefore simply be called a typo. No source directly explaining the author's choice was found, but code confirms separation between waiting and actual reset assertion.

UG476's post-configuration RX sequence requires waiting at least 500 ns before asserting GTRXRESET and related signals, and not releasing GTRXRESET before the associated PLL locks. INIT=1 can assert earlier than that wait, so compliance of actual DONE/GT-reset timing remains unverified. Hardware boot success and logic simulation alone do not prove specification compliance. This is an effective candidate under the tested AMANEQ conditions, not a vendor-approved general fix or a guarantee of no side effects in every condition. Logic simulation completed after repeated SOFT_RESET; actual configuration timing, late cable insertion, and TDC precision require separate validation.

| Item | Value |
|---|---|
| Original repository | AMANEQ-official/StrLrTdc |
| Base commit | `5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039` |
| Local candidate commit | `3302acf26b9679c44ef5eea5651736377a8a2aea` |
| Runtime version | `0x60C4F304` |
| MCS SHA-256 | `15a95d87c6c6d301cac830d5f3d22fc6ed4229f9f609ee1b475ab95efe1fe912` |
| Full Flash readback SHA-256 (both boards match) | `99e79ca5f3397e060013f73209a2b4cecfe52e6407e5f64430eb1e5e248361b2` |

This does not imply the candidate commit was published upstream. Bitstreams, generated IP, and tool checkpoints are not included.

### Validation

Both board16 and board17 passed **15/15 power cycles**: three initial trials, three after reprogramming, seven additional 5-second OFF trials, one 60-second OFF trial, and one 600-second OFF trial. Each success was rechecked later for RBCP/TCP/version/IP. Full Flash readback and matching pre/post EEPROM reads were verified. OFF durations derive from commands and response confirmation, not supply-rail waveforms.

Simultaneous monitoring ran **2026-10-18 02:24:39–04:36:59 JST** and stopped normally for the user's next experiment request, before the planned 10:30 endpoint. Actual first-to-last probe spans were 7919.969 seconds on board16 and 7918.953 seconds on board17 (about 2 hours 12 minutes). Each passed RBCP **265/265** and TCP **27/27**, zero failures. Monitoring child processes exited normally. The parent required the planned duration and returned exit code 1 for early stopping; this is separate from communication failure. See [status.json](status.json).

Earlier board17-only F304 monitoring spanned 2 hours 48 minutes 37 seconds between probes, RBCP 338/338 and TCP 34/34, a separate interval. TDC precision, physical late cable insertion, and continuous full-packet BER remain unverified.

### Additional comparisons requested on 2026-10-18

- F305 changes only RX FSM `STARTUP_DELAY`, 500 ns → 5 µs.
- F306 changes the same constant to 50 µs.
- F307 retains original 500 ns/INIT0/SOFT0, waits for one second of PLL/RX/TX readiness and reset inactivity, then adds one automatic 16-RX-clock PMA pulse.

F307 retains normal sequential mode; subsequent internal resets may also occur, so distinguish it from earlier PMA isolation in single mode. Logic simulation checks readiness waiting, 16-clock width, one-shot operation, and rearming after SOFT_RESET. Simulation is recorded separately from implementation review and hardware power-cycle comparisons.

[PMA diagnostic RTL/testbenches](diagnostic-pma/) include normal/fault simulations. Fault models cover interrupted readiness, no RX clock from the start, and RXRESETDONE stuck high. They do not validate mid-operation clock loss or physical late cable insertion.

### Additional comparison results (2026-10-18)

F305 (5 µs wait) passed **0/3 on board16**, retaining INIT0/SOFT0 and changing only the wait constant. Full Flash readback matched. Even in failure, FPGA DONE/EOS were 1 and configuration CRC/ID errors and fallback were 0. Increasing this wait tenfold did not help under these conditions. Configuration-register PLL_LOCK differs from GTX CPLLLOCK/CDR lock.

Factory in the same series passed 1/3. Factory and fresh builds differ in placement/tool conditions, so this is not strict same-placement causality. F305 lacked recovered-clock instrumentation; the frequency offset seen in previous diagnostics was not directly confirmed on F305. See [reviewed F305 outcome](evidence/day2-f305-reviewed-outcome.json).

F306 (50 µs) also passed **0/3 on board16**. Full readback matched; after the third failure, DONE/EOS=1 and CRC/ID/fallback errors=0. Healthy board17 monitoring had no communication failures. See [reviewed F306 outcome](evidence/day2-f306-reviewed-outcome.json). About 71 minutes after the third trial, two read-only checks without reset/power intervention still received no RBCP reply. See [later communication checks](evidence/day2-f306-late-readonly-status.json) and [power readback](evidence/day2-f306-late-power-status.json). The supply reported output ON, 30 V/1 A settings; this is not a waveform measurement of on-board GT rails.

| Condition | board16 successful boots | Note |
|---|---:|---|
| Original factory, 500 ns | 1/3 | Tool/placement differ from fresh builds |
| F305, 5 µs, INIT0/SOFT0 | 0/3 | Only wait constant changed |
| F306, 50 µs, INIT0/SOFT0 | 0/3 | Only wait constant changed |

The tested 5/50 µs waits did not improve startup; this does not reject every wait value. F307 automatic-PMA enabled/disabled images with physical-PMA observation passed implementation/review. Hardware comparisons below include reversal to disabled and healthy .17 regression testing.

Functional generated-HDL diffs are one replacement each for F305/F306, and +104/−1 for F307. F307 includes an 87-line controller, wrapper connections, and debug signals. Counts exclude version, build procedures, comparison physical gate, and ILA. They do not establish a minimal PMA implementation. See [diff/count record](evidence/day2-functional-hdl-diffs.json), [F305 patch](day2-f305-functional-hdl.patch), [F306 patch](day2-f306-functional-hdl.patch), and [F307 patch](diagnostic-pma/day2-f307-functional-hdl.patch).

### F307 PMA enabled/disabled comparison

Original 500 ns/INIT0/SOFT0 and placement/routing were retained; only the gate LUT INIT immediately before the GT input changed. Original placed primitive names/types/LOC/BEL matched. Both variants had final WNS +0.068 ns and WHS +0.015 ns, and full Flash readback matched expected images.

| Condition | Successful boots | Request issued | Reached GT input | RXRESETDONE drop/recovery |
|---|---:|---|---|---|
| board16 PMA disabled | 0/3 | All three | None | None |
| board16 PMA enabled | 3/3 | All three | All three | All three |
| board16 reversed to disabled | 0/3 | All three | None | None |
| Healthy board17 enabled | 3/3 | All three | All three | All three |

Two-stage synchronization and latches recorded pulses at the issuer and GT input. Five ILA probes also read controller RXRESETDONE drop/recovery/timeout flags. This confirms pulse presence, not direct analog waveform, pulse-width, or pulse-count measurement. RTL and logic simulation establish 16 user-clock width and once per SOFT_RESET. PMA reset in normal sequential mode can trigger subsequent internal resets.

Evidence: [independent implementation review](evidence/day2-autopma-observed-independent-review.json), [first disabled trial](evidence/day2-pma-first-trial-v2.json), [first ILA decoding](evidence/day2-pma-first-bypass-decoded.json), [remaining two disabled trials](evidence/day2-pma-cohort-d2pma-b16tail.json), and [three enabled trials](evidence/day2-pma-cohort-d2pma-en16.json). The first disabled trial is not double-counted. Reversal passed 0/3 and healthy .17 enabled passed 3/3: [reversal](evidence/day2-pma-cohort-d2pma-rev16.json), [healthy .17](evidence/day2-pma-cohort-d2pma-en17.json), [all 12 trials crosschecked](evidence/day2-autopma-reviewed-outcome.json). Healthy .17 F304 monitoring ended after about 4 hours 21 minutes, RBCP 523/523 and TCP 53/53, zero failures: [completion](evidence/day2-control17-stop-verified.json).

This supports post-startup PMA reset as a preventive measure but does not identify the responsible internal PMA state or triggering board power/clock condition. Three successes do not guarantee all conditions.

## Establishing the remaining physical cause

1. Record conditions/results of prior supply/cable swaps and establish whether failure follows the board.
2. Simultaneously measure GT reference clock, GT power rails, and reset waveforms in successful/failed boots.
3. Control incoming-signal timing with a managed port or equivalent and compare startup.

Mean-frequency observation is not analog jitter measurement; there is insufficient evidence that adding a jitter cleaner will resolve this.

## Evidence and cleanup

[evidence/](evidence/) stores diagnostic/boot aggregates and source SHA-256 hashes. Some originals are local only; this repository does not contain every raw record. All 41 export-time hash comparisons matched. Credentials and raw EEPROM data are excluded.

The pre-interruption capture contains 38,846 packets and passed file-read validation. First/last packets were 2026-10-17 11:51:16 and 2026-10-18 04:53:16 JST. Process exit code and final drop count were unavailable at interruption. The last packet is not necessarily capture-process exit time. This is separate from post-resumption capture; continuous coverage of all testing is not claimed. See [interruption audit](evidence/day2-capture-interruption-audit.json) for hashes/checks.

After testing, board16 was restored to existing F202 (0x60C4F202) and board17 to original factory (0x60C4020A). Each full 16 MiB readback matched expected hashes; three power cycles each, repeated RBCP/TCP, IP/version, original EEPROM hashes, and both power outputs ON were verified. See [restoration](evidence/investigation24h-restoration.json) and [final communication/EEPROM/power checks](evidence/investigation24h-final-status.json). Diagnostic F307 was not left as the operational image.

The resumed capture contains 13,210 packets, first/last 2026-10-18 05:04:27 and 10:41:33 JST. It was stopped with Ctrl-C after restoration checks, exit code 1; independent file-reading validation succeeded. Final drops were unavailable and are not assumed zero. Sleep inhibition was released. The [completion audit](evidence/investigation24h-completion-audit.json) records 127 original-source checks and cleanup.

## References

- [AMD UG476: 7 Series FPGAs GTX/GTH Transceivers](https://docs.amd.com/v/u/en-US/ug476_7Series_Transceivers)
- [AMANEQ hardware overview](https://spadi-alliance.rcnp.osaka-u.ac.jp/ug-amaneq/hardware/overview/overview/)
- [StrLrTdc upstream](https://github.com/AMANEQ-official/StrLrTdc)

Latest additional record: [minimum AMANEQ-side fix and hardware comparisons (2026-10-19)](amaneq-side-minimum-20261019/). See that record for patches, all boot results, controls, and final restoration.
