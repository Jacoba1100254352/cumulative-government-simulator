# Cumulative Design Notes

## Purpose

The cumulative project compares government designs as portfolios. A portfolio combines:

- a legislative structure from the Congress simulator
- a constitutional-review structure from the Supreme Court / constitutional-review simulator
- an anti-capture structure from the lobbying simulator

This framing avoids treating "best government" as a single mechanism. A high-throughput legislature can still need review and anti-capture safeguards. A strong court can still be undermined by capture, delay, or political retaliation. An anti-capture system can still fail if the legislature cannot pass broadly beneficial policy.

## Source Reports

Default inputs are intentionally existing campaign artifacts:

- Congress: `simulation-campaign-v21-paper.csv`
- Constitutional review: `constitutional-review-campaign-v2.csv`
- Lobby capture: `lobby-capture-campaign.csv`

Each source is aggregated by `scenarioKey`. When a source has multiple case rows for a scenario, rows are weighted by `caseWeight` if present; otherwise each row receives equal weight.

## Component Scoring

Each component receives a 0-1 score from available source columns. Missing columns are skipped rather than filled with fake certainty.

Legislative scoring emphasizes:

- directional score
- representative quality
- risk control
- administrative feasibility
- productivity
- welfare and public alignment
- democratic responsiveness and legitimacy
- penalties for gridlock, low-support passage, lobby capture, private-gain ratios, concentrated-harm passage, and administrative cost

Review scoring emphasizes:

- directional score
- stability and rights protection
- legitimacy and public confidence
- democratic responsiveness
- independence/accountability balance
- penalties for partisan alignment, shadow-docket abuse, emergency legitimacy risk, constitutional conflict, reversal/invalidation pressure, and administrative/institutional cost

Anti-capture scoring emphasizes:

- directional score
- capture control
- representation
- reform feasibility
- anti-capture success
- public interest
- disclosure, detection, sanctions, and net transparency gain
- penalties for capture rate, public-preference distortion, private-gain ratios, hidden influence, preserved influence capacity, reform decay, and administrative cost

## Portfolio Scoring

The portfolio score combines diagnostics rather than using only the three component scores:

- policy delivery
- public alignment
- rights safeguard
- capture resistance
- legitimacy
- efficiency
- resilience floor
- complexity score

The "resilience floor" is deliberately conservative. A portfolio that performs very well in two subsystems but collapses in capture resistance, rights protection, or complexity should not outrank a more balanced package.

## Scoring Profiles

The default balanced score is no longer the only ranking. The report builder also reranks every portfolio under five alternate profiles:

- efficiency-first: emphasizes policy delivery, implementation efficiency, and low complexity
- rights-first: emphasizes constitutional safeguards, legal stability, legitimacy, and subsystem floor
- anti-capture-first: emphasizes capture resistance, public alignment, legitimacy, and transparency
- low-complexity: emphasizes low administrative burden, efficiency, and subsystem floor
- legitimacy-first: emphasizes legitimacy, democratic/public alignment, rights safeguards, and capture resistance

Each profile is explicit in `scripts/build_portfolios.py`. This makes the normative choice visible. A portfolio that wins only one profile is interesting, but a portfolio that remains strong across profiles is a better candidate for the paper's core institutional design argument.

## Robustness Report

`reports/portfolio-robustness.csv` and `.md` summarize cross-profile durability. The robust score uses:

- average rank across profiles
- worst rank across profiles
- number of top-10, top-25, and top-100 profile appearances
- score spread across profiles
- the portfolio's resilience floor

The robustness report is intentionally separate from the balanced report. A balanced-score winner can still be fragile if a modest change in weights pushes it far down the list.

## Uncertainty, Regret, and Fragility

`reports/cumulative-government-portfolios.csv` includes synthetic uncertainty bands. These are not empirical confidence intervals. They are conservative model-sensitivity bands that widen when a portfolio combines separately calibrated source artifacts, shows component imbalance, has cross-profile instability, or depends on thin metric coverage. Thin metric coverage is now measured against the configured metric list for each source, not against the maximum coverage observed in the imported rows.

`reports/portfolio-uncertainty-tiers.csv` and `.md` sort the same portfolios by uncertainty lower bound and interval dominance. These reports are meant to prevent point-estimate ranks from being mistaken for separated conclusions when broad synthetic intervals overlap.

`reports/portfolio-minimax-regret.csv` and `.md` rank portfolios by worst-profile regret. Regret is the gap between a portfolio's score and the best available score under each configured value profile. The minimax-regret winner minimizes the largest of those gaps. This is useful for finding broadly non-embarrassing rows, but it is not a recommendation rule by itself because low-regret rows can still be weak on rights, capture, or legitimacy.

`reports/portfolio-profile-tradeoffs.csv` and `.md` compare the focused candidate set profile by profile: balanced winner, robustness winner, minimax-regret winner, profile winners, and the current-system-ish baseline.

