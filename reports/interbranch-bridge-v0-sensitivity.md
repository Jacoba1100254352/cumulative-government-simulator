# Interbranch Bridge v0 Sensitivity

Generated: `2026-08-30T16:31:26+00:00`

This report reruns the same focused bridge cases under every stress profile defined in `config/interbranch-bridge-v0.json`. The question is whether the baseline bridge winner remains stable when capture pressure, public trust, rights threat, emergency abuse, institutional noncompliance, administrative overload, or federalism/agency-capacity constraints become worse. It is not a full bridge run over every portfolio.

## Stress Winners

| Stress Profile | Winner | Score | Final Quality | Final Legitimacy | Winner Failure Modes |
| --- | --- | --- | --- | --- | --- |
| Administrative Overload and Complexity Stress | Balanced winner | 0.694 | 0.319 | 0.659 | weak starting floor |
| Baseline | Balanced winner | 0.727 | 0.359 | 0.703 | weak starting floor |
| Court-Curbing and Institutional Noncompliance Stress | Balanced winner | 0.703 | 0.351 | 0.661 | weak starting floor |
| Emergency Abuse Stress | Robustness winner | 0.709 | 0.322 | 0.677 | no dominant failure mode |
| Federalism and Agency-Capacity Stress | Balanced winner | 0.674 | 0.300 | 0.631 | weak starting floor |
| High Capture Pressure | Robustness winner | 0.498 | 0.025 | 0.440 | low policy quality; public alignment erosion; legitimacy erosion |
| High Rights-Threat Environment | Rights/capture winner | 0.721 | 0.322 | 0.711 | no dominant failure mode |
| Low Public Trust | Balanced winner | 0.679 | 0.321 | 0.586 | weak starting floor |

## Cross-Stress Stability

The table below is sorted by the wins/top-two rule. The criterion-winner table shows how the conclusion changes under other defensible stability definitions.

| Win/Top-2 Rank | Case | Avg Rank | Worst Rank | Wins | Top-2 Profiles | Avg Score | Max Regret | Score Spread |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Balanced winner | 2.250 | 5 | 5 | 5 | 0.598 | 0.302 | 0.532 |
| 2 | Robustness winner | 4.125 | 6 | 2 | 2 | 0.667 | 0.015 | 0.221 |
| 3 | Rights/capture winner | 2.750 | 4 | 1 | 4 | 0.664 | 0.035 | 0.259 |
| 4 | Efficiency caution case | 4.625 | 7 | 0 | 3 | 0.559 | 0.332 | 0.556 |
| 5 | Legitimacy-first winner | 3.750 | 5 | 0 | 1 | 0.664 | 0.035 | 0.259 |
| 6 | Minimax-regret winner | 3.875 | 6 | 0 | 1 | 0.574 | 0.309 | 0.530 |
| 7 | Current-system-ish baseline | 6.625 | 7 | 0 | 0 | 0.390 | 0.469 | 0.239 |

## Stability Criterion Winners

| Criterion | Winner | Winner Metric | Interpretation |
| --- | --- | --- | --- |
| Wins/top-two rule | Balanced winner | 5 wins; 5 top-two placements; average rank 2.250 | Ranks cases by stress-profile wins, then top-two placements, then average stress rank. |
| Best average stress rank | Balanced winner | average rank 2.250; worst rank 5 | Ranks cases by average rank across stress profiles, regardless of how wins are distributed. |
| Best average bridge score | Robustness winner | average bridge score 0.667 | Ranks cases by mean bridge score across stress profiles. |
| Lowest maximum stress regret | Robustness winner | max stress regret 0.015; average regret 0.009 | Ranks cases by the smallest worst gap from the winning score in any stress profile. |
| Smallest score spread | Robustness winner | score spread 0.221 | Ranks cases by the smallest difference between best and worst stress-profile bridge score. |

## Administrative Overload and Complexity Stress
Implementation is harder: effective complexity, delivery, review capacity, and compliance are reduced.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.694 | Balanced winner | 0.544 | 0.319 | 0.000 | 0.020 | 0.659 | weak starting floor |
| 2 | 0.684 | Minimax-regret winner | 0.531 | 0.303 | 0.000 | 0.018 | 0.633 | no dominant failure mode |
| 3 | 0.684 | Rights/capture winner | 0.476 | 0.277 | 0.000 | 0.018 | 0.668 | no dominant failure mode |
| 4 | 0.684 | Legitimacy-first winner | 0.476 | 0.277 | 0.000 | 0.018 | 0.668 | no dominant failure mode |
| 5 | 0.681 | Robustness winner | 0.468 | 0.272 | 0.000 | 0.018 | 0.662 | no dominant failure mode |
| 6 | 0.658 | Efficiency caution case | 0.548 | 0.288 | 0.000 | 0.099 | 0.574 | weak starting floor |
| 7 | 0.417 | Current-system-ish baseline | 0.245 | 0.000 | 0.632 | 0.000 | 0.317 | weak starting floor; low policy quality; public alignment erosion; capture drift; legitimacy erosion; delivery bottleneck |

