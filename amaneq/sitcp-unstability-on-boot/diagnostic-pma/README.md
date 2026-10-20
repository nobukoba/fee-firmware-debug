# F307 automatic PMA reset: diagnostic sources

**Language: English | [日本語](README.ja.md)**

This directory contains only custom control RTL, testbenches, and logic simulation results. It preserves the original RX FSM's 500 ns delay, INIT0, and SOFT0. After readiness and inactivity of existing resets have persisted for one second, it requests one PMA reset lasting 16 RX clock cycles. Normal GTRESETSEL=0 operation is retained. The RX-side clock is the implementation's shared TX/RX user clock; this is separate from measuring the recovered receive clock.

This is a diagnostic candidate distinct from F304, which changes only two locations in the original RX FSM. It is not presented as the smallest production fix. Integration requires adding signals and an instance to the generated GT wrapper, and ORing the request into RXPMARESET. The full generated vendor IP is not included. A physical gate and ILA are added separately for comparison tests.

The normal model checks readiness waiting, the 16-cycle pulse, RXRESETDONE deassertion and recovery, one-shot operation, and rearming after SOFT_RESET. Fault models cover interrupted readiness, absence of the RX clock from the start, and RXRESETDONE remaining high. These simulations do not validate a clock stopping during operation, analog behavior, or physically connecting the cable after startup.

Hardware testing had not been performed when the RTL was first exported. Subsequent tests compared the physical gate enabled and disabled, completing hardware evaluation. See the parent study README for placement/routing, ILA observations, all 12 trials, and limitations. Source correspondence, line counts, and hashes before and after export transformations are recorded in [source-index.json](source-index.json).
