# Interbranch Bridge v0 Stability Definitions

Generated: `2026-08-30T16:31:26+00:00`

These definitions are computed over the focused bridge case set in `config/interbranch-bridge-v0.json`. They are alternative summaries of the same stress-profile results, not separate empirical validations.

| Criterion | Winner | Winner Metric | Interpretation |
| --- | --- | --- | --- |
| Wins/top-two rule | Balanced winner | 5 wins; 5 top-two placements; average rank 2.250 | Ranks cases by stress-profile wins, then top-two placements, then average stress rank. |
| Best average stress rank | Balanced winner | average rank 2.250; worst rank 5 | Ranks cases by average rank across stress profiles, regardless of how wins are distributed. |
| Best average bridge score | Robustness winner | average bridge score 0.667 | Ranks cases by mean bridge score across stress profiles. |
| Lowest maximum stress regret | Robustness winner | max stress regret 0.015; average regret 0.009 | Ranks cases by the smallest worst gap from the winning score in any stress profile. |
| Smallest score spread | Robustness winner | score spread 0.221 | Ranks cases by the smallest difference between best and worst stress-profile bridge score. |
