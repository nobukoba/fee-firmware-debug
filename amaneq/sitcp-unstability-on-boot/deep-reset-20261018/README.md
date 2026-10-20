# AMANEQ SiTCP startup failure: further isolation (started 2026-10-18)

**Language: English | [日本語](README.ja.md)**

**The approximately ten-hour follow-up investigation is complete.** Checkpoints below are retained as interim records from their respective times. See this section and [result-summary.json](result-summary.json) for final results.

## Final results

The shortest repeatedly verified candidate in this study is the following four-line proposal. This does not prove a mathematical minimum over every possible fix.

The short change with substantial repeated verification has **4 added / 3 deleted lines at three locations**. Problem .16 passed 39/39 and healthy .17 passed 36/36, including 30/120/600-second OFF periods and continuous communication. See [actual diff](patches/deepreset-functional-f30b.patch) and [75-boot summary](evidence/deepreset-f30b-75-summary.json).

The change extends an existing counter to 10 µs, reloads it when DATA_VALID drops, and prevents transition to DONE until validity persists continuously for 10 µs. This prevents short valid indications from repeatedly clearing the existing 100 µs error monitor and allows the existing reset path to operate. No independent PMA-reset generator is added. The initial 500 ns delay and reset values in INIT/SOFT are unchanged.

| Additional comparison | Boot results |
|---|---|
| Original firmware .16, actual ARP transmission verified | 0/3 |
| Same-placement filter enabled .16, immediate probing | 3/3 |
| Same-placement filter disabled .16, reversal retested with immediate probing | 0/3 |
| One-line clock-stability wait F30C | .16: 0/3; .17: 3/3 |
| Diagnostic CDR hold until RXUSERRDY | .16: 0/3 |
| [One-line F310: existing WAIT_TIME_MAX changed to 1 ms](patches/deepreset-functional-f310.patch) | .16: 1/3; .17: 3/3 |

F310 passed [formal timing/image qualification](evidence/deepreset-f310-independent-review.json), including [inspection of the implemented 18-bit counter](evidence/deepreset-f310-counter-audit.json). [Packet verification of final paired cohorts](evidence/deepreset-packet-final-cohorts.json) found actual late ARP requests with no replies in both failed .16 boots. Adding a 1 ms wait alone did not reliably stabilize startup.

**The fault has been narrowed to receive PMA/CDR startup state; the triggering physical factor remains unresolved.** In two failed boots, the mean common-CPLL-derived TXPCS clock remained normal while only recovered RX was offset by about −678 ppm. PMA intervention in each same boot returned it to about +31 ppm; successful startup was about +32 ppm. Mean frequency alone cannot distinguish missing edges, jitter, MGT supply fluctuations, or other explanations. CPLLLOCK/RXRESETDONE not guaranteeing correct receive data is separate from claiming the manufacturer's sequence is necessarily wrong for this board.

Board differences and internal-loopback results support dependence on the on-board receive path/initialization, but do not establish component failure. Further component-level confirmation requires measuring dedicated MGT supplies and reference-clock jitter/waveforms during the same failed boot, or swapping components/paths and checking whether the fault follows.

Host ARP retries sometimes had gaps of about 60 seconds, consistent with Windows negative caching/retry control; kernel-internal state was not measured. Later comparisons verified actual capture transmission/reply times rather than inferring continued receive failure solely from communication timeouts. This confound does not explain the RX-clock anomaly measured directly by ILA.

RXCDR_CFG=03000023FF10100020 matches UG476 Table 4-19 for 8b/10b, RXOUT_DIV=4, and ±200 ppm. No inconsistency was found in the nominal 1.25 Gbit/s, 20-bit, 62.5 MHz division relationship. A failed recovered RX-clock offset is not treated as the transmitter's frequency offset or as justification to widen CDR tolerance. See [settings crosscheck](evidence/deepreset-cdr-settings-crosscheck.json).

