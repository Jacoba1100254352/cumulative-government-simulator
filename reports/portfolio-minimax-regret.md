# Portfolio Minimax-Regret Ranking

Generated: `2026-05-12T02:04:25+00:00`

This report asks which portfolio has the smallest worst-case loss across the configured value profiles. Regret is measured against the best profile score available in the current portfolio universe for each profile. This is a synthetic sensitivity diagnostic, not an empirical confidence interval.

| Regret Rank | Max Regret | Avg Regret | Balanced Rank | Balanced Score | Uncertainty Band | Floor | Legislature | Review | Anti-capture |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.051 | 0.034 | 323 | 0.633 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | No emergency relief without merits review | Full anti-capture bundle |
| 2 | 0.053 | 0.036 | 354 | 0.631 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Automatic merits follow-up for emergency relief | Full anti-capture bundle |
| 3 | 0.054 | 0.023 | 119 | 0.640 | 0.096 | 0.607 | Default pass unless 2/3 block | No emergency relief without merits review | Full anti-capture bundle |
| 4 | 0.054 | 0.024 | 127 | 0.640 | 0.096 | 0.605 | Default pass unless 2/3 block | Emergency integrity package | Full anti-capture bundle |
| 5 | 0.055 | 0.035 | 327 | 0.632 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Emergency integrity package | Full anti-capture bundle |
| 6 | 0.056 | 0.038 | 446 | 0.629 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Randomized merits panels with en banc correction | Full anti-capture bundle |
| 7 | 0.057 | 0.038 | 447 | 0.629 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Three-judge panels with en banc correction | Full anti-capture bundle |
| 8 | 0.057 | 0.039 | 464 | 0.628 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Comparative 16-seat constitutional senates | Full anti-capture bundle |
| 9 | 0.057 | 0.025 | 152 | 0.639 | 0.096 | 0.604 | Default pass unless 2/3 block | Automatic merits follow-up for emergency relief | Full anti-capture bundle |
| 10 | 0.057 | 0.039 | 460 | 0.628 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Random panels with jurisdiction safeguards | Full anti-capture bundle |
| 11 | 0.057 | 0.036 | 709 | 0.624 | 0.096 | 0.598 | Default pass + multi-round mediation + challenge | No emergency relief without merits review | Democracy vouchers |
| 12 | 0.057 | 0.027 | 176 | 0.638 | 0.096 | 0.605 | Default pass unless 2/3 block | Constitutional remand with override window | Full anti-capture bundle |
| 13 | 0.057 | 0.038 | 391 | 0.630 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Pre-enactment constitutional council | Full anti-capture bundle |
| 14 | 0.058 | 0.037 | 734 | 0.623 | 0.096 | 0.598 | Default pass + multi-round mediation + challenge | Emergency integrity package | Democracy vouchers |
| 15 | 0.058 | 0.039 | 387 | 0.630 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Constitutional remand before invalidation | Full anti-capture bundle |
| 16 | 0.058 | 0.040 | 474 | 0.628 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Public-interest litigation filter | Full anti-capture bundle |
| 17 | 0.058 | 0.038 | 372 | 0.631 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Constitutional council with concrete-review backstop | Full anti-capture bundle |
| 18 | 0.058 | 0.027 | 189 | 0.638 | 0.096 | 0.602 | Default pass unless 2/3 block | Constitutional remand before invalidation | Full anti-capture bundle |
| 19 | 0.058 | 0.040 | 476 | 0.628 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Independent recusal enforcement with substitutes | Full anti-capture bundle |
| 20 | 0.058 | 0.027 | 187 | 0.638 | 0.096 | 0.597 | Default pass unless 2/3 block | Constitutional council with concrete-review backstop | Full anti-capture bundle |
| 21 | 0.059 | 0.037 | 699 | 0.624 | 0.097 | 0.599 | Default pass + multi-round mediation + challenge | No emergency relief without merits review | Budgeted disclosed lobbying |
| 22 | 0.059 | 0.040 | 492 | 0.627 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Mandatory written emergency reasoning | Full anti-capture bundle |
| 23 | 0.059 | 0.039 | 484 | 0.628 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Jurisdiction stripping constrained by rights carveouts | Full anti-capture bundle |
| 24 | 0.059 | 0.038 | 729 | 0.623 | 0.096 | 0.599 | Default pass + multi-round mediation + challenge | Emergency integrity package | Budgeted disclosed lobbying |
| 25 | 0.059 | 0.040 | 491 | 0.627 | 0.094 | 0.608 | Default pass + multi-round mediation + challenge | Nonpartisan commission appointments | Full anti-capture bundle |

## Reading Notes

- Lower regret is better.
- A portfolio can rank first on minimax regret without being the balanced-score winner.
- Regret is measured only across the value profiles currently defined in `scripts/build_portfolios.py`.
