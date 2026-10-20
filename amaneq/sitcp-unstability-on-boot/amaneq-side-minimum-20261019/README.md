# Minimizing the AMANEQ-side SiTCP startup remedy (2026-10-19)

**Language: English | [日本語](README.ja.md)**

## Final results

The smallest selected candidate built from source and verified on both boards in this study is **F402**. It changes only AMANEQ's `hdl/toplevel.vhd`: **three new functional lines and one existing line modified**. Including a comment and a blank line, the Git diff is **6 added / 1 deleted (net +5)**. See [patch](patches/outerreset-functional-f402.patch), [complete source](source/f402/toplevel.vhd), and [qualification](evidence/outerreset-f402-independent-review.json). The generated IP's internal startup FSM is unchanged.

Problem board .16 passed **7/7**, and healthy board .17 passed **6/6**. See [all cohorts](evidence/outerreset-cohort-summary-final.json) and [verification against the closed capture](evidence/outerreset-packets-final.json). This is the smallest of the candidates investigated here, not proof of a mathematical minimum across all possible circuits.

The physical trigger remains unresolved. Distinguish the previous [recovered-clock/PMA-CDR study](../deep-reset-20261018/) from this study of higher-level reset sequencing.

With identical F401 placement/routing, the problem board changed from enabled 3/3 to bypass 0/3, initial-reset extension 0/3, and enabled again 3/3. The extended-hold and enabled versions share the final reset-release edge. This supports the effect of Ethernet reinitialization after an initial startup attempt rather than simply delaying release. See [causal comparison](evidence/outerreset-f401-causal-reversal.json) and [hypotheses recorded beforehand](evidence/outerreset-causal-hypotheses-before-hold-raw.json). It does not uniquely establish the physical cause or future failure rate.

### All boot comparisons

| Candidate / condition | Board | Successes / trials | Requested OFF seconds |
|---|---|---:|---|
| [f401 / enabled](evidence/outerreset-cohort-outerf40116a.json) | 192.168.10.16 | 3/3 | 5, 5, 5 |
| [f401 / enabled](evidence/outerreset-cohort-outerf40116back.json) | 192.168.10.16 | 3/3 | 5, 5, 5 |
| [f401 / bypass](evidence/outerreset-cohort-outerf40116by.json) | 192.168.10.16 | 0/3 | 5, 5, 5 |
| [f401 / hold](evidence/outerreset-cohort-outerf40116hold.json) | 192.168.10.16 | 0/3 | 5, 5, 5 |
| [f401 / enabled](evidence/outerreset-cohort-outerf40116long.json) | 192.168.10.16 | 3/3 | 30, 120, 600 |
| [f401 / enabled](evidence/outerreset-cohort-outerf40116more.json) | 192.168.10.16 | 18/18 | 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5 |
| [f401 / enabled](evidence/outerreset-cohort-outerf40117a.json) | 192.168.10.17 | 3/3 | 5, 5, 5 |
| [f401 / enabled](evidence/outerreset-cohort-outerf40117more.json) | 192.168.10.17 | 9/9 | 5, 5, 5, 5, 5, 5, 5, 5, 5 |
| [f402 / enabled](evidence/outerreset-cohort-outerf40216a.json) | 192.168.10.16 | 3/3 | 5, 5, 5 |
| [f402 / enabled](evidence/outerreset-cohort-outerf40216backlong.json) | 192.168.10.16 | 4/4 | 5, 30, 120, 600 |
| [f402 / bypass](evidence/outerreset-cohort-outerf40216by.json) | 192.168.10.16 | 0/3 | 5, 5, 5 |
| [f402 / early](evidence/outerreset-cohort-outerf40216raw.json) | 192.168.10.16 | 3/3 | 5, 5, 5 |
| [f402 / enabled](evidence/outerreset-cohort-outerf40217a.json) | 192.168.10.17 | 3/3 | 5, 5, 5 |
| [f402 / enabled](evidence/outerreset-cohort-outerf40217back.json) | 192.168.10.17 | 3/3 | 5, 5, 120 |
| [f402 / early](evidence/outerreset-cohort-outerf40217raw.json) | 192.168.10.17 | 1/3 | 5, 5, 5 |
| [f403 / enabled](evidence/outerreset-cohort-outerf40316a.json) | 192.168.10.16 | 3/3 | 5, 5, 5 |
| [f403 / enabled](evidence/outerreset-cohort-outerf40317a.json) | 192.168.10.17 | 1/3 | 5, 5, 120 |
| [factory / enabled](evidence/outerreset-cohort-outerfact16long.json) | 192.168.10.16 | 0/3 | 30, 120, 600 |
| [factory / enabled](evidence/outerreset-cohort-outerfact16q.json) | 192.168.10.16 | 0/3 | 5, 5, 5 |
| [factory / enabled](evidence/outerreset-cohort-outerfact17long.json) | 192.168.10.17 | 3/3 | 30, 120, 600 |
| [factory / enabled](evidence/outerreset-cohort-outerfact17q.json) | 192.168.10.17 | 3/3 | 5, 5, 5 |