At completion, **.16 was restored to F202 and .17 to original factory**. Full 16 MiB readback, three power cycles per board, RBCP/TCP, unchanged EEPROM, and both power outputs ON were verified. See [restoration](evidence/deepreset-restoration.json), [final checks](evidence/deepreset-final-status.json), and [capture/sleep-inhibition cleanup](evidence/deepreset-resource-cleanup.json). The switch stayed ON throughout. The candidate was not automatically adopted for normal operation.

References: [AMD UG476](https://docs.amd.com/v/u/en-US/ug476_7Series_Transceivers), [AMD AR66699: assessing CDR lock](https://adaptivesupport.amd.com/s/article/66699?language=en_US), [Windows ResolveIpNetEntry2](https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-resolveipnetentry2).

## Checkpoint 7: negative CDR-hold results and host ARP confounding

Startup FSM traces showed one transition to DONE in the healthy case, but 90/91 MONITOR–DONE round trips in two failures. DONE residence was 400–1760 ns. Brief valid indications can repeatedly clear the existing 100 µs error monitor: [trace comparison](evidence/deepreset-txpcs-startup-trace-comparison.json). Recording covers only the first 256 events, not reset counts over the entire boot.

The same-placement diagnostic holding RXCDRHOLD until actual RXUSERRDY rose passed **0/3 on .16**. In another failed boot, 5.12 µs and 40.96 µs HOLD pulses reached the GT input while five other reset requests remained inactive, but the abnormal recovered RX clock did not recover. The ordinary-source three-line HOLD addition is rejected. See [manual tests](evidence/deepreset-hold-cohort-deephold16m.json), [startup hold](evidence/deepreset-hold-cohort-deephold16r.json), and [independent review](evidence/deepreset-cdrhold-postload-review-v15.json). This does not exclude every CDR problem or every hold duration.

PMA intervention in the same boot normalized RX frequency and 256 fresh receive words, yet an immediate communication test displayed failure. Capture showed that the host sent neither ARP nor UDP in that interval, so this cannot be interpreted as MAC failure after PMA. Communication later succeeded in the same boot. See [post-PMA receive check](evidence/deepreset-hold-manual-RX-summary.json), [actual transmission](evidence/deepreset-packet-hold-interim.json), and [later communication](evidence/deepreset-neighbor-ready16post.json).

A check using ResolveIpNetEntry2 only for the target Windows IP was added. Actual ARP retries could still be about 60 seconds apart; API calls are not equivalent to packet transmissions. Fresh capture comparisons found real late ARP requests without replies in failures of original .16 **0/3** and filter-disabled **1/3**. Filter-enabled **3/3** immediately replied to requests arriving around 63 seconds after power-on. See [transmission/reply timing](evidence/deepreset-packet-fresh-neighbor.json). Disabled testing with a 12-second wait differed from immediate enabled probing, so an additional immediate-probe disabled comparison was in progress.

This host delay affects communication failure/recovery timing, not the directly measured abnormal RX mean clock alongside normal TXPCS. Earlier internal PMA loopback passed .16 0/3 and .17 3/3: [recheck](evidence/deepreset-prior-loopback-recheck.json). XADC-readable supply/temperature values showed no large failure-correlated change, but dedicated MGT supply transients and jitter were not measured: [readings](evidence/deepreset-txpcs-sysmon-summary.json).

The shortest verified change remained **+4/−3 at three locations**. The shorter one-line existing-constant 1 ms candidate was still building and had not yet undergone hardware evaluation at this checkpoint.

## Checkpoint 6: abnormal mean frequency isolated to recovered RX

**Investigation was ongoing. New measurements localized the effect to reception, without identifying a failed physical component.** A measurement image connected common-CPLL-derived TXOUTCLKPCS to the existing counter, preserving original GT inputs/settings and all existing cell placements/BELs: [independent review](evidence/deepreset-txpcs-unified-review.json). Split displays of existing VIO probes were normalized after checking bit ranges on all 13 ports. The existing observation image's 422 warnings were compared separately from added-circuit warnings: [stopped/repaired review](evidence/deepreset-txpcs-fresh-review-failure.json).

Healthy .17 passed 1/1, with TXPCS about 62.49992 MHz, RX about 62.50206 MHz, and RX/TXPCS about +34 ppm. With the same image, .16 passed 1/3 and failed 2/3. Both failed boots were compared before/after PMA without cycling power. See [paired summary](evidence/deepreset-txpcs-paired-summary.json) and [interpretation/limits](evidence/deepreset-txpcs-interpretation.json).

| Problem .16 | Common-CPLL TXPCS | Recovered RX | RX/TXPCS | RBCP/TCP |
|---|---:|---:|---:|---|
| Successful boot | ~62.49837 MHz | ~62.50036 MHz | ~+32 ppm | Success |
| Two failed boots | ~62.49838 MHz | ~62.45603 MHz | ~−678 ppm | Failure |
| After PMA in each boot | ~62.49838 MHz | ~62.50035 MHz | ~+31 ppm | Recovered |

TXPCS changed only about 0.046/0.025 ppm across PMA. Physical inputs also confirmed RXOUTCLKSEL=010 selects recovered RXOUTCLKPMA and TX/RXSYSCLKSEL=00 selects the same CPLL. Clock-path reference: [UG476 Figure 3-28 p150 and p212](https://docs.amd.com/v/u/en-US/ug476_7Series_Transceivers).

This supports **an inappropriate state in the receive PMA/CDR recovered-clock path rather than an offset in the whole common PLL's mean frequency**. Mean values cannot exclude PLL jitter, supply changes, signal quality, or missing clocks, and do not identify a component or physical trigger. This summary did not independently decode all reset waveforms during PMA, so it also does not claim a purely PMA-only effect.

The next experiment would hold CDR to the reference while observing other reset signals. The short ordinary-firmware fix remained +4/−3; a three-line CDR-hold proposal had only syntax checking/preparation at this stage.

## Checkpoint 5: one-line clock wait did not improve the problem board

**Investigation was ongoing; the verified short fix remained F30B (+4/−3).** [One-line F30C](patches/deepreset-functional-f30c.patch), delaying GTRXRESET release until the existing MMCM-lock check, passed a full build and [independent review](evidence/deepreset-f30c-independent-review.json), WNS +0.068 ns / WHS +0.015 ns. Hardware results were **.16 0/3**, **.17 3/3**: [problem board](evidence/deepreset-cohort-deepf30c16a.json), [healthy board](evidence/deepreset-cohort-deepf30c17a.json). This wait alone does not resolve the issue. It is a separately placed build, not general proof against physical clock-sequencing causes.

Both boards with same-placement F30D filter enabled passed 30-minute read-only monitoring: RBCP 60/60, TCP 6/6, zero failures. See [soak summary](evidence/deepreset-f30d-soak-summary-v2.json). Terminal completion and process absence were checked; the numerical exit code was absent from tool output, so its field remains null.

[Control packet analysis](evidence/deepreset-packet-matched-interim.json) found no ARP/IPv4 replies in three bypass failures and replies in three trials after re-enabling. Late first ARP requests include PC negative-cache effects and are not FPGA startup times. Capture was ongoing; final file hashes would be recorded at completion.

The common-PLL TXOUTCLKPCS observation image and CDR-reference experiment were in preparation, not hardware-verified results at this checkpoint.

## Checkpoint 4: validity qualification worked in controlled comparisons

**Investigation was ongoing; F30B (+4/−3) was the verified short candidate.** .16 passed 39/39 and .17 36/36, each including one trial after 30, 120, and 600 seconds OFF. See [75-boot summary](evidence/deepreset-f30b-75-summary.json).

F30D retained identical placement/routing while changing only the qualification LUT INIT. See [summary/limits](evidence/deepreset-matched-filter-summary.json) and [independent review](evidence/deepreset-f30d-independent-review.json). DCP PHYSDB_ROUTE, name mapping, clock DB, and SHAPE matched byte-for-byte; all primitive placement/INIT matched except the qualification gate.

| Board | Condition | Successful power cycles |
|---|---|---:|
| .16 | Validity filter enabled | 3/3 |
| .16 | Filter bypass | 0/3 |
| .16 | Re-enabled | 3/3 |
| .17 | Enabled, healthy control | 3/3 |

The bypass variant still contains the 10 µs wait and counter reload logic. In this comparison, extending the wait alone did not help; requiring continuous validity did. Actual GT-reset waveforms/retry counts were not observed in this variant, so the internal mechanism mediating improvement was not directly measured.

The original FSM returns to FSM_DONE even after brief validity, clearing the error timer. Failed-boot traces showed FSM_DONE residence of 405–1780 ns. Feeding representative 560 ns invalid / 575 ns valid intervals to the manufacturer FSM showed that **a +3/−2 variant retaining the original 500 ns qualification evades monitoring, whereas the four-line 10 µs variant reinitializes**. See [threshold study](evidence/deepreset-filter-threshold-study.json) and [insufficient three-line patch](patches/deepreset-insufficient-three-line-filter.patch). This rejects one specific line-removal proposal, not every possible fix of three lines or fewer.

**Do not conflate the 500 ns delays:** post-configuration STARTUP_DELAY=500 ns is unchanged. WAIT_TIME_MAX, changed here to 10 µs, is another counter; its original 100 cycles equal 500 ns at 200 MHz. The fixed approximately 50 µs CDR wait is also retained.

A GT Wizard pair properly configured for 1.25 Gbps, 20 bits, and LPM at 125/156.25 MHz differed only in CPLL multiplication and RX/TX CLK25 division. CDR and LPM settings matched the existing design. See [manufacturer-generated settings comparison](evidence/deepreset-gtwizard-reference-comparison.json). Earlier controlled CLK25 divisor 5/7 tests also did not improve the problem. The physical receive-fault trigger remained unresolved.

Another **one-line F30C was still building and untested on hardware**. It holds GTRXRESET until the existing common-user-clock stability condition; [full-FSM simulation including mid-operation clock loss](evidence/deepreset-clockhold-sim-v3-result.json) passed. A [CDR reference hold until RXUSERRDY (+3/−1)](patches/deepreset-readyhold-proposal.patch) was also prepared, but had [syntax checking only](evidence/deepreset-readyhold-hypothesis.json). It differs from PMA reset and was not recommended for adoption at that point.

The following sections retain earlier interim records.

## Interim results at 21:40 JST

**Investigation was ongoing. Hardware-successful F30B (+4/−3) stood at .16 39/39 and .17 33/33.** See [summary/limits](evidence/deepreset-f30b-72-summary.json). .16 passed once each after 30/120/600 seconds OFF. Additional monitoring passed .16 15 minutes, RBCP 30/30 and TCP 3/3; .17 20 minutes, RBCP 40/40 and TCP 4/4, with zero failures. This does not guarantee long-term TDC data quality.

Restoring original factory on .16 produced 0/3 successful boots; returning to F30B produced 3/3. See [factory reversal](evidence/deepreset-native-deepfactory16r1.json) and [candidate restoration](evidence/deepreset-cohort-deepf30b16r1.json). [Interim packet analysis](evidence/deepreset-packet-interim.json) found no board ARP/IPv4 replies in the three factory failures and RBCP/TCP replies from the same MAC after returning to F30B. Host capture alone cannot identify internal PHY/PLL/CDR or analog-supply causes.

The initial routed F30D comparison build had two TDC-side hold violations, worst −0.107 ns. It was not used on hardware; physical repairs were planned. Qualified placement/routing would produce enabled/bypass variants to test whether the 10 µs extension alone worked.

**One-line F30C had simulation only, with no hardware testing yet:** [patch](deepreset-functional-f30c.patch), [hypothesis/applicability](evidence/deepreset-clockhold-hypothesis.json), [full-FSM simulation](evidence/deepreset-clockhold-sim-v2-result.json). Initial GTRXRESET release preceded common-user-clock lock by 36.060 µs, motivating the existing-stability-check hold. This is not proof of a manufacturer sequence violation or physical root cause.

## Interim results at 19:55 JST

**F30B passed 3/3 power cycles on problem .16; adoption and long-term verification were not complete.** It retained +4/−3, passed full 16 MiB Flash readback, and met RBCP IP/version, TCP, and five-second recheck criteria. See [hardware cohort](evidence/deepreset-cohort-deepf30b16a.json) and [independent build review](evidence/deepreset-f30b-independent-review.json). Final WNS was +0.073 ns and WHS +0.009 ns. Tests on .17 and matched-wait qualification-gate controls were to follow.

Healthy .17 factory monitoring ended after about 100 minutes, RBCP 201/201, TCP 21/21, zero failures: [control monitoring](evidence/deepreset-control17-stop-verified.json).

The same native failed boot retained receive-frequency offset after 32 minutes. A further five-minute measurement using the existing RAM timestamp counter and on-board SYS time around readout delays found RXOUTCLK about 583–729 ppm slower than the reference-derived user clock: [interpretation](evidence/deepreset-tx-meter-interpretation.json). **The measured TX user clock was not CPLL output itself.** TXOUTCLKSEL=100 selects reference/2, so these measurements do not establish a healthy CPLL internally. CDRHOLD variants were being generated offline and were untested on hardware. The physical trigger remained unresolved.

The following build/unverified statements describe the initial checkpoint; current F30B results are above.

## Initial observations in this study

Existing qualified F104 frequency-observation firmware was programmed onto .16 and verified by full Flash readback. Power cycling with the switch ON reproduced startup failure. Without further reset or power intervention, the same failed state was measured around 0, 5, and 10 minutes later. All three observations lacked communication; mean RX was about 62.456 MHz and RX/reference about 0.399729. It had not spontaneously returned to the normal ratio near 0.4.

These are **three observations of one failed boot**, not three independent power cycles. Mean frequency cannot identify jitter or a particular failed component. See [observations](evidence/deepreset-native-persistence-analysis.json). Healthy .17 remained on factory under separate monitoring.

## Initial short proposals and unverified points

- **F30B: +4/−3 at three locations.** Reuse the wait counter and require 10 µs of synchronization before accepting recovery. Investigate whether brief synchronization repeatedly clears the existing 100 µs error monitor. Retain initial 500 ns and reset initial value 0; add no PMA pulse timer.
- Digital simulation covered normal startup, short errors, intermittent synchronization, long errors, DONT_RESET_ON_DATA_ERROR, and SOFT_RESET. PLL/CDR were idealized; **hardware effects were unverified and the build was ongoing**.
- Changing WAIT_TIME_MAX also extends initial reset hold and user-clock waiting. Even if effective, a controlled comparison is needed to isolate validity qualification.
- **CDRHOLD: one-line connection hypothesis.** Prepare documented GTX RXCDRHOLD linked to GTRXRESET and a short post-startup diagnostic intervention. Compare against same-placement/routing disabled controls and inspect other physical reset inputs. **Not yet hardware-tested at this checkpoint.**

See [F30B patch](patches/deepreset-functional-f30b.patch), [simulation](evidence/f30b-simulation.json), and [CDRHOLD hypothesis](evidence/deepreset-cdrhold-hypothesis.json).

Reserved RXCDRRESET/RXCDRFREQRESET pins are not forced. GTX behavior follows [AMD UG476](https://docs.amd.com/v/u/en-US/ug476_7Series_Transceivers).

## Study conditions

The switch stays ON. Only Kikusui's output is switched for .16, retaining 30 V/1 A. ezOutlet controls .17. No EEPROM writes occur. Completion requires restoring .16=F202 and .17=factory, verifying readback, three boots each, communication, EEPROM, and both power outputs ON.

F308 from the [previous study](../minimum-reset-20261018/README.md), +32/−1 with both boards passing 3/3, is the comparison baseline. Interim results here do not replace that study's conclusions.
