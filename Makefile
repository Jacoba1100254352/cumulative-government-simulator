PYTHON ?= python3
LATEXMK ?= latexmk
.DEFAULT_GOAL := paper
REPORT_BUILDER := scripts/build_portfolios.py
BRIDGE_BUILDER := scripts/build_interbranch_bridge.py
ADAPTIVE_BRIDGE_BUILDER := scripts/build_adaptive_bridge.py
PAPER_TABLE_BUILDER := paper/scripts/generate_tables.py
PAPER_CLAIM_CHECKER := paper/scripts/check_claims.py
PAPER_LOG_CHECKER := paper/scripts/check_latex_log.py
PAPER_FRESHNESS_CHECKER := paper/scripts/check_pdf_freshness.py
PAPER_TEX := paper/main.tex
PAPER_PDF := paper/main.pdf
REPORTS_DIR ?= reports
PAPER_GENERATED_DIR ?= paper/generated
PAPER_BUILD_DIR ?= paper/build
TEST_REPORT_DIR := reports/.test-output
TEST_GENERATED_DIR := paper/.test-generated
TEST_BUILD_DIR := paper/.test-build

.PHONY: report bridge paper paper-tables paper-check paper-pdf paper-freshness test clean

report:
	$(PYTHON) $(REPORT_BUILDER) --output-dir $(REPORTS_DIR)

bridge: report
	$(PYTHON) $(BRIDGE_BUILDER) --input-dir $(REPORTS_DIR) --output-dir $(REPORTS_DIR)
	$(PYTHON) $(ADAPTIVE_BRIDGE_BUILDER) --input-dir $(REPORTS_DIR) --output-dir $(REPORTS_DIR)

paper: paper-pdf paper-freshness
	@printf 'Paper source: $(PAPER_TEX)\n'
	@printf 'Paper PDF: $(PAPER_PDF)\n'
	@printf 'Portfolio report: reports/cumulative-government-portfolios.md\n'
	@printf 'Profile sensitivity: reports/profile-sensitivity.md\n'
	@printf 'Robustness report: reports/portfolio-robustness.md\n'
	@printf 'Minimax-regret report: reports/portfolio-minimax-regret.md\n'
	@printf 'Focused profile tradeoffs: reports/portfolio-profile-tradeoffs.md\n'
	@printf 'Fragile watchlist: reports/fragile-portfolio-watchlist.md\n'
	@printf 'Uncertainty tiers: reports/portfolio-uncertainty-tiers.md\n'
	@printf 'Pareto front: reports/pareto-front.md\n'
	@printf 'Epsilon Pareto front: reports/pareto-front-epsilon.md\n'
	@printf 'Uncertainty-aware Pareto front: reports/pareto-front-uncertainty.md\n'
	@printf 'Interbranch bridge: reports/interbranch-bridge-v0.md\n'
	@printf 'Bridge sensitivity: reports/interbranch-bridge-v0-sensitivity.md\n'
	@printf 'Bridge stability definitions: reports/interbranch-bridge-v0-stability-definitions.md\n'
	@printf 'Review source reconciliation: reports/review-source-reconciliation.md\n'
	@printf 'Review harmonization manifest: reports/review-harmonization-manifest.md\n'
	@printf 'Review variant sensitivity: reports/dual-review-sensitivity.md\n'
	@printf 'Review variant overlap: reports/review-variant-overlap.md\n'
	@printf 'Review variant rank shifts: reports/review-variant-rank-shifts.md\n'
	@printf 'Adaptive bridge: reports/adaptive-bridge-v1.md\n'
	@printf 'Adaptive bridge gate: reports/adaptive-bridge-v1-recommendation-gate.md\n'
	@printf 'Adaptive bridge calibration: reports/adaptive-bridge-v1-calibration.md\n'
	@printf 'Adaptive bridge coefficients: reports/adaptive-bridge-v1-coefficients.md\n'

paper-tables: bridge $(PAPER_TABLE_BUILDER)
	$(PYTHON) $(PAPER_TABLE_BUILDER) --reports-dir $(REPORTS_DIR) --output-dir $(PAPER_GENERATED_DIR)

paper-check: paper-tables $(PAPER_CLAIM_CHECKER)
	$(PYTHON) $(PAPER_CLAIM_CHECKER) --reports-dir $(REPORTS_DIR) --generated-dir $(PAPER_GENERATED_DIR) --paper-tex $(PAPER_TEX)

paper-pdf: paper-check $(PAPER_TEX)
	mkdir -p $(PAPER_BUILD_DIR)
	cd paper && $(LATEXMK) -g -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
	$(PYTHON) $(PAPER_LOG_CHECKER) $(PAPER_BUILD_DIR)/main.log
	cp $(PAPER_BUILD_DIR)/main.pdf $(PAPER_PDF)

paper-freshness:
	$(PYTHON) $(PAPER_FRESHNESS_CHECKER) --paper-pdf $(PAPER_PDF) --build-pdf $(PAPER_BUILD_DIR)/main.pdf --paper-tex $(PAPER_TEX) --generated-dir $(PAPER_GENERATED_DIR) --reports-dir $(REPORTS_DIR)

