# Minimum reset changes: follow-up tests (afternoon of 2026-10-18)

**Language: English | [日本語](README.ja.md)**

**Hardware comparisons, restoration of both boards, and shutdown checks are complete. The physical root cause remains unresolved.** The study retains the 500 ns post-configuration delay and reduces functional HDL changes by reusing existing circuitry.

## Hardware comparison results

| Order | Firmware on .16 | Successful power cycles |
|---|---|---|
| 1 | Original factory | 0/3 |
| 2 | F30A: change one existing wait constant | 1/3 |
| 3 | Restore original factory | 0/3 |
| 4 | F308: reduced PMA addition | 3/3 |

Healthy control .17 also passed 3/3 with F308. The LAN remained connected and the switch stayed ON. A trial passed only if RBCP, TCP24, version, and IP matched within 90 seconds after power cycling, followed by another successful check five seconds later. Every programming operation passed a complete 16 MiB readback against the expected image.

F308 on .16 was confirmed successful after approximately 63.7, 14.0, and 14.0 seconds. The first board frame appeared after about 58.5 seconds. These times include host ARP backoff and readiness waiting. The actual PMA pulse was not observed in this study, so this does not demonstrate that the board alone starts within one second. See [F308 on .16](evidence/minpma-v2-cohort-pma16a.json), [.17 regression tests](evidence/minpma-v2-cohort-pma17a.json), and [reversal to the original](evidence/minpma-native-minrev16.json).

The smallest hardware-tested PMA addition in this study that preserves the original 500 ns initialization delay has **32 added lines / 1 deleted line: 29 new functional lines, one replacement connection line, and two blank lines**. This does not prove that no shorter implementation exists.

The original factory image was programmed onto .16 and verified by full 16 MiB readback. With the switch ON, it passed **0/3** power cycles within the 90-second communication deadline. The host sent 8, 1, and 1 ARP requests after the respective boots; no frames or ARP replies from the target MAC/IP were observed. See [factory control](evidence/minpma-native-minbase16.json) and [packet verification](evidence/minpma-packets-native-baseline.json).

After the third failure, configuration DONE and EOS were 1; CRC, ID, and fallback errors were 0. Two read-only communication checks about 26 minutes later both timed out on RBCP. Configuration-register PLL_LOCK does not indicate GTX CPLL/CDR lock. See [configuration state](evidence/minpma-native-config-status.json) and [later communication checks](evidence/minpma-native-late-readonly.json).

Factory monitoring on healthy .17 finished after about 2 hours 35 minutes with RBCP 311/311 and TCP 32/32 successful. See [monitoring completion](evidence/minpma-control17-stop-verified.json). Kikusui powers .16; ezOutlet powers .17. The switch stayed ON, and no EEPROM writes were performed. These boot tests used an already-connected LAN; cable insertion after boot, port OFF/ON, TDC precision, and BER were not evaluated.

## Reduced candidates

| Candidate | Functional HDL diff | Validation |
|---|---|---|
| F308: one clock domain, shared counter | +32 / −1 | First implementation had WNS −0.044 ns and was not used. Rerouting without logic changes achieved WNS +0.068 ns / WHS +0.015 ns; both boards passed 3/3. |
| F309: reuse existing CDR wait counter | +6 / −1 | Logic simulation passed, but rejected because it conflicts with the manufacturer's initialization sequence. Never used on hardware. |
| F30A: change existing WAIT_TIME_MAX from 100 to 1000 | One replacement | WNS +0.068 ns / WHS +0.015 ns. After full readback, .16 passed 1/3 and failed 2/3. |

The initial timing-failing image was never used on hardware. The retry used the already-qualified F307 DCP as a placement/routing reference without changing functional HDL. Old and new placement are not identical. This F308 comparison alone therefore does not strictly establish PMA causality; distinguish it from the earlier F307 comparison using identical placement and a physical PMA gate. See [rerouting](evidence/minpma-f308-build-v2.json) and [independent review](evidence/minpma-f308-v2-independent-review.json).

F308's 32 added lines include the replacement connection and two blank lines; its new functional block is 29 lines. F309 adds a declaration and five lines in the existing process, and replaces one connection. F308 runs on the TX user clock and uses one counter for two-stage synchronization of seven conditions, a one-second readiness wait, a 16-clock PMA pulse, and one-shot operation. It completes the pulse even if RXRESETDONE drops during it and rearms on SOFT_RESET_RX. It omits the cross-clock completion handshake and diagnostic state of the older 104-line version.

Simply ANDing PMA with RXRESETDONE could cut the pulse short when PMA itself lowers RXRESETDONE; the counter guarantees width after pulse initiation. This addition is a one-shot startup action, with no continuous communication monitoring or automatic retries. The existing RX startup FSM continues operating, but its recovery blind spot described below remains. Minimization means comparing reuse of state and counters, rather than merely removing line breaks. Version, build procedures, and comparison gates/ILA are excluded from functional HDL counts. See [frozen candidate status](evidence/minpma-candidate-status-frozen.json), [F308 patch](f308-prototype.patch), and [F309 patch](f309-prototype.patch).

