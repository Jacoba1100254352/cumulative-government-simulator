# Interbranch Bridge v0 Sensitivity

Generated: `2026-05-12T02:04:27+00:00`

This report reruns the same focused bridge cases under every stress profile defined in `/Users/jacobanderson/Documents/simulators/Cumulative Government Simulator/config/interbranch-bridge-v0.json`. The question is whether the baseline bridge winner remains stable when capture pressure, public trust, rights threat, emergency abuse, institutional noncompliance, administrative overload, or federalism/agency-capacity constraints become worse. It is not a full bridge run over every portfolio.

## Stress Winners

| Stress Profile | Winner | Score | Final Quality | Final Legitimacy | Winner Failure Modes |
| --- | --- | --- | --- | --- | --- |
| Administrative Overload and Complexity Stress | Balanced winner | 0.690 | 0.310 | 0.653 | weak starting floor |
| Baseline | Balanced winner | 0.723 | 0.350 | 0.697 | weak starting floor |
| Court-Curbing and Institutional Noncompliance Stress | Balanced winner | 0.699 | 0.342 | 0.655 | weak starting floor |
| Emergency Abuse Stress | Robustness winner | 0.709 | 0.312 | 0.680 | no dominant failure mode |
| Federalism and Agency-Capacity Stress | Balanced winner | 0.670 | 0.292 | 0.624 | weak starting floor |
| High Capture Pressure | Robustness winner | 0.479 | 0.003 | 0.420 | low policy quality; public alignment erosion; capture drift; legitimacy erosion |
| High Rights-Threat Environment | Rights/capture winner | 0.718 | 0.315 | 0.707 | no dominant failure mode |
| Low Public Trust | Balanced winner | 0.675 | 0.313 | 0.581 | weak starting floor |

## Cross-Stress Stability

The table below is sorted by the wins/top-two rule. The criterion-winner table shows how the conclusion changes under other defensible stability definitions.

| Win/Top-2 Rank | Case | Avg Rank | Worst Rank | Wins | Top-2 Profiles | Avg Score | Max Regret | Score Spread |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Balanced winner | 2.250 | 5 | 5 | 5 | 0.593 | 0.289 | 0.534 |
| 2 | Robustness winner | 4.125 | 6 | 2 | 2 | 0.661 | 0.015 | 0.236 |
| 3 | Rights/capture winner | 2.625 | 4 | 1 | 5 | 0.660 | 0.033 | 0.273 |
| 4 | Efficiency caution case | 4.625 | 7 | 0 | 3 | 0.556 | 0.314 | 0.554 |
| 5 | Legitimacy-first winner | 3.625 | 5 | 0 | 1 | 0.660 | 0.033 | 0.273 |
| 6 | Minimax-regret winner | 4.125 | 6 | 0 | 0 | 0.570 | 0.298 | 0.535 |
| 7 | Current-system-ish baseline | 6.625 | 7 | 0 | 0 | 0.379 | 0.483 | 0.248 |

## Stability Criterion Winners

| Criterion | Winner | Winner Metric | Interpretation |
| --- | --- | --- | --- |
| Wins/top-two rule | Balanced winner | 5 wins; 5 top-two placements; average rank 2.250 | Ranks cases by stress-profile wins, then top-two placements, then average stress rank. |
| Best average stress rank | Balanced winner | average rank 2.250; worst rank 5 | Ranks cases by average rank across stress profiles, regardless of how wins are distributed. |
| Best average bridge score | Robustness winner | average bridge score 0.661 | Ranks cases by mean bridge score across stress profiles. |
| Lowest maximum stress regret | Robustness winner | max stress regret 0.015; average regret 0.009 | Ranks cases by the smallest worst gap from the winning score in any stress profile. |
| Smallest score spread | Robustness winner | score spread 0.236 | Ranks cases by the smallest difference between best and worst stress-profile bridge score. |

## Administrative Overload and Complexity Stress
Implementation is harder: effective complexity, delivery, review capacity, and compliance are reduced.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.690 | Balanced winner | 0.534 | 0.310 | 0.000 | 0.020 | 0.653 | weak starting floor |
| 2 | 0.681 | Rights/capture winner | 0.468 | 0.271 | 0.000 | 0.018 | 0.664 | no dominant failure mode |
| 3 | 0.681 | Legitimacy-first winner | 0.468 | 0.271 | 0.000 | 0.018 | 0.664 | no dominant failure mode |
| 4 | 0.680 | Minimax-regret winner | 0.523 | 0.296 | 0.000 | 0.018 | 0.626 | weak starting floor |
| 5 | 0.677 | Robustness winner | 0.457 | 0.264 | 0.000 | 0.018 | 0.657 | no dominant failure mode |
| 6 | 0.656 | Efficiency caution case | 0.541 | 0.282 | 0.000 | 0.095 | 0.568 | weak starting floor |
| 7 | 0.410 | Current-system-ish baseline | 0.253 | 0.000 | 0.666 | 0.001 | 0.310 | weak starting floor; low policy quality; public alignment erosion; capture drift; legitimacy erosion; delivery bottleneck |

