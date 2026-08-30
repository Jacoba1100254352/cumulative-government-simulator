# Interbranch Bridge v0

Generated: `2026-05-12T02:04:27+00:00`

This deterministic bridge model runs `24` periods for a focused set of portfolio cases. It converts static portfolio diagnostics into feedback loops among legislation, review, capture, correction, court-curbing pressure, compliance, and legitimacy. Coefficients and stress modifiers are externalized in `/Users/jacobanderson/Documents/simulators/Cumulative Government Simulator/config/interbranch-bridge-v0.json`.

## Baseline Bridge Ranking

| Bridge Rank | Bridge Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.723 | Balanced winner | 0.601 | 0.350 | 0.000 | 0.028 | 0.697 | weak starting floor |
| 2 | 0.719 | Efficiency caution case | 0.627 | 0.345 | 0.000 | 0.029 | 0.661 | no dominant failure mode |
| 3 | 0.715 | Minimax-regret winner | 0.595 | 0.337 | 0.000 | 0.027 | 0.675 | no dominant failure mode |
| 4 | 0.713 | Rights/capture winner | 0.528 | 0.305 | 0.000 | 0.026 | 0.708 | no dominant failure mode |
| 5 | 0.713 | Legitimacy-first winner | 0.528 | 0.305 | 0.000 | 0.026 | 0.708 | no dominant failure mode |
| 6 | 0.709 | Robustness winner | 0.516 | 0.298 | 0.000 | 0.025 | 0.700 | no dominant failure mode |
| 7 | 0.474 | Current-system-ish baseline | 0.297 | 0.000 | 0.479 | 0.000 | 0.391 | weak starting floor; low policy quality; public alignment erosion; legitimacy erosion; delivery bottleneck |

## Case Details

### Balanced winner
Highest balanced portfolio score.

| Legislature | Review | Anti-capture | Balanced Rank | Selector |
| --- | --- | --- | --- | --- |
| Expanded portfolio hybrid legislature | No emergency relief without merits review | Full anti-capture bundle | 1 | cumulative-government-portfolios.csv rank 1 |

### Efficiency caution case
Highest efficiency-first profile row, included as a stress case for weak-floor risks.

| Legislature | Review | Anti-capture | Balanced Rank | Selector |
| --- | --- | --- | --- | --- |
| Default pass unless 2/3 block | No emergency relief without merits review | Democracy vouchers | 348 | profile-sensitivity.csv efficiency-first rank 1 |

### Minimax-regret winner
Lowest maximum regret across configured value profiles.

| Legislature | Review | Anti-capture | Balanced Rank | Selector |
| --- | --- | --- | --- | --- |
| Default pass + multi-round mediation + challenge | No emergency relief without merits review | Full anti-capture bundle | 323 | portfolio-minimax-regret.csv rank 1 |

### Rights/capture winner
Highest rights-first profile row, which weights rights while preserving capture resistance.

| Legislature | Review | Anti-capture | Balanced Rank | Selector |
| --- | --- | --- | --- | --- |
| Unicameral majority + pairwise alternatives | No emergency relief without merits review | Full anti-capture bundle | 125 | profile-sensitivity.csv rights-first rank 1 |

### Legitimacy-first winner
Highest legitimacy-first profile row.

| Legislature | Review | Anti-capture | Balanced Rank | Selector |
| --- | --- | --- | --- | --- |
| Unicameral majority + pairwise alternatives | No emergency relief without merits review | Full anti-capture bundle | 125 | profile-sensitivity.csv legitimacy-first rank 1 |

### Robustness winner
Highest cross-profile robustness score.

| Legislature | Review | Anti-capture | Balanced Rank | Selector |
| --- | --- | --- | --- | --- |
| Portfolio hybrid legislature | No emergency relief without merits review | Full anti-capture bundle | 267 | portfolio-robustness.csv rank 1 |

### Current-system-ish baseline
Stylized current institutional package for comparison.

| Legislature | Review | Anti-capture | Balanced Rank | Selector |
| --- | --- | --- | --- | --- |
| Stylized U.S.-like conventional benchmark | Stylized current U.S.-like supreme court | Open access lobbying | 33486 | fixed baseline keys |


## Reading Notes

- `Bridge Score` is a feedback-adjusted score over final policy quality, legitimacy, capture control, correction backlog control, compliance, average delivery, and court-curbing control.
- `Final Capture` and `Final Backlog` are pressure values where lower is better.
- The baseline per-period trace is in `reports/interbranch-bridge-v0-timeseries.csv`.
- Stress sensitivity is in `reports/interbranch-bridge-v0-sensitivity.md`.
- The assumptions file is `reports/interbranch-bridge-v0-assumptions.json`.
