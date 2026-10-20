# HR reset policy adapted to LR-TDC

**Language: English | [日本語](README.ja.md)**

Study: October 20–21, 2026 JST. Only problem board `.16` was operated. Control `.11` stayed OFF throughout. The jitter cleaner remained disabled (`CDCE_PDB='0'`). The final image is the existing F402 workaround; board `.16` and the network switch are ON.

The CPLL-qualified upper-reset wait alone did **not** fix connected power-on: F511 passed 0/3. Adding earlier PHY initialization in F512 passed 18/18. The one-line early-PHY comparison F503 passed 18/18. These are finite tests on one board, not a universal reliability guarantee or an identification of a defective component.

## Results

| Version | Policy | Board boot, switch ON | Boot with switch initially OFF | Switch cycle from healthy state |
|---|---|---:|---:|---:|
| F500 | Old LR logic, rebuilt | 3/21 | 3/3 | 5/5 |
| F402 | Existing reinitialization workaround | 24/24 | 12/12 | 15/15 |
| F511 | CPLL-qualified upper reset only | 0/3 | 3/3 | 3/3 |
| F512 | HR-style early PHY + qualified upper reset | 18/18 | 3/3 | 15/15 |
| F503 | Early PHY only, one-line change | 18/18 | 3/3 | 15/15 |

Counts are success/attempts. Native F500 additionally recovered **1/1** when the switch was cycled from an unresponsive state, without cycling board power. Reloading the same native Flash image with board power retained succeeded **4/4**, including one reload from an unresponsive state. Once running, native F500 also passed its 30-minute communication check. Thus successful operation after recovery does not imply reliable power-on.

The existing F402 image was retested before the native baseline, restored after F511 as a positive control, and restored again at the end. Cohorts are preserved separately in [results.json](results.json). Warm FPGA reload also changes I/O defaults and attached-module conditions; it does not isolate FPGA-internal effects from external effects.

The initial native connected-boot cohort was **3/18**. After F503 testing, the native image was reprogrammed as a late bench-history control and passed **0/3** connected boots. The table includes both periods. The [late control plan](planned-native-reversal.json) was recorded before observing F503 boot outcomes; temperature was not directly controlled or measured.

## What was changed