## Baseline
Default bridge coefficients with no additional stress modifiers.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.723 | Balanced winner | 0.601 | 0.350 | 0.000 | 0.028 | 0.697 | weak starting floor |
| 2 | 0.719 | Efficiency caution case | 0.627 | 0.345 | 0.000 | 0.029 | 0.661 | no dominant failure mode |
| 3 | 0.715 | Minimax-regret winner | 0.595 | 0.337 | 0.000 | 0.027 | 0.675 | no dominant failure mode |
| 4 | 0.713 | Rights/capture winner | 0.528 | 0.305 | 0.000 | 0.026 | 0.708 | no dominant failure mode |
| 5 | 0.713 | Legitimacy-first winner | 0.528 | 0.305 | 0.000 | 0.026 | 0.708 | no dominant failure mode |
| 6 | 0.709 | Robustness winner | 0.516 | 0.298 | 0.000 | 0.025 | 0.700 | no dominant failure mode |
| 7 | 0.474 | Current-system-ish baseline | 0.297 | 0.000 | 0.479 | 0.000 | 0.391 | weak starting floor; low policy quality; public alignment erosion; legitimacy erosion; delivery bottleneck |

## Court-Curbing and Institutional Noncompliance Stress
Corrective review creates more retaliation pressure, institutional compliance falls, and court-curbing pressure decays slowly.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.699 | Balanced winner | 0.593 | 0.342 | 0.000 | 0.028 | 0.655 | weak starting floor |
| 2 | 0.694 | Efficiency caution case | 0.617 | 0.336 | 0.000 | 0.029 | 0.618 | no dominant failure mode |
| 3 | 0.692 | Minimax-regret winner | 0.586 | 0.329 | 0.000 | 0.027 | 0.633 | no dominant failure mode |
| 4 | 0.688 | Rights/capture winner | 0.521 | 0.298 | 0.000 | 0.025 | 0.664 | no dominant failure mode |
| 5 | 0.688 | Legitimacy-first winner | 0.521 | 0.298 | 0.000 | 0.025 | 0.664 | no dominant failure mode |
| 6 | 0.684 | Robustness winner | 0.509 | 0.291 | 0.000 | 0.025 | 0.657 | no dominant failure mode |
| 7 | 0.450 | Current-system-ish baseline | 0.292 | 0.000 | 0.499 | 0.000 | 0.350 | weak starting floor; low policy quality; public alignment erosion; legitimacy erosion; delivery bottleneck |

## Emergency Abuse Stress
Emergency action and emergency litigation generate more rights-threatening policy, larger review dockets, and stronger legitimacy penalties when review cannot keep up.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.709 | Robustness winner | 0.506 | 0.312 | 0.000 | 0.003 | 0.680 | no dominant failure mode |
| 2 | 0.705 | Rights/capture winner | 0.516 | 0.319 | 0.000 | 0.030 | 0.672 | no dominant failure mode |
| 3 | 0.705 | Legitimacy-first winner | 0.516 | 0.319 | 0.000 | 0.030 | 0.672 | no dominant failure mode |
| 4 | 0.492 | Balanced winner | 0.556 | 0.252 | 0.000 | 1.000 | 0.400 | weak starting floor; public alignment erosion; uncorrected rights backlog; legitimacy erosion |
| 5 | 0.467 | Minimax-regret winner | 0.541 | 0.208 | 0.000 | 1.000 | 0.337 | low policy quality; public alignment erosion; uncorrected rights backlog; legitimacy erosion |
| 6 | 0.443 | Efficiency caution case | 0.557 | 0.162 | 0.000 | 1.000 | 0.264 | low policy quality; public alignment erosion; uncorrected rights backlog; legitimacy erosion |
| 7 | 0.227 | Current-system-ish baseline | 0.272 | 0.000 | 0.642 | 1.000 | 0.063 | weak starting floor; low policy quality; public alignment erosion; capture drift; uncorrected rights backlog; legitimacy erosion; delivery bottleneck |

## Federalism and Agency-Capacity Stress
Subnational resistance, agency undercapacity, procurement friction, and implementation bottlenecks weaken delivery, compliance, and correction capacity.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.670 | Balanced winner | 0.504 | 0.292 | 0.000 | 0.017 | 0.624 | weak starting floor |
| 2 | 0.661 | Rights/capture winner | 0.442 | 0.255 | 0.000 | 0.015 | 0.636 | no dominant failure mode |
| 3 | 0.661 | Legitimacy-first winner | 0.442 | 0.255 | 0.000 | 0.015 | 0.636 | no dominant failure mode |
| 4 | 0.660 | Minimax-regret winner | 0.493 | 0.278 | 0.000 | 0.015 | 0.597 | weak starting floor |
| 5 | 0.657 | Robustness winner | 0.431 | 0.249 | 0.000 | 0.015 | 0.629 | low policy quality |
| 6 | 0.617 | Efficiency caution case | 0.505 | 0.248 | 0.000 | 0.153 | 0.511 | weak starting floor; low policy quality |
| 7 | 0.377 | Current-system-ish baseline | 0.235 | 0.000 | 0.738 | 0.022 | 0.267 | weak starting floor; low policy quality; public alignment erosion; capture drift; legitimacy erosion; delivery bottleneck |