Separately from this standard cohort table, the first three immediate probes after factory .16 programming passed 0/3: [record](evidence/deepreset-native-outerfact16a-cold3.json). Together with the six standard factory .16 trials, factory .16 passed 0/9. Diagnostic `hold`/`early` images are not counted as validation of independent minimal-source variants.

### Continuous communication

- [outerreset-soak-f401both.json](evidence/outerreset-soak-f401both.json): requested 900 seconds, state `read_only_candidate_soak_completed_both_healthy`. See the record for each board's RBCP/TCP counts and failures.
- [outerreset-soak-f402both.json](evidence/outerreset-soak-f402both.json): requested 600 seconds, same completed/healthy state. See the record for individual counts and failures.

### Applying and rebuilding

The base commit is `5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039`. Patch application and Git line counts were verified using a [temporary index](evidence/outerreset-patch-application-check.json). In a corresponding AMANEQ clone, obtain the patch and run `git apply outerreset-functional-f402.patch`, then `git diff --check`. No new module registration is required because this reuses RstDelayTimer.

The test version identifier is separate from the functional diff: [defBusAddressMap.vhd](source/f402/defBusAddressMap.vhd). The [study build.tcl](source/f402/build.tcl) uses Vivado 2023.2, the then-current I/J/Y drive mappings, and earlier qualified DCPs. It is a research script, not a portable build for an arbitrary fresh clone. For independent rebuilding, use normal AMANEQ procedures or remove the study reference-DCP settings and recheck STA, DRC, and bus skew. Existing 156.25 MHz CPLL/XDC settings remain necessary: [clock audit](evidence/outerreset-f402-board-clock-audit.json).

See the [source commit record](evidence/outerreset-final-source-commit.json) for the local commit containing only the functional source file. No push to the public upstream was performed.

The [final consistency audit](evidence/outerreset-local-completion-audit-v2.json), requiring restoration, cleanup, and a commit of verified source, also completed. Older audit records retain their original scope.

### Final state

**.16 was restored to F202, and .17 to the original factory image.** Fresh full 16 MiB readbacks, three boots per board, RBCP/TCP, unchanged EEPROM, and both power outputs ON were verified. See [restoration](evidence/outerreset-restoration.json), [final status](evidence/outerreset-final-status.json), [post-restoration soak](evidence/outerreset-final-soak-summary.json), and [capture/sleep-inhibition cleanup](evidence/outerreset-resource-cleanup.json). Raw packets, EEPROM, Flash images, DCPs, and power-controller credentials were not copied to the public records.

### One-line F403 was rejected

F403 only changes `reset => pwr_on_reset` to `reset => raw_pwr_on_reset`. It was built independently from source without the extra timer and tested after STA, DRC, initialization, physical routing, and full Flash readback checks. Problem .16 passed **3/3**, but healthy .17 passed **1/3**. It was rejected because it introduced failures on the healthy board. Success on .16 alone is not a one-line solution. See [independent one-line patch](patches/outerreset-functional-f403.patch), [qualification](evidence/outerreset-f403-independent-review.json), and [all hardware results](evidence/outerreset-cohort-summary-final.json).

In F403's initial .17 comparison, both requested 5-second OFF trials failed, and the single 120-second OFF trial passed. These three trials do not establish that longer OFF always succeeds. Actual ARP requests/replies were checked against the closed capture. Rather than extending F403 testing, the already-qualified F402 placement was used for an `early` diagnostic on .17, then restored to F402 enabled.

The diagnostic retaining F402 placement/routing but using early release alone passed **1/3** on healthy .17: [record](evidence/outerreset-cohort-outerf40217raw.json). Since early release alone also fails, the candidate selected for both boards retains the extra reinitialization. This does not identify the physical trigger.

Healthy .17 passed 3/3 with F402 enabled, 1/3 with early release alone, then 3/3 after returning to enabled, including one 120-second OFF trial. See [regression/reversal evidence](evidence/outerreset-board17-regression-reversal.json). These are small, ordered comparisons; actual power rails and FPGA DONE during failures were not measured. No response does not uniquely imply CDR failure.

Identical placement/routing comparisons apply only to F401/F402 diagnostic variants. F403 was synthesized and implemented from separate source without the extra timer; matching placement with F402 or factory is not claimed.

The selected candidate is the smallest in this search to pass every trial on both boards. This is not proof that every one-line idea is impossible. Existing RstDelayTimer's readyOut is simply the inverse of delayRstOut, so it provides no independent intermediate time threshold. Combining those same two signals alone cannot produce a finite additional reset window. F402 reuses the existing global startup wait as the endpoint and adds one independent timer. See [timer output analysis](evidence/outerreset-existing-timer-output-analysis.json).