F309 issues PMA reset before the first RXRESETDONE. UG476 requires individual resets to remain Low during initialization until RXRESETDONE rises, so the candidate was rejected despite passing logic simulation. See [design review](evidence/minpma-f309-design-review.json) and [AMD UG476](https://docs.amd.com/v/u/en-US/ug476_7Series_Transceivers).

F30A passed only 1/3 and is insufficient as a reliable remedy. See [hardware tests](evidence/resetwidth-cohort-width16a.json) and [one-line patch](f30a-native-wait.patch). Its constant differs from post-configuration STARTUP_DELAY. INIT0, SOFT0, and STARTUP_DELAY=500 ns remain unchanged; the changed constant controls minimum waiting during native RX reset and the later RX user-clock wait. In an ideal-PLL logic model, GTRXRESET hold changed from 515 ns to 5015 ns; this is not a measured waveform. See [simulation](evidence/f30a-logical-simulation.json).

The previously reported F304 [two-line change](../minimal-f304.patch) instead sets the initial GTRXRESET value and its SOFT_RESET value to 1. It previously passed 15/15 on both boards, but reset can become High before the 500 ns post-configuration wait, so compliance of that initial condition with the manufacturer's sequence remains unverified. This study compares candidates retaining the original 500 ns sequence. Common Vivado 2023.2 IP-regeneration adjustments, clock constraints, version identifiers, and build procedures are required separately; the entire project diff is not one line or 32 lines.

## What this study adds about the cause

Frozen event records from three earlier failed boots were reanalyzed after verifying hashes. The startup MONITOR_DATA_VALID/FSM_DONE recording spans about 131–136 µs. Within it, the longest intervals returning from monitoring to DONE were 585, 595, and 585 ns. A reset retry requires 100 µs of continuous invalid data, while a return to a valid state reinitializes that timer.

This supports a recovery blind spot: **monitoring continues, but repeated brief synchronization failures never reach the continuous-error threshold**. Normal PRBS selection 000 enables retries on errors; this is not explained by DONT_RESET_ON_DATA_ERROR simply being tied to 1. DATA_VALID is PCS synchronization status bit 1, not successful Auto-Negotiation or IP communication. See [analysis and limitations](evidence/minpma-fsm-recovery-analysis.json) and [AMD PG047 status definitions](https://docs.amd.com/r/en-US/pg047-gig-eth-pcs-pma/Configuration-and-Status-Vectors).

The record is not a continuous waveform over the entire 90 seconds. Post-PMA logs included rereading the previous 256 events, so old blocks were not counted again as new failures. The physical board condition that first puts the receiver into the bad state remains unresolved.

Earlier hardware records showed RX reset held for about 31.36–31.57 µs including PLL waiting. After release, the CDR wait timer advanced for about 50 µs; RXUSERRDY rose about another 520 ns later. F30A therefore cannot isolate reset-width effects alone; the longer subsequent user-clock wait must also be separated. The CDR wait timer is not an actual CDR lock detector. See [native sequence reanalysis](evidence/minpma-native-order-analysis.json).

The mean clock difference before and after PMA reset was about 709 ppm. Assuming a constant frequency offset, a slip of 1 UI takes about 1.128 µs, close to the observed median MONITOR transition intervals of 1.130–1.155 µs. This is consistent with repeated phase slip causing loss of synchronization, but is not a direct measurement of phase or jitter; alternatives such as missing pulses remain possible. See [frequency/state-period comparison](evidence/minpma-slip-scale-analysis.json).

## Evidence handling

Predictions made before hardware tests are saved as [pretest hypotheses](evidence/minpma-pretest-hypotheses.json). Packet analysis used separate snapshots containing only complete PCAPNG blocks. Raw captures, raw EEPROM data, and credentials are not included. [export-manifest.json](export-manifest.json) distinguishes original hashes from hashes after public JSON transformations. Finalized evidence with the same filename is not overwritten.

[Packet verification](evidence/minpma-packets-comparison.json) covers 21 boot windows. None of the eight failures contained frames from the target MAC/IP; all 13 successes contained RBCP/TCP responses. Host-NIC observation is not evidence of physical-line Auto-Negotiation or analog waveforms.

Capture switched between two files between tests. See [handoff](evidence/minpma-capture-handoff.json) and [merge verification](evidence/minpma-capture-merge.json). A conservative excluded interval of about 596 seconds, from the last original frame to confirmation of continuing capture, intersects none of the 21 boot windows. It includes idle time and is not the actual capture outage duration. The precise outage and drop count are unknown.

## Final state

.16 was restored to existing F202 (0x60C4F202), and .17 to factory (0x60C4020A). Full 16 MiB readbacks matched their references; both boards passed 3/3 power cycles after restoration. Repeated RBCP/TCP, version/IP, original EEPROM hashes, unchanged Kikusui 30 V/1 A settings, and both power outputs ON were verified. See [restoration](evidence/minpma-restoration.json) and [final communication/settings checks](evidence/minpma-final-status.json).

Monitoring, builds, programming, power tests, capture, and temporary sleep inhibition have all ended. Both dumpcap runs ended with exit code 1 after explicit Ctrl-C, but individual file reading and merged capinfos validation succeeded. See [cleanup](evidence/minpma-cleanup.json), [completion audit of 138 hashes and states](evidence/minpma-completion-audit.json), and [reviewed outcome](evidence/minpma-reviewed-outcome.json).