test:
	$(PYTHON) -m py_compile $(REPORT_BUILDER)
	$(PYTHON) -m py_compile $(BRIDGE_BUILDER)
	$(PYTHON) -m py_compile $(ADAPTIVE_BRIDGE_BUILDER)
	$(PYTHON) -m py_compile $(PAPER_TABLE_BUILDER)
	$(PYTHON) -m py_compile $(PAPER_CLAIM_CHECKER)
	$(PYTHON) -m py_compile $(PAPER_LOG_CHECKER)
	$(PYTHON) -m py_compile $(PAPER_FRESHNESS_CHECKER)
	rm -rf $(TEST_REPORT_DIR) $(TEST_GENERATED_DIR) $(TEST_BUILD_DIR)
	$(PYTHON) $(REPORT_BUILDER) --quiet --output-dir $(TEST_REPORT_DIR)
	$(PYTHON) $(BRIDGE_BUILDER) --quiet --input-dir $(TEST_REPORT_DIR) --output-dir $(TEST_REPORT_DIR)
	$(PYTHON) $(ADAPTIVE_BRIDGE_BUILDER) --quiet --input-dir $(TEST_REPORT_DIR) --output-dir $(TEST_REPORT_DIR)
	$(PYTHON) $(PAPER_TABLE_BUILDER) --reports-dir $(TEST_REPORT_DIR) --output-dir $(TEST_GENERATED_DIR)
	$(PYTHON) $(PAPER_CLAIM_CHECKER) --reports-dir $(TEST_REPORT_DIR) --generated-dir $(TEST_GENERATED_DIR) --paper-tex $(PAPER_TEX)
	mkdir -p $(TEST_BUILD_DIR)
	cd paper && $(LATEXMK) -g -pdf -interaction=nonstopmode -halt-on-error -outdir=.test-build test-main.tex
	$(PYTHON) $(PAPER_LOG_CHECKER) $(TEST_BUILD_DIR)/test-main.log
	rm -rf $(TEST_REPORT_DIR) $(TEST_GENERATED_DIR) $(TEST_BUILD_DIR)
	$(PYTHON) $(PAPER_FRESHNESS_CHECKER) --paper-pdf $(PAPER_PDF) --build-pdf $(PAPER_BUILD_DIR)/main.pdf --paper-tex $(PAPER_TEX) --generated-dir $(PAPER_GENERATED_DIR) --reports-dir $(REPORTS_DIR)

clean:
	rm -f reports/cumulative-government-portfolios.csv
	rm -f reports/cumulative-government-portfolios.md
	rm -f reports/component-scores.csv
	rm -f reports/pareto-front.csv
	rm -f reports/pareto-front.md
	rm -f reports/pareto-front-epsilon.csv
	rm -f reports/pareto-front-epsilon.md
	rm -f reports/pareto-front-uncertainty.csv
	rm -f reports/pareto-front-uncertainty.md
	rm -f reports/portfolio-robustness.csv
	rm -f reports/portfolio-robustness.md
	rm -f reports/portfolio-minimax-regret.csv
	rm -f reports/portfolio-minimax-regret.md
	rm -f reports/portfolio-profile-tradeoffs.csv
	rm -f reports/portfolio-profile-tradeoffs.md
	rm -f reports/fragile-portfolio-watchlist.csv
	rm -f reports/fragile-portfolio-watchlist.md
	rm -f reports/portfolio-uncertainty-tiers.csv
	rm -f reports/portfolio-uncertainty-tiers.md
	rm -f reports/speculative-modeling-agenda.md
	rm -f reports/review-source-reconciliation.csv
	rm -f reports/review-source-reconciliation.md
	rm -f reports/review-harmonization-manifest.csv
	rm -f reports/review-harmonization-manifest.md
	rm -f reports/harmonized-review-source.csv
	rm -f reports/dual-review-sensitivity.csv
	rm -f reports/dual-review-sensitivity.md
	rm -f reports/review-variant-overlap.csv
	rm -f reports/review-variant-overlap.md
	rm -f reports/review-variant-rank-shifts.csv
	rm -f reports/review-variant-rank-shifts.md
	rm -f reports/profile-sensitivity.csv
	rm -f reports/profile-sensitivity.md
	rm -f reports/interbranch-bridge-v0.csv
	rm -f reports/interbranch-bridge-v0.md
	rm -f reports/interbranch-bridge-v0-timeseries.csv
	rm -f reports/interbranch-bridge-v0-sensitivity.csv
	rm -f reports/interbranch-bridge-v0-sensitivity.md
	rm -f reports/interbranch-bridge-v0-sensitivity-timeseries.csv
	rm -f reports/interbranch-bridge-v0-stability.csv
	rm -f reports/interbranch-bridge-v0-stability-definitions.csv
	rm -f reports/interbranch-bridge-v0-stability-definitions.md
	rm -f reports/interbranch-bridge-v0-assumptions.json
	rm -f reports/adaptive-bridge-v1.csv
	rm -f reports/adaptive-bridge-v1-summary.csv
	rm -f reports/adaptive-bridge-v1.md
	rm -f reports/adaptive-bridge-v1-recommendation-gate.csv
	rm -f reports/adaptive-bridge-v1-recommendation-gate.md
	rm -f reports/adaptive-bridge-v1-calibration.md
	rm -f reports/adaptive-bridge-v1-coefficients.csv
	rm -f reports/adaptive-bridge-v1-coefficients.md
	rm -f reports/adaptive-bridge-v1-timeseries.csv
	rm -f reports/adaptive-bridge-v1-assumptions.json
	rm -f reports/source-inventory.json
	rm -rf $(TEST_REPORT_DIR)
	rm -f paper/main.aux
	rm -f paper/main.fdb_latexmk
	rm -f paper/main.fls
	rm -f paper/main.log
	rm -f paper/main.out
	rm -f paper/main.pdf
	rm -f paper/main.toc
	rm -rf paper/build
	rm -rf $(TEST_BUILD_DIR)
	rm -rf $(TEST_GENERATED_DIR)
	rm -rf paper/generated
	rm -rf scripts/__pycache__
	rm -rf paper/scripts/__pycache__
	rm -f paper/build/*\ 2.fls