## Implementation and test design

**Hardware tests and final restoration are complete.** See the final results and evidence above. Preparation/build JSON records preserve their state at creation.

The target is AMANEQ-official/StrLrTdc commit `5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039`. Both boards remain connected to the same switch: .16 is the problem board and .17 the healthy control. Kikusui output controls .16; the former switch ezOutlet controls .17. The switch stays ON. Kikusui 30 V/1 A settings and EEPROM are unchanged.

The goal is a small remedy in AMANEQ's upper-level source without editing the generated AMD IP's RX startup FSM. Earlier F202 has a dedicated 114-line module plus connections. Earlier F30B (+4/−3, 75 boots verified) edits generated IP internals, so it is distinct from this study's constraint.

## Candidates and line counting

| Candidate | Actual diff | Added control | Intent |
|---|---:|---|---|
| F401 | +9 / −1 | Two existing RstDelayTimer instances | After normal power-on waiting, run for one second, then assert external reset for 100 ms |
| F402 | +6 / −1 | One timer instance | Reassert reset one second after SYS lock; release when the existing approximately 2.147-second power-on wait ends |
| F403 | +1 / −1 (one existing line modified) | None | Start Ethernet after SYS lock, retaining the original SiTCP wait |

F401/F402 added-line counts include the replacement reset connection, one comment, and one blank line. Net increases are eight and five lines respectively. Version identifiers and build/test scripts are separate. Existing AMANEQ 156.25 MHz CPLL/XDC settings are shared prerequisites, not new startup-fix changes. No new HDL module or independent reset FSM is added.

F402 does not merely compress the same code onto fewer lines: it reuses the existing power-on timer, removing one timer and a dedicated reset signal/assignment. It avoids repurposing unrelated signals or circular logic that continuously resets itself until reception succeeds.

## What is reset

The request enters top-level `GbEPcsPma.reset`, then the existing PCS reset and four-stage asynchronous-assert/synchronous-release circuit, rerunning the existing TX/RX startup sequence. It does not directly pulse only GTX `RXPMARESET` with a separate 100 ms circuit. Generated IP's 500 ns delay, GTRXRESET values in INIT/SOFT_RESET, and receive-valid logic remain unchanged.

[AMD PG047 v16.2 Resets](https://docs.amd.com/r/16.2-English/pg047-gig-eth-pcs-pma/Resets?contentId=L6jmqD4heKc3zefmU9oeGA) also describes synchronizing the public reset to an independent clock for GT configurations. See [crosscheck against this version/implementation](evidence/outerreset-manufacturer-reset-crosscheck.json). Wait values were chosen for this study; hardware comparisons provide the operational evidence.

The timer uses the independent 125 MHz SYS clock generated from BASE_CLK. The independent 200 MHz GT clock is supplied by the same SYS clock generator. Timer operation does not depend on the faulty recovered receive clock or Ethernet link establishment.

F401/F402 add one startup reset, not ongoing fault monitoring. They may temporarily interrupt a link during startup. No managed port or separate switch supply was available to automate physical cable insertion after startup; that test is not claimed.

## Tests and acceptance criteria

Before programming, check post-synthesis/implementation STA, bus skew, DRC against known findings, unchanged generated GT HDL, timer simulation, and actual clock/reset routing. Full 16 MiB SPI readback identifies both board and image. For enabled/disabled comparisons, compare all primitive LOC/BEL/INIT values and five types of physical DCP data, confirming that only the reset LUT INIT differs.

A successful boot requires expected RBCP IP/version, a TCP24 connection, and another check five seconds later. Standard comparisons wait until 12 seconds after the power-ON response before the test script's first connection probe. This does not guarantee 12 seconds without network traffic: Windows background ARP can occur earlier. Classifying failure as board nonresponse also requires checking actual captured ARP transmission and replies.

Original firmware .16 initially passed 0/3 with immediate checks and 0/3 with checks after 12 seconds; .17 passed 3/3 with the 12-second wait. All six failed boots had actual ARP requests and no board ARP replies. See the complete table for later long-OFF and candidate trials: original .16 totals 0/9 and .17 totals 6/6.

Recovery does not establish the physical root cause. Earlier observations support dependence on recovered-clock/PMA-CDR startup state, but do not uniquely identify MGT supply, reference-clock jitter, missing edges, or a specific component as the trigger.

## Completion criteria

Restore .16 to F202 and .17 to original factory. Verify fresh full readback, three power cycles each, RBCP/TCP, unchanged EEPROM, and both power outputs ON. Stop capture and temporary sleep inhibition; remove only drive mappings created by the study. The new candidate is not automatically adopted for normal operation.

TDC precision/calibration using external inputs is outside these boot/communication tests.