LR source: [StrLrTdc 5ac5ce7](https://github.com/AMANEQ-official/StrLrTdc/tree/5ac5ce75944aaec1ab2d4e81588aa9ab19eb7039). HR reference: [StrHrTdcBase 33e3f35](https://github.com/AMANEQ-official/StrHrTdcBase/tree/33e3f35dfc43b04672d0bf6b352be2ff33b5579d).

The LR `hdl/common` submodule is [common-src 784244d](https://github.com/AMANEQ-official/common-src/tree/784244da3c0a60535bde74ac01daeadd8d4fe80a). Distribution patches use LF endings. Forward application to a temporary index containing the pinned root/common files, reverse application, and normalized equality to the actual built sources all passed. The small candidate directories reuse shared project files, so they alone are not a complete clean checkout.

- **F511**, [patch](f511-functional.patch): expose the existing CPLL-lock output through the AMANEQ wrapper, synchronize it with three `ASYNC_REG` flip-flops, and reuse the existing `SystemReset` module for Ethernet upper logic. PHY reset retains the original approximately 2.147-second startup hold. Functional diff including comments: **26 added / 5 deleted**, two files.
- **F512**, [patch](f512-functional.patch): additionally release the active PCS/PMA from SYS lock and seed the upper reset from the same raw reset. The upper wait is approximately 4.295 seconds after its prerequisites, plus 32 release stages. **27 added / 6 deleted**, two files.
- **F503**, [patch](f503-functional.patch): change only the active PCS/PMA reset assignment from `pwr_on_reset` to `raw_pwr_on_reset`. Upper logic keeps the original startup wait. **One line replaced**.
- **F402** remains the [previously selected workaround](../amaneq-side-minimum-20261019/): three new functional lines and one existing line changed; an early start followed by one startup reinitialization. It leaves generated IP internals unchanged.

Test version identifiers and the common board clock settings are separate from these functional counts. All variants use the existing 156.25 MHz Ethernet reference configuration, 1.25 Gbps line rate, 125 MHz SYS and 200 MHz independent clock. The generated LR Ethernet IP internals and TDC reset logic were kept identical across these variants. An unnecessary edit to the unused, permanently powered-down shared QPLL reset was removed before F512/F503 were built.

The changed `reset` is the PCS/PMA wrapper input. It starts the core's existing internal GT reset sequence earlier; it does not directly force `GTRXRESET` low when SYS locks.

To inspect/apply **one** alternative in a working tree at the pinned LR commit, initialize submodules first, then use ordinary working-tree patch application, for example `git submodule update --init --recursive`, `git apply --check f503-functional.patch`, and `git apply f503-functional.patch`. F511/F512 also modify a file inside `hdl/common`; do not use the parent repository's `git apply --index` for the combined patch. If committing those variants upstream, commit the common-src change separately and update the parent's gitlink. F503 touches only the parent top. The patches omit common clock prerequisites and test IDs; use the normal AMANEQ build process and the [previous board-clock audit](../amaneq-side-minimum-20261019/evidence/outerreset-f402-board-clock-audit.json), then repeat timing/DRC checks. These are alternatives, not patches to stack together.

HR uses 10G PCS/PMA with QPLL; LR uses 1G PCS/PMA with CPLL. This adapts the inspectable **reset policy**, not HR's complete core or jitter-cleaner sequence. HR's CDCE-lock prerequisite was omitted because the cleaner is explicitly disabled. PHY startup does not depend on the PLL lock that it must establish: the reused module's `masterReset` output is left open, preventing reset feedback.

## Interpretation and limits

The results support testing **PHY initialization timing relative to the incoming link**, rather than merely adding an upper-logic wait. F503 separates the requirement for the extra upper-reset circuit on `.16`; it does not explain every difference between HR and LR.

The physical trigger remains unresolved. Power/reference-clock transients, receiver acquisition/alignment, and implementation-dependent margin remain alternatives. No new dynamic GT CPLL-lock or recovered-clock waveform was measured in these plain test images. FPGA configuration-register `PLL_LOCK` is not GT CPLL telemetry. Sampled failed boots had configuration DONE/EOS set and no CRC/fallback error, but that does not prove valid reception.

Each variant was synthesized separately and implemented with the same F402 incremental reference checkpoint. In the named PCS/PMA subset, F500 versus F503 has **1596/1596** matching primitive type/LOC/BEL records and **2696/2701** matching net ROUTE/pin records. Explicitly named shared constants, shared/global ROUTE strings over 100,000 characters, external reset nets and clock distribution outside the named subset are excluded. This is a bounded routing comparison, not complete image equivalence or matched-route control of every affected path. Counts and canonical subset hashes are in [results.json](results.json).

Inspection found the five changed common net names and five aliases unique to each build in reset-related paths. Thus the compared core's data-path placement/routing is strongly shared, while the intended reset connection differs. This narrows a routing confounder within the measured subset; it does not identify an analog component fault.

The [Tcl signature builder](tools/pllwait_core_signature.py) and [streaming comparison script](tools/compare_pllwait_core.py) record the method. They require local Vivado checkpoints/signature files and the study directory layout; no hardware operation is performed by these tools.

**Do not promote F503 to a universal fix.** The earlier source-equivalent F403 passed `.16` 3/3 but healthy `.17` only 1/3; see the [previous regression and reversal](../amaneq-side-minimum-20261019/README.md#one-line-f403-was-rejected). The earlier failed trials used a nominal 5-second OFF wait; one 120-second OFF trial passed. Current `.11` was intentionally not tested. F402 was therefore restored at the end.

LR's internal 500 ns startup timer already rearms on `SOFT_RESET`, with a 5 ns stable-clock setting. A missing soft-reset wait was **not** established as the HR/LR difference. See [source review](hr-source-review.json) and the [predictions recorded before F503](hypotheses-after-F512-before-F503.json).

## Verification and method

Each Flash operation backed up and read back all 16 MiB and checked the complete programmed image plus erased remainder. Source identity, routed timing, bus skew, DRC, physical clock settings, and the three actual CDC flip-flops were checked. A digital reset simulation tested missing/interrupted lock, reset reassertion, and release; it is not an analog CDR model. Drafts F501/F502 were rejected before hardware programming because synthesis inferred an SRL in their proposed CDC helper; F511/F512 use explicitly preserved flip-flops.

Immediately after Flash programming, the FPGA still runs the programming helper until a power cycle. That initial unavailable-service probe is not counted as a failed firmware boot; only completed power-cycle trials are counted.

One initial recorder run stopped with a duplicate `time` keyword before any trial. It performed no OFF/ON trial and preserved control `.11` OFF. It is retained separately as a zero-trial aborted run, not counted as a firmware failure. The recorder was fixed before F402-r1.

The build inherited synthesis-time clock-name warnings also present in F500. For final F512/F503 checkpoints, named clocks and the effective asynchronous clock group were checked separately. Existing constraints, including a `ckl_tdc2` spelling in a TDC group list, were held constant. Timing results are under those existing constraints; no full TDC timing/calibration signoff is claimed.

Board power tests use a nominal 10-second OFF wait, plus remote-control latency; this is power cycling, not controlled thermal cooling. HS3 remained connected; supply-rail discharge was not measured. For switch-OFF boot, board power is restored while the switch is OFF, then the switch is turned ON after a 15-second wait. Switch-only tests retain board power and use a nominal 10-second switch-OFF wait. Switch OFF proves Ethernet link disruption here, not necessarily absence of serial output from the local SFP.

The active-ARP cohorts wait 15 seconds after the final ON command is confirmed, then check RBCP firmware ID, runtime IP, an unchanged hash of the 128-byte EEPROM comparison region, and TCP port 24. Two successful checks five seconds apart are required; nominal observation deadlines are 120 seconds for board boots and 180 seconds for link operations. Blocking probe calls and the failure-status snapshot can extend the recorded trial window. The first legacy F402 cohort started probes earlier and used Windows ARP alone, so its latency is not compared with the active-ARP cohorts. Closed packet captures were correlated with trial windows: every failed window contains actual target ARP requests, and **21/21** failed windows contain no ARP response. Service failure is assessed with the complete RBCP/TCP check, not ARP alone. Raw captures, Flash dumps, credentials, and hardware serial numbers are kept private.

Read-only communication checks (five-second sampling, no power operations):

| Image | Minutes requested | Samples | Failures |
|---|---:|---:|---:|
| 0x60C4F402 | 30 | 359 | 0 |
| 0x60C4F402 | 5 | 60 | 0 |
| 0x60C4F500 | 30 | 359 | 0 |
| 0x60C4F512 | 15 | 180 | 0 |

These checks cover network startup/recovery and low-load RBCP/TCP service, not TDC accuracy or full DAQ operation. Full hashes, individual outcomes and packet counts are in [results.json](results.json). Binary firmware artifacts are retained locally.
