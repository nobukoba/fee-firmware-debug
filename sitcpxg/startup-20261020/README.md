# StrHrTdc SiTCP-XG startup with a connected network

**Language: English | [日本語](README.ja.md)**

Compare the problematic board at 192.168.10.10 with the control board intended for 192.168.10.11 when powered on while connected to a network switch. HS3 adapters are not the subject of the study.

Initial observations on 2026-10-20: .10 did not answer ICMP or RBCP; .11 answered both and returned SiTCP-XG identifier `58544350` at `0xFFFFFF08`, and firmware value `C480020A` at `0xFFFFFF00`, matching StrHrTdcBase v2.A. The running firmware on .10 is unverified. Both JTAG chains contain an XC7K160T; their IP mapping is unverified.

## Measurements

**The 12 trials below preceded verification of the jitter-cleaner configuration. They do not establish a StrHrTdc firmware fault with correct clock settings.** Later, Skeleton v2.2 was loaded temporarily through BIT into the problematic board. CDCE62002 readback at 192.168.10.16 differed from the intended preset. At 19:54 JST, input 125 MHz / outputs 500 and 125 MHz were configured, verified and followed by an acknowledged EEPROM-copy command. Readback still matched and ping succeeded 22 seconds later. At 20:04 JST, each board was powered OFF for at least 15 seconds and ON with the switch already running (one trial each). SiTCP-XG returned after 9.171 seconds on .10 and 9.089 seconds on .11, and both answered ping. Board .10 reported firmware C480020A and retained CDCE62002 values 52080150 / 8F81C081 after power cycling. See [restart evidence](evidence/post-jitter-powercycle-20261020-200302.json) and [retention evidence](evidence/post-jitter-retention.json). Long-term startup reliability remains unverified. [Configuration evidence](evidence/jitter-cleaner-configured.json)

Existing firmware was tested with at least 15 seconds board power off. Success requires three consecutive valid SiTCP-XG identifier reads at least one second apart.

| Condition | Observation window | .10 successes/trials | .11 successes/trials | .11 first responses in successful trials |
| --- | --- | --- | --- | --- |
| Switch already powered on | 60 seconds after confirmed board ON | 0/3 | 2/3 | 43.720 s, 9.090 s |
| Switch powered on at least 15 seconds after board ON | 120 seconds after confirmed switch ON | 0/3 | 3/3 | 16.410 s, 16.410 s, 14.610 s |

The problematic board did not resume communication with either ordering. The control also exceeded the first observation window once. Stable startup is not established. Three trials per condition, with different observation windows, do not establish a general failure rate or a causal ordering effect. Saved IP, running image and internal reset state on .10 still require verification.

Switch OFF disconnected the host Ethernet link; ON restored it. During the first switch-after-board .10 trial, .11 was separately confirmed reachable. Final state: both boards and switch ON, Ethernet Up, .11 reachable and .10 unresponsive. No firmware, IP or license writes were performed.

MSNSwitch2 at 172.16.207.110 controls board power (outlets 1/.10 and 2/.11). ezOutlet5 at 172.16.207.91 controls switch power. Initial management timeouts were resolved when the user changed Wi-Fi from 192.168.19.12/24 to 172.16.207.92/19. Ethernet remains 192.168.10.70/24 at 1 Gbps. The scripts did not change host networking. UIS automatic power control was disabled and ezOutlet5 was in manual mode. Credentials are not stored.

ezOutlet5 power requests can time out after executing. Actual outlet state was read back instead of interpreting the HTTP timeout as failure. One initial aborted attempt is stored separately and excluded from the measurement counts; all outlets were subsequently restored ON.

The latest public [StrHrTdcBase](https://github.com/AMANEQ-official/StrHrTdcBase) firmware is v2.A at main commit `33e3f35dfc43b04672d0bf6b352be2ff33b5579d` (2025-10-14); source version is `C480020A`. Separate AMANEQ board revision 1 and 4 MCS images exist. PCB revision cannot be established from FPGA part alone. MznStrHrTdc is separate mezzanine firmware. StrLrTdc-10G v2.1 is unrelated to this target.

Upstream specifies Vivado 2023.1.1. Vivado 2023.2 updated 13 IP configurations without HDL edits. Project generation, synthesis, place/route and bitstream generation succeeded. Output: `local/StrHrTdcBase/build/StrHrTdcBase.runs/impl_1/toplevel.bit`, 6,692,677 bytes.

User-specified timing constraints were met (WNS 0.119 ns, WHS 0.041 ns). There are 37 missing-input-delay and 35 missing-output-delay checks, six synthesis critical warnings about asynchronous clock-group objects, and DRC warnings including SERDES clock topology. This is not validation of all physical operating conditions.

**Vivado 12-1790 warns that generated evaluation cores stop functioning after a period of time. Do not use this generated image for production or long-running operation.** It was not programmed into hardware or used in the startup measurements. This warning does not establish the cause of the existing boards' behavior. Equivalence with the official MCS is unverified. Source and generated binaries remain in Git-excluded `local/`; build outcome and artifact hash are recorded in [build evidence](evidence/baseline-build-summary.json).

Run these read-only checks in PowerShell 7 from the study repository root:

```powershell
./sitcpxg/startup-20261020/scripts/inspect-network.ps1
./sitcpxg/startup-20261020/scripts/read-sitcpxg.ps1
```

After upstream project generation, run from its clone directory:

```powershell
C:/Xilinx/Vivado/2023.2/bin/vivado.bat -mode batch -source ../../sitcpxg/startup-20261020/scripts/build-baseline.tcl
```

The measurement script is `scripts/run-connected-cohort.ps1`; it accepts PSCredential inputs and refuses to overwrite existing evidence. Switch-after-board trials use `-Condition switch_after_board -ObservationSeconds 120`. All 12 completed trials passed timestamp and success-condition checks in `measurement-audit.json`. A cable-disconnected-at-boot comparison was not performed.

Next investigations: confirm .10 saved IP, running image and PCB revision, then observe PCS block lock, QPLL lock, IDELAYCTRL readiness and SiTCP reset using an independent clock and JTAG diagnostic core. Current designs report no supported debug cores. Once configuration is verified, extend to about 30 trials per condition with equal observation windows. Missing IP assignment or power must not be counted as firmware failure.

Source observations at the pinned commit: the PCS/PMA reset is driven by SystemReset.masterReset (external reset and MMCM lock); SiTCP synchronized resets depend on QPLL lock, IDELAYCTRL readiness and a delay timer. Loss of PCS block lock also asserts SiTCP-XG RSTs through synchronized rst_from_miku_xgmii. PCS/PMA resetdone is unused. These are observations, not a demonstrated root cause.

The pinned SiTCP-XG core is v4.0, commit `33916a82262dabfe5321a7a05802643147b3cef4`. Its [official history](https://github.com/BeeBeansTechnologies/SiTCPXG_Netlist_for_Kintex7/blob/33916a82262dabfe5321a7a05802643147b3cef4/README.md) records a transmit stall fix for coincident ARP and RBCP responses. The running core version and applicability to these boards remain unverified.

Evidence: [initial network](evidence/network.json), [initial RBCP](evidence/rbcp.json), [connected trials](evidence/connected-cohort.json), [switch-after-board trials](evidence/switch-after-board-cohort.json), [measurement audit](evidence/measurement-audit.json), [final power](evidence/final-power-state.json), [JTAG configuration](evidence/config-status.json), [status](status.json).
