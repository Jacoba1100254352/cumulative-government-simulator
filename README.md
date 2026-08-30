# Cumulative Government Simulator

This project is the integration layer for the neighboring government simulator projects. It is intentionally paper-first and simulator-light: the goal is to compare institutional portfolios by combining existing campaign outputs rather than building a vague all-of-government simulation from scratch.

The current cumulative harness imports:

- legislative outputs from `../Congress Institutional Simulator/reports/simulation-campaign-v21-paper.csv`
- constitutional-review outputs from `../Supreme Court Simulator Design/reports/constitutional-review-campaign-v2.csv`
- lobbying and capture outputs from `../Lobby Capture Simulator/reports/lobby-capture-campaign.csv`

`../Civ Pro` is not imported yet because it is currently a civil-procedure learning game rather than a government-performance campaign simulator. It can be added later if it exports comparable metrics for access to justice, procedural fairness, litigation cost, or rule compliance.

## Run

```sh
make report
```

This writes:

- `reports/component-scores.csv`
- `reports/cumulative-government-portfolios.csv`
- `reports/cumulative-government-portfolios.md`
- `reports/profile-sensitivity.csv`
- `reports/profile-sensitivity.md`
- `reports/portfolio-robustness.csv`
- `reports/portfolio-robustness.md`
- `reports/portfolio-minimax-regret.csv`
- `reports/portfolio-minimax-regret.md`
- `reports/portfolio-profile-tradeoffs.csv`
- `reports/portfolio-profile-tradeoffs.md`
- `reports/fragile-portfolio-watchlist.csv`
- `reports/fragile-portfolio-watchlist.md`
- `reports/portfolio-uncertainty-tiers.csv`
- `reports/portfolio-uncertainty-tiers.md`
- `reports/pareto-front.csv`
- `reports/pareto-front.md`
- `reports/pareto-front-epsilon.csv`
- `reports/pareto-front-epsilon.md`
- `reports/pareto-front-uncertainty.csv`
- `reports/pareto-front-uncertainty.md`
- `reports/speculative-modeling-agenda.md`
- `reports/source-inventory.json`

Run the focused interbranch feedback harness and the all-portfolio adaptive bridge:

```sh
make bridge
```

This also refreshes the portfolio reports and writes:

- `reports/interbranch-bridge-v0.csv`
- `reports/interbranch-bridge-v0.md`
- `reports/interbranch-bridge-v0-timeseries.csv`
- `reports/interbranch-bridge-v0-sensitivity.csv`
- `reports/interbranch-bridge-v0-sensitivity.md`
- `reports/interbranch-bridge-v0-sensitivity-timeseries.csv`
- `reports/interbranch-bridge-v0-stability.csv`
- `reports/interbranch-bridge-v0-stability-definitions.csv`
- `reports/interbranch-bridge-v0-stability-definitions.md`
- `reports/interbranch-bridge-v0-assumptions.json`
- `reports/adaptive-bridge-v1.csv`
- `reports/adaptive-bridge-v1-summary.csv`
- `reports/adaptive-bridge-v1.md`
- `reports/adaptive-bridge-v1-recommendation-gate.csv`
- `reports/adaptive-bridge-v1-recommendation-gate.md`
- `reports/adaptive-bridge-v1-calibration.md`
- `reports/adaptive-bridge-v1-timeseries.csv`
- `reports/adaptive-bridge-v1-assumptions.json`

Refresh every generated artifact used by the paper and compile the LaTeX paper to PDF:

```sh
make paper
```

Plain `make` also defaults to this target.

This refreshes the report CSV/Markdown files, writes generated LaTeX tables, bridge figures, input-provenance metadata, and appendix fragments into `paper/generated/`, verifies the paper's headline claims against the reports, checks the LaTeX log for layout/build warnings, writes `paper/main.pdf` from `paper/main.tex`, and verifies that the public PDF is fresh.

Check whether the committed/public PDF is current without rebuilding it:

```sh
make paper-freshness
```

This fails if `paper/main.pdf` is older than the paper source, generated fragments, report CSV/JSON artifacts, bridge configs, source-generation scripts, or imported sibling simulator CSVs. It also fails if `paper/main.pdf` does not match `paper/build/main.pdf`, or if the recorded source hashes in `paper/generated/source-provenance.json` no longer match the imported sibling reports.

Run a hermetic syntax, report-build, paper-claim, LaTeX-log, PDF-build, and production-PDF freshness check:

```sh
make test
```

`make test` builds reports under `reports/.test-output/`, paper fragments under `paper/.test-generated/`, and a temporary wrapper PDF under `paper/.test-build/`. Those temp directories are removed when the check completes, so the production reports, generated paper fragments, and `paper/main.pdf` are not mutated by the test target.

## Version Control

The repository tracks the simulator code and configuration, documentation, paper source and PDF, generated LaTeX fragments, Markdown report summaries, and compact diagnostic data. Large row-level CSVs produced by the portfolio and adaptive-bridge builds are intentionally ignored because they are reproducible and would otherwise make ordinary Git history impractically large. Run `make report` or `make bridge` beside the sibling simulator repositories to regenerate them locally.