## Baseline
Default bridge coefficients with no additional stress modifiers.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.727 | Balanced winner | 0.612 | 0.359 | 0.000 | 0.029 | 0.703 | weak starting floor |
| 2 | 0.722 | Efficiency caution case | 0.634 | 0.352 | 0.000 | 0.030 | 0.666 | no dominant failure mode |
| 3 | 0.719 | Minimax-regret winner | 0.602 | 0.344 | 0.000 | 0.027 | 0.681 | no dominant failure mode |
| 4 | 0.716 | Rights/capture winner | 0.537 | 0.312 | 0.000 | 0.026 | 0.712 | no dominant failure mode |
| 5 | 0.716 | Legitimacy-first winner | 0.537 | 0.312 | 0.000 | 0.026 | 0.712 | no dominant failure mode |
| 6 | 0.713 | Robustness winner | 0.528 | 0.307 | 0.000 | 0.025 | 0.705 | no dominant failure mode |
| 7 | 0.480 | Current-system-ish baseline | 0.288 | 0.000 | 0.449 | 0.000 | 0.396 | weak starting floor; low policy quality; public alignment erosion; legitimacy erosion; delivery bottleneck |

## Court-Curbing and Institutional Noncompliance Stress
Corrective review creates more retaliation pressure, institutional compliance falls, and court-curbing pressure decays slowly.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.703 | Balanced winner | 0.603 | 0.351 | 0.000 | 0.028 | 0.661 | weak starting floor |
| 2 | 0.697 | Efficiency caution case | 0.624 | 0.342 | 0.000 | 0.029 | 0.622 | no dominant failure mode |
| 3 | 0.695 | Minimax-regret winner | 0.593 | 0.336 | 0.000 | 0.027 | 0.639 | no dominant failure mode |
| 4 | 0.691 | Rights/capture winner | 0.529 | 0.305 | 0.000 | 0.025 | 0.668 | no dominant failure mode |
| 5 | 0.691 | Legitimacy-first winner | 0.529 | 0.305 | 0.000 | 0.025 | 0.668 | no dominant failure mode |
| 6 | 0.688 | Robustness winner | 0.521 | 0.300 | 0.000 | 0.025 | 0.662 | no dominant failure mode |
| 7 | 0.456 | Current-system-ish baseline | 0.283 | 0.000 | 0.469 | 0.000 | 0.354 | weak starting floor; low policy quality; public alignment erosion; legitimacy erosion; delivery bottleneck |

## Emergency Abuse Stress
Emergency action and emergency litigation generate more rights-threatening policy, larger review dockets, and stronger legitimacy penalties when review cannot keep up.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.709 | Robustness winner | 0.517 | 0.322 | 0.000 | 0.015 | 0.677 | no dominant failure mode |
| 2 | 0.700 | Rights/capture winner | 0.523 | 0.324 | 0.000 | 0.070 | 0.667 | no dominant failure mode |
| 3 | 0.700 | Legitimacy-first winner | 0.523 | 0.324 | 0.000 | 0.070 | 0.667 | no dominant failure mode |
| 4 | 0.495 | Balanced winner | 0.566 | 0.258 | 0.000 | 1.000 | 0.405 | weak starting floor; public alignment erosion; uncorrected rights backlog; legitimacy erosion |
| 5 | 0.471 | Minimax-regret winner | 0.549 | 0.215 | 0.000 | 1.000 | 0.344 | low policy quality; public alignment erosion; uncorrected rights backlog; legitimacy erosion |
| 6 | 0.447 | Efficiency caution case | 0.565 | 0.170 | 0.000 | 1.000 | 0.272 | low policy quality; public alignment erosion; uncorrected rights backlog; legitimacy erosion |
| 7 | 0.240 | Current-system-ish baseline | 0.265 | 0.000 | 0.593 | 1.000 | 0.086 | weak starting floor; low policy quality; public alignment erosion; capture drift; uncorrected rights backlog; legitimacy erosion; delivery bottleneck |

## Federalism and Agency-Capacity Stress
Subnational resistance, agency undercapacity, procurement friction, and implementation bottlenecks weaken delivery, compliance, and correction capacity.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.674 | Balanced winner | 0.513 | 0.300 | 0.000 | 0.017 | 0.631 | weak starting floor |
| 2 | 0.664 | Rights/capture winner | 0.449 | 0.261 | 0.000 | 0.015 | 0.640 | no dominant failure mode |
| 3 | 0.664 | Legitimacy-first winner | 0.449 | 0.261 | 0.000 | 0.015 | 0.640 | no dominant failure mode |
| 4 | 0.664 | Minimax-regret winner | 0.500 | 0.285 | 0.000 | 0.015 | 0.604 | weak starting floor |
| 5 | 0.661 | Robustness winner | 0.442 | 0.257 | 0.000 | 0.015 | 0.633 | no dominant failure mode |
| 6 | 0.622 | Efficiency caution case | 0.511 | 0.256 | 0.000 | 0.149 | 0.520 | weak starting floor |
| 7 | 0.387 | Current-system-ish baseline | 0.228 | 0.000 | 0.704 | 0.001 | 0.276 | weak starting floor; low policy quality; public alignment erosion; capture drift; legitimacy erosion; delivery bottleneck |

