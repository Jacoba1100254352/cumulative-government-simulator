# Portfolio Minimax-Regret Ranking

Generated: `2026-08-30T16:31:20+00:00`

This report asks which portfolio has the smallest worst-case loss across the configured value profiles. Regret is measured against the best profile score available in the current portfolio universe for each profile. This is a synthetic sensitivity diagnostic, not an empirical confidence interval.

| Regret Rank | Max Regret | Avg Regret | Balanced Rank | Balanced Score | Uncertainty Band | Floor | Legislature | Review | Anti-capture |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.050 | 0.034 | 339 | 0.638 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | No emergency relief without merits review | Full anti-capture bundle |
| 2 | 0.052 | 0.036 | 379 | 0.636 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Automatic merits follow-up for emergency relief | Full anti-capture bundle |
| 3 | 0.054 | 0.035 | 348 | 0.637 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Emergency integrity package | Full anti-capture bundle |
| 4 | 0.054 | 0.023 | 150 | 0.644 | 0.096 | 0.605 | Default pass unless 2/3 block | No emergency relief without merits review | Full anti-capture bundle |
| 5 | 0.054 | 0.024 | 167 | 0.644 | 0.096 | 0.603 | Default pass unless 2/3 block | Emergency integrity package | Full anti-capture bundle |
| 6 | 0.055 | 0.038 | 460 | 0.634 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Randomized merits panels with en banc correction | Full anti-capture bundle |
| 7 | 0.055 | 0.038 | 459 | 0.634 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Three-judge panels with en banc correction | Full anti-capture bundle |
| 8 | 0.055 | 0.039 | 472 | 0.633 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Comparative 16-seat constitutional senates | Full anti-capture bundle |
| 9 | 0.055 | 0.039 | 469 | 0.633 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Random panels with jurisdiction safeguards | Full anti-capture bundle |
| 10 | 0.056 | 0.038 | 428 | 0.635 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Pre-enactment constitutional council | Full anti-capture bundle |
| 11 | 0.056 | 0.037 | 783 | 0.627 | 0.096 | 0.601 | Default pass + multi-round mediation + challenge | No emergency relief without merits review | Democracy vouchers |
| 12 | 0.057 | 0.039 | 485 | 0.633 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Public-interest litigation filter | Full anti-capture bundle |
| 13 | 0.057 | 0.040 | 493 | 0.633 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Judicial electorate selection court | Full anti-capture bundle |
| 14 | 0.057 | 0.038 | 424 | 0.635 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Constitutional remand before invalidation | Full anti-capture bundle |
| 15 | 0.057 | 0.038 | 811 | 0.627 | 0.096 | 0.601 | Default pass + multi-round mediation + challenge | Emergency integrity package | Democracy vouchers |
| 16 | 0.057 | 0.036 | 632 | 0.629 | 0.096 | 0.608 | Default pass + multi-round mediation + challenge | No emergency relief without merits review | Budgeted disclosed lobbying |
| 17 | 0.057 | 0.025 | 201 | 0.643 | 0.096 | 0.602 | Default pass unless 2/3 block | Automatic merits follow-up for emergency relief | Full anti-capture bundle |
| 18 | 0.057 | 0.039 | 491 | 0.633 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Independent recusal enforcement with substitutes | Full anti-capture bundle |
| 19 | 0.057 | 0.028 | 218 | 0.642 | 0.096 | 0.604 | Default pass unless 2/3 block | Constitutional remand with override window | Full anti-capture bundle |
| 20 | 0.057 | 0.037 | 412 | 0.635 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Constitutional council with concrete-review backstop | Full anti-capture bundle |
| 21 | 0.057 | 0.037 | 660 | 0.629 | 0.096 | 0.608 | Default pass + multi-round mediation + challenge | Emergency integrity package | Budgeted disclosed lobbying |
| 22 | 0.058 | 0.040 | 513 | 0.632 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Mandatory written emergency reasoning | Full anti-capture bundle |
| 23 | 0.058 | 0.039 | 505 | 0.632 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Jurisdiction stripping constrained by rights carveouts | Full anti-capture bundle |
| 24 | 0.058 | 0.039 | 512 | 0.632 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Nonpartisan commission appointments | Full anti-capture bundle |
| 25 | 0.058 | 0.040 | 525 | 0.632 | 0.094 | 0.613 | Default pass + multi-round mediation + challenge | Expanded 15-seat court | Full anti-capture bundle |

## Reading Notes

- Lower regret is better.
- A portfolio can rank first on minimax regret without being the balanced-score winner.
- Regret is measured only across the value profiles currently defined in `scripts/build_portfolios.py`.