## Project Shape

- `scripts/build_portfolios.py`: dependency-free importer and static portfolio scorer.
- `scripts/build_interbranch_bridge.py`: focused interbranch feedback harness.
- `scripts/build_adaptive_bridge.py`: synthetic all-portfolio adaptive survival screen.
- `config/interbranch-bridge-v0.json`: editable bridge coefficients, thresholds, and stress profiles.
- `config/adaptive-bridge-v1.json`: editable adaptive survival mechanisms, score weights, research-calibration priors, and recommendation gate thresholds.
- `docs/design.md`: scoring model, boundaries, and extension notes.
- `paper/scripts/generate_tables.py`: report-to-LaTeX fragment generator for paper tables and bridge figures.
- `paper/scripts/check_claims.py`: paper claim checker against current report artifacts.
- `paper/scripts/check_latex_log.py`: LaTeX log gate for errors, undefined references, and overfull/underfull boxes.
- `paper/scripts/check_pdf_freshness.py`: production PDF freshness gate.
- `paper/main.tex`: canonical LaTeX synthesis paper.
- `paper/test-main.tex`: test-only wrapper that compiles the paper against hermetic generated fragments.
- `paper/generated/`: generated LaTeX macros, tables, figure fragments, appendix fragments, and source-provenance metadata used by the paper.
- `paper/main.pdf`: generated PDF from the LaTeX paper.
- `reports/`: generated portfolio rankings and component summaries.

## Current Report Layers

The cumulative harness now produces complementary views:

- balanced ranking: the default score over delivery, alignment, rights, capture resistance, legitimacy, efficiency, and subsystem floor, now with synthetic uncertainty bands
- uncertainty tiers: lower-bound and interval-dominance rankings that show when point-estimate ranks are not separated by synthetic uncertainty bands
- profile sensitivity: alternative rankings for efficiency-first, rights-first, anti-capture-first, low-complexity, and legitimacy-first priorities
- robustness: portfolios that remain strong across multiple value profiles, even if they are not the balanced-score winner
- minimax regret: portfolios with the smallest worst-profile loss across the configured value profiles
- focused profile tradeoffs: side-by-side ranks for the headline candidate families
- do-not-recommend-yet watchlist: attractive rows that are fragile under uncertainty, regret, floor, alignment, capture, complexity, or default-passage diagnostics
- Pareto fronts: exact point-estimate, epsilon, and uncertainty-aware filters across the major diagnostic dimensions
- interbranch bridge: focused feedback simulation for the balanced, minimax-regret, robust, rights/capture, legitimacy, efficiency-caution, and current-system-ish cases
- bridge sensitivity: the same focused cases under baseline, high-capture, low-trust, rights-threat, emergency-abuse, court-curbing/noncompliance, administrative-overload, and federalism/agency-capacity stress profiles, with alternative stability definitions
- adaptive bridge: all-portfolio synthetic survival screen over sequencing, emergency safeguards, federalism/capacity constraints, party, court, lobby, agency, voter, transition, and citizen-agenda adaptation mechanisms
- adaptive recommendation gate: separates provisional shortlist rows, calibration gray-zone rows, review-priority rows, and do-not-recommend-yet rows
- speculative modeling agenda: systems not yet fully modeled, including phased reform sequences, transition costs, federalism/agency constraints, public implementation feedback, and citizen agenda-setting mechanisms

## Interpretation Boundary

The cumulative score is a decision aid, not a claim that one generated government design is objectively optimal. The reports are meant to surface durable tradeoffs:

- throughput versus harmful or weak-mandate policy passage
- rights protection versus review delay, review cost, and countermajoritarian pressure
- capture resistance versus administrative complexity and reform evasion
- legitimacy versus strategic manipulation under stress

The strongest use of this project is to identify a small set of plausible institutional portfolios and then examine why they rank well across the separate simulators.

## Paper Guardrails

The paper is intentionally kept coupled to the generated reports instead of hand-maintained tables. The current guardrails are:

- generated LaTeX fragments for every report-backed table and figure used in `paper/main.tex`
- generated method appendix tables for diagnostic formulas, scoring-profile weights, bridge-score weights, and stress-profile modifiers
- generated uncertainty-resolution, uncertainty, minimax-regret, focused-profile-tradeoff, fragile-watchlist, bridge-scope, bridge-stability-definition, adaptive-bridge, adaptive-calibration, adaptive-gate, and speculative-agenda tables
- generated source-provenance records in `paper/generated/source-provenance.json` and `paper/generated/source-provenance-table.tex`, including SHA-256 hashes for imported sibling CSVs
- `paper/scripts/check_claims.py` to verify generated-macro consistency and structural report invariants without freezing current winners as permanent fixtures
- `paper/scripts/check_latex_log.py` to fail PDF builds with LaTeX errors, undefined references, or layout warnings
- `paper/scripts/check_pdf_freshness.py` to fail when `paper/main.pdf` is stale, detached from `paper/build/main.pdf`, or based on changed source CSVs
- `make test` to verify all of the above through temp output directories before touching production artifacts