## High Capture Pressure
Organized interests adapt more aggressively, capture pressure starts higher, and capture controls are less effective.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.479 | Robustness winner | 0.462 | 0.003 | 0.573 | 0.006 | 0.420 | low policy quality; public alignment erosion; capture drift; legitimacy erosion |
| 2 | 0.446 | Rights/capture winner | 0.470 | 0.000 | 0.661 | 0.083 | 0.389 | low policy quality; public alignment erosion; capture drift; legitimacy erosion |
| 3 | 0.446 | Legitimacy-first winner | 0.470 | 0.000 | 0.661 | 0.083 | 0.389 | low policy quality; public alignment erosion; capture drift; legitimacy erosion |
| 4 | 0.304 | Current-system-ish baseline | 0.253 | 0.000 | 1.000 | 0.120 | 0.129 | weak starting floor; low policy quality; public alignment erosion; capture drift; legitimacy erosion; delivery bottleneck |
| 5 | 0.189 | Balanced winner | 0.502 | 0.000 | 1.000 | 1.000 | 0.095 | weak starting floor; low policy quality; public alignment erosion; capture drift; uncorrected rights backlog; legitimacy erosion |
| 6 | 0.180 | Minimax-regret winner | 0.494 | 0.000 | 1.000 | 1.000 | 0.059 | low policy quality; public alignment erosion; capture drift; uncorrected rights backlog; legitimacy erosion |
| 7 | 0.165 | Efficiency caution case | 0.505 | 0.000 | 1.000 | 1.000 | 0.000 | low policy quality; public alignment erosion; capture drift; uncorrected rights backlog; legitimacy erosion |

## High Rights-Threat Environment
Bad-policy inflow is more likely to create rights-threatening review pressure.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.718 | Rights/capture winner | 0.526 | 0.315 | 0.000 | 0.000 | 0.707 | no dominant failure mode |
| 2 | 0.718 | Legitimacy-first winner | 0.526 | 0.315 | 0.000 | 0.000 | 0.707 | no dominant failure mode |
| 3 | 0.714 | Robustness winner | 0.514 | 0.307 | 0.000 | 0.000 | 0.701 | no dominant failure mode |
| 4 | 0.609 | Balanced winner | 0.580 | 0.301 | 0.000 | 0.539 | 0.570 | weak starting floor |
| 5 | 0.495 | Minimax-regret winner | 0.559 | 0.225 | 0.000 | 1.000 | 0.435 | low policy quality; public alignment erosion; uncorrected rights backlog; legitimacy erosion |
| 6 | 0.480 | Efficiency caution case | 0.581 | 0.195 | 0.000 | 1.000 | 0.384 | low policy quality; public alignment erosion; uncorrected rights backlog; legitimacy erosion |
| 7 | 0.365 | Current-system-ish baseline | 0.289 | 0.000 | 0.491 | 0.573 | 0.279 | weak starting floor; low policy quality; public alignment erosion; uncorrected rights backlog; legitimacy erosion; delivery bottleneck |

## Low Public Trust
Legitimacy and compliance start lower, and public-alignment losses have stronger legitimacy effects.

| Rank | Score | Case | Avg Delivery | Final Quality | Final Capture | Final Backlog | Final Legitimacy | Failure Modes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.675 | Balanced winner | 0.550 | 0.313 | 0.000 | 0.026 | 0.581 | weak starting floor |
| 2 | 0.672 | Efficiency caution case | 0.574 | 0.308 | 0.000 | 0.027 | 0.549 | no dominant failure mode |
| 3 | 0.669 | Minimax-regret winner | 0.545 | 0.302 | 0.000 | 0.025 | 0.564 | no dominant failure mode |
| 4 | 0.666 | Rights/capture winner | 0.483 | 0.273 | 0.000 | 0.024 | 0.590 | no dominant failure mode |
| 5 | 0.666 | Legitimacy-first winner | 0.483 | 0.273 | 0.000 | 0.024 | 0.590 | no dominant failure mode |
| 6 | 0.663 | Robustness winner | 0.472 | 0.267 | 0.000 | 0.023 | 0.585 | no dominant failure mode |
| 7 | 0.426 | Current-system-ish baseline | 0.268 | 0.000 | 0.533 | 0.000 | 0.264 | weak starting floor; low policy quality; public alignment erosion; legitimacy erosion; delivery bottleneck |