## High Capture Pressure
Organized interests adapt more aggressively, capture pressure starts higher, and capture controls are less effective.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.498 | Robustness winner | 0.476 | 0.025 | 0.529 | 0.000 | 0.440 | low policy quality; public alignment erosion; legitimacy erosion |
| 2 | 0.463 | Rights/capture winner | 0.480 | 0.000 | 0.615 | 0.058 | 0.410 | low policy quality; public alignment erosion; capture drift; legitimacy erosion |
| 3 | 0.463 | Legitimacy-first winner | 0.480 | 0.000 | 0.615 | 0.058 | 0.410 | low policy quality; public alignment erosion; capture drift; legitimacy erosion |
| 4 | 0.308 | Current-system-ish baseline | 0.244 | 0.000 | 1.000 | 0.083 | 0.132 | weak starting floor; low policy quality; public alignment erosion; capture drift; legitimacy erosion; delivery bottleneck |
| 5 | 0.196 | Balanced winner | 0.515 | 0.000 | 1.000 | 1.000 | 0.114 | weak starting floor; low policy quality; public alignment erosion; capture drift; uncorrected rights backlog; legitimacy erosion |
| 6 | 0.189 | Minimax-regret winner | 0.505 | 0.000 | 1.000 | 1.000 | 0.087 | low policy quality; public alignment erosion; capture drift; uncorrected rights backlog; legitimacy erosion |
| 7 | 0.166 | Efficiency caution case | 0.512 | 0.000 | 1.000 | 1.000 | 0.000 | low policy quality; public alignment erosion; capture drift; uncorrected rights backlog; legitimacy erosion |

## High Rights-Threat Environment
Bad-policy inflow is more likely to create rights-threatening review pressure.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.721 | Rights/capture winner | 0.534 | 0.322 | 0.000 | 0.000 | 0.711 | no dominant failure mode |
| 2 | 0.721 | Legitimacy-first winner | 0.534 | 0.322 | 0.000 | 0.000 | 0.711 | no dominant failure mode |
| 3 | 0.718 | Robustness winner | 0.526 | 0.317 | 0.000 | 0.000 | 0.705 | no dominant failure mode |
| 4 | 0.611 | Balanced winner | 0.590 | 0.308 | 0.000 | 0.551 | 0.576 | weak starting floor; uncorrected rights backlog |
| 5 | 0.500 | Minimax-regret winner | 0.567 | 0.233 | 0.000 | 1.000 | 0.443 | low policy quality; public alignment erosion; uncorrected rights backlog; legitimacy erosion |
| 6 | 0.483 | Efficiency caution case | 0.588 | 0.199 | 0.000 | 1.000 | 0.388 | low policy quality; public alignment erosion; uncorrected rights backlog; legitimacy erosion |
| 7 | 0.405 | Current-system-ish baseline | 0.282 | 0.000 | 0.438 | 0.408 | 0.314 | weak starting floor; low policy quality; public alignment erosion; legitimacy erosion; delivery bottleneck |

## Low Public Trust
Legitimacy and compliance start lower, and public-alignment losses have stronger legitimacy effects.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.679 | Balanced winner | 0.560 | 0.321 | 0.000 | 0.026 | 0.586 | weak starting floor |
| 2 | 0.674 | Efficiency caution case | 0.580 | 0.314 | 0.000 | 0.027 | 0.554 | no dominant failure mode |
| 3 | 0.673 | Minimax-regret winner | 0.552 | 0.308 | 0.000 | 0.025 | 0.569 | no dominant failure mode |
| 4 | 0.669 | Rights/capture winner | 0.491 | 0.280 | 0.000 | 0.024 | 0.594 | no dominant failure mode |
| 5 | 0.669 | Legitimacy-first winner | 0.491 | 0.280 | 0.000 | 0.024 | 0.594 | no dominant failure mode |
| 6 | 0.666 | Robustness winner | 0.484 | 0.275 | 0.000 | 0.023 | 0.589 | no dominant failure mode |
| 7 | 0.431 | Current-system-ish baseline | 0.260 | 0.000 | 0.505 | 0.000 | 0.269 | weak starting floor; low policy quality; public alignment erosion; legitimacy erosion; delivery bottleneck |