`reports/fragile-portfolio-watchlist.csv` and `.md` flag rows that should not be recommended yet. The current criteria include wide synthetic uncertainty, weak subsystem floor, weak public alignment, capture-control vulnerability, administrative complexity, large worst-profile regret, severe profile dependence, and default-passage throughput risk.

## Pareto Front

`reports/pareto-front.csv` and `.md` list exact point-estimate Pareto rows that are not dominated across:

- policy delivery
- public alignment
- rights safeguards
- capture resistance
- legitimacy
- complexity score
- resilience floor

The exact Pareto front is expected to be large because government design involves real tradeoffs. The project also writes `reports/pareto-front-epsilon.csv` / `.md` and `reports/pareto-front-uncertainty.csv` / `.md`. The epsilon front treats tiny diagnostic differences as non-decisive. The uncertainty-aware front requires no point-estimate weakness and a larger uncertainty-scaled advantage before a row can dominate another. The practical use is not to treat any front as a recommendation list; it is to avoid prematurely discarding portfolios that are weaker on a headline score but stronger on a specific constitutional design dimension.

## Interbranch Bridge v0

`scripts/build_interbranch_bridge.py` is the first feedback harness. The equations, thresholds, default period count, and stress profiles are configured in `config/interbranch-bridge-v0.json` rather than embedded only in code. The script does not score all portfolios. Instead, it selects a focused set:

- balanced winner
- minimax-regret winner
- cross-profile robustness winner
- rights/capture winner
- legitimacy-first winner
- efficiency caution case
- current-system-ish baseline

The bridge runs a deterministic 24-period model by default. Each period links:

- legislative delivery to useful policy and bad-policy/rights-threat inflow
- rights-threat and correction backlog to review docket pressure
- review capacity to correction and possible court-curbing pressure
- capture pressure to weak capture controls, throughput, and public-alignment decay
- legitimacy to compliance, policy quality, capture, uncorrected pressure, and court-curbing pressure

The bridge writes:

- `reports/interbranch-bridge-v0.csv`
- `reports/interbranch-bridge-v0.md`
- `reports/interbranch-bridge-v0-timeseries.csv`
- `reports/interbranch-bridge-v0-sensitivity.csv`
- `reports/interbranch-bridge-v0-sensitivity.md`
- `reports/interbranch-bridge-v0-sensitivity-timeseries.csv`
- `reports/interbranch-bridge-v0-stability.csv`
- `reports/interbranch-bridge-v0-assumptions.json`

Bridge v0 is deliberately small and auditable. It is a transition from static portfolio comparison toward an actual interbranch simulator, but it is still a stylized model over already-generated diagnostics.

## Adaptive Bridge v1

`scripts/build_adaptive_bridge.py` is the broader synthetic survival screen. It runs every static portfolio through every configured v0 stress profile, then adds first-pass adaptive mechanisms configured in `config/adaptive-bridge-v1.json`:

- transition load from reform complexity, low subsystem floor, uncertainty, and value-profile regret
- sequencing readiness from front-loaded legality, staffing, transparency, and review capacity
- party adaptation and agenda obstruction
- court adaptation and court-curbing pressure
- lobby adaptation and venue shifting across alternate influence venues
- emergency-powers safeguards against fast, evasive, or normalized executive action
- agency implementation gaps under federalism resistance, delivery bottlenecks, and recovery capacity
- public feedback through asymmetric trust erosion, voter backlash, compliance, and legitimacy
- citizen agenda capacity as a corrective channel, with overload and rights-risk penalties for weakly deliberative tools
- family-level direct-evidence strength used as a recommendation gate caveat

The script writes:

- `reports/adaptive-bridge-v1.csv`
- `reports/adaptive-bridge-v1-summary.csv`
- `reports/adaptive-bridge-v1.md`
- `reports/adaptive-bridge-v1-recommendation-gate.csv`
- `reports/adaptive-bridge-v1-recommendation-gate.md`
- `reports/adaptive-bridge-v1-calibration.md`
- `reports/adaptive-bridge-v1-timeseries.csv`
- `reports/adaptive-bridge-v1-assumptions.json`

Adaptive Bridge v1 is broader than Bridge v0, but it is not more empirical. It now encodes evidence-informed priors from the Deep Research reports, but those priors are directional and not fitted coefficients. It should be used to demote fragile static winners, identify direct family comparisons, and expose where adaptive assumptions need outside evidence. Its recommendation gate has four labels:

- provisional shortlist: passes the current synthetic adaptive screen, but is still not an empirical recommendation
- calibration gray zone, not recommendation: strong enough to validate directly, but still blocked by evidence, stress, regret, or failure-mode caveats
- review priority, not recommendation: interesting enough to model further, but fails at least one gate condition
- do not recommend yet: too fragile under current uncertainty, regret, resilience, or adaptive stress criteria

## Bridge Stress Profiles

The configured stress profiles are:

- baseline: no additional stress modifiers
- high-capture-pressure: higher initial capture pressure, faster capture growth, weaker capture control, and stronger capture penalties
- low-public-trust: weaker starting legitimacy and compliance, plus stronger legitimacy loss from uncorrected pressure and capture
- high-rights-threat: bad-policy inflow creates more review pressure and stronger quality/backlog penalties
- court-curbing-noncompliance: corrective review produces more retaliation pressure, institutional compliance falls, and curbing pressure decays more slowly
- emergency-abuse-stress: emergency action and emergency litigation generate more rights-threatening policy, larger dockets, and stronger legitimacy penalties when review cannot keep up
- administrative-complexity-stress: effective complexity, delivery, review capacity, and compliance are reduced
- federalism-agency-capacity-stress: subnational resistance, agency undercapacity, procurement friction, and implementation bottlenecks weaken delivery, compliance, and correction capacity

The current sensitivity report sorts cross-stress stability by a wins/top-two rule over the focused bridge case set. It also reports average-rank, average-score, minimax-stress-regret, and score-spread stability winners so the paper does not collapse every meaning of stability into one hidden sort. The major exceptions are high-capture pressure and emergency-abuse stress, where the robustness winner takes first and the balanced winner falls under the stress-specific bridge rankings for different reasons.

## Paper Build

The synthesis paper is maintained as LaTeX in `paper/main.tex`. Running `make paper` regenerates the static portfolio reports, refreshes the interbranch bridge reports, writes generated LaTeX fragments into `paper/generated/`, checks the paper's headline claims, recompiles `paper/main.pdf`, and verifies that the public PDF is fresh. Plain `make` defaults to the same target. The PDF is therefore treated as a generated artifact that should be refreshed through the Makefile whenever the reports or paper source change.

The generated paper fragments are intentionally narrow publication artifacts:

- `paper/generated/report-macros.tex`: counts and headline values used in prose.
- `paper/generated/*-table.tex`: source, balanced-winner, uncertainty, minimax-regret, profile, robustness, fragile-watchlist, speculative-agenda, Pareto, bridge, adaptive-bridge, adaptive-calibration, stress-stability, high-capture, method-appendix, and provenance tables.
- `paper/generated/figure-*.tex`: LaTeX-native bridge figures for baseline ranking, stress-rank stability, and the high-capture exception.
- `paper/generated/source-provenance.json`: machine-readable source inventory with SHA-256 hashes for imported sibling CSVs.

`paper/scripts/check_claims.py` verifies structural invariants and generated-macro consistency against the current report artifacts. It no longer freezes current winners as hard-coded expected conclusions; winner names, stress winners, and stability leaders are generated from the reports. It still rejects known overclaiming phrases and fails when required generated fragments or rank structures are missing.

`paper/scripts/check_latex_log.py` verifies the compiled LaTeX log. It fails on LaTeX errors, undefined citations/references, package errors, and overfull/underfull boxes. This makes PDF generation a real publication check rather than only a file-existence check.

`paper/scripts/check_pdf_freshness.py` verifies the public PDF after generation and during `make test`. It fails if `paper/main.pdf` is older than `paper/main.tex`, any generated paper fragment, any report CSV/JSON artifact, either bridge configuration, the source-generation scripts, or the imported sibling simulator CSVs. It also fails if `paper/main.pdf` does not byte-match `paper/build/main.pdf`, or if the SHA-256 values recorded in `paper/generated/source-provenance.json` no longer match the sibling source CSVs.

`make test` runs the same pipeline hermetically, then checks the production PDF freshness gate. It writes reports into `reports/.test-output/`, generated paper fragments into `paper/.test-generated/`, and compiles `paper/test-main.tex` into `paper/.test-build/`. The test wrapper sets `\GeneratedDir` to the temp fragment directory before loading `paper/main.tex`, then the Makefile removes the temp directories after a successful check.

The production paper uses `\GeneratedDir` as an overridable generated-fragment root:

- production build: `\GeneratedDir` defaults to `paper/generated/`
- test build: `paper/test-main.tex` sets it to `paper/.test-generated/`

That boundary is important. It lets the test target prove that the paper can be built from fresh data without mutating the checked production fragments or the user-facing PDF.

## Current Boundary

The importer is not a causal empirical model. The portfolio scorer ranks candidate bundles from existing campaign outputs. Bridge v0 adds deterministic feedback over a focused set of cases, and Adaptive Bridge v1 expands that feedback to every portfolio with synthetic adaptive mechanisms. Neither bridge reruns the sibling simulators or estimates real-world causal magnitudes.

The next serious extension would be a deeper bridge model:

- legislative outputs become dockets for review
- review outcomes feed back into legislative correction and court-curbing pressure
- capture outcomes alter proposal access, rulemaking, enforcement, and review stress
- procedural-access metrics from `Civ Pro` enter as access-to-justice and litigation-cost diagnostics
- adaptive parameters are calibrated against historical institutional-transition cases, not only chosen as transparent sensitivity assumptions
- phased reform sequences become explicit candidate mechanisms rather than speculative notes
