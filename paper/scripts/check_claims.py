#!/usr/bin/env python3
"""Verify that the paper's generated claims match current report artifacts."""

from __future__ import annotations

import csv
import argparse
import json
import os
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(os.environ.get("REPORTS_DIR", ROOT / "reports"))
PAPER = ROOT / "paper"
GENERATED = Path(os.environ.get("PAPER_GENERATED_DIR", PAPER / "generated"))
PAPER_TEX = PAPER / "main.tex"


REQUIRED_FRAGMENTS = [
    "report-macros.tex",
    "source-summary-table.tex",
    "source-paper-crosswalk-table.tex",
    "review-source-reconciliation-table.tex",
    "review-harmonization-manifest-table.tex",
    "dual-review-sensitivity-table.tex",
    "review-variant-overlap-table.tex",
    "review-variant-rank-shift-table.tex",
    "balanced-result-table.tex",
    "profile-winners-table.tex",
    "robustness-result-table.tex",
    "uncertainty-resolution-table.tex",
    "pareto-summary-table.tex",
    "bridge-case-scope-table.tex",
    "bridge-ranking-table.tex",
    "stress-stability-table.tex",
    "stress-stability-definitions-table.tex",
    "figure-bridge-baseline.tex",
    "figure-stress-stability.tex",
    "figure-high-capture-exception.tex",
    "high-capture-stress-table.tex",
    "adaptive-bridge-v1-leaders-table.tex",
    "adaptive-bridge-v1-gate-table.tex",
    "adaptive-bridge-v1-stress-winners-table.tex",
    "adaptive-bridge-v1-mechanisms-table.tex",
    "adaptive-bridge-v1-calibration-table.tex",
    "adaptive-bridge-v1-coefficients-table.tex",
    "uncertainty-summary-table.tex",
    "candidate-synthesis-table.tex",
    "minimax-regret-table.tex",
    "profile-tradeoff-table.tex",
    "fragile-watchlist-table.tex",
    "speculative-agenda-table.tex",
    "source-provenance-table.tex",
    "diagnostic-formulas-table.tex",
    "profile-weights-table.tex",
    "bridge-score-weights-table.tex",
    "stress-modifiers-table.tex",
]

BANNED_MAIN_PHRASES = [
    "most defensible efficient government",
    "favors moderated portfolio designs",
    "objectively best",
    "most stress-stable case overall",
    "clearly most stable",
]


def read_csv(name: str) -> list[dict[str, str]]:
    with (REPORTS / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def ranked(rows: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: int(row[key]))


def rows_for(rows: list[dict[str, str]], **filters: str) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if all(row.get(field) == value for field, value in filters.items())
    ]


def portfolio(row: dict[str, str]) -> str:
    return f"{row['legislature']} + {row['review']} + {row['antiCapture']}"


def fmt_int(value: int | str) -> str:
    return f"{int(value):,}"


def fmt_float(value: str | float) -> str:
    return f"{float(value):.3f}"


def source_for_kind(inventory: dict, kind: str) -> dict:
    for source in inventory["sources"]:
        if source["kind"] == kind:
            return source
    raise AssertionError(f"Missing source kind: {kind}")


def fail(message: str) -> None:
    raise AssertionError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def parse_macros() -> dict[str, str]:
    path = GENERATED / "report-macros.tex"
    text = path.read_text(encoding="utf-8")
    return dict(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}", text))


def require_fragment_inputs() -> None:
    main_tex = PAPER_TEX.read_text(encoding="utf-8")
    for fragment in REQUIRED_FRAGMENTS:
        path = GENERATED / fragment
        require(path.exists(), f"Missing generated fragment: {path}")
        include_default = rf"\input{{generated/{fragment}}}"
        include_variable = rf"\input{{\GeneratedDir/{fragment}}}"
        require(
            include_default in main_tex or include_variable in main_tex,
            f"main.tex does not include {fragment}",
        )


def require_macro(macros: dict[str, str], name: str, expected: str) -> None:
    actual = macros.get(name)
    require(actual == expected, f"Macro {name} expected {expected!r}, found {actual!r}")


def require_no_banned_prose() -> None:
    text = PAPER_TEX.read_text(encoding="utf-8").lower()
    for phrase in BANNED_MAIN_PHRASES:
        require(phrase not in text, f"Overclaiming phrase remains in paper: {phrase!r}")


def require_source_paper_crosswalk() -> dict:
    path = GENERATED / "source-paper-crosswalk.json"
    require(path.exists(), f"Missing generated source-paper crosswalk JSON: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    sources = data.get("sources", [])
    expected_projects = {
        "Congress Institutional Simulator",
        "Supreme Court Simulator Design",
        "Constitutional Review Simulator",
        "Lobby Capture Simulator",
    }
    projects = {record.get("project") for record in sources}
    require(expected_projects <= projects, "Source-paper crosswalk lost one or more sibling projects")
    by_project = {record["project"]: record for record in sources}
    require(
        by_project["Constitutional Review Simulator"]["cumulativeUse"].startswith("Referenced review cross-check"),
        "Constitutional Review Simulator must remain a referenced cross-check until schema reconciliation",
    )
    for imported_project in [
        "Congress Institutional Simulator",
        "Supreme Court Simulator Design",
        "Lobby Capture Simulator",
    ]:
        report = by_project[imported_project].get("report", {})
        require(report.get("exists") is True, f"Missing report artifact for {imported_project}")
        require(int(report.get("rows", 0)) > 0, f"Report artifact for {imported_project} has no rows")
    companion_report = by_project["Constitutional Review Simulator"].get("report", {})
    require(companion_report.get("exists") is True, "Missing Constitutional Review Simulator cross-check report")
    require(int(companion_report.get("rows", 0)) > 0, "Constitutional Review Simulator cross-check report has no rows")
    return data


def require_unique_ranks(rows: list[dict[str, str]], rank_field: str, group_field: str | None = None) -> None:
    groups: dict[str, list[dict[str, str]]] = {}
    if group_field is None:
        groups["all"] = rows
    else:
        for row in rows:
            groups.setdefault(row[group_field], []).append(row)
    for group, group_rows in groups.items():
        ranks = sorted(int(row[rank_field]) for row in group_rows)
        require(ranks == list(range(1, len(group_rows) + 1)), f"{rank_field} values are not complete in {group}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=REPORTS)
    parser.add_argument("--generated-dir", type=Path, default=GENERATED)
    parser.add_argument("--paper-tex", type=Path, default=PAPER_TEX)
    return parser.parse_args()


def main() -> None:
    global REPORTS, GENERATED, PAPER_TEX
    args = parse_args()
    REPORTS = args.reports_dir
    GENERATED = args.generated_dir
    PAPER_TEX = args.paper_tex

    require_fragment_inputs()
    require_no_banned_prose()
    source_paper_crosswalk = require_source_paper_crosswalk()

    inventory = read_json("source-inventory.json")
    assumptions = read_json("interbranch-bridge-v0-assumptions.json")
    portfolios = read_csv("cumulative-government-portfolios.csv")
    uncertainty_rows = read_csv("portfolio-uncertainty-tiers.csv")
    profile_rows = read_csv("profile-sensitivity.csv")
    robustness_rows = read_csv("portfolio-robustness.csv")
    regret_rows = read_csv("portfolio-minimax-regret.csv")
    tradeoff_rows = read_csv("portfolio-profile-tradeoffs.csv")
    watchlist_rows = read_csv("fragile-portfolio-watchlist.csv")
    pareto_rows = read_csv("pareto-front.csv")
    epsilon_pareto_rows = read_csv("pareto-front-epsilon.csv")
    uncertainty_pareto_rows = read_csv("pareto-front-uncertainty.csv")
    review_reconciliation_rows = read_csv("review-source-reconciliation.csv")
    review_harmonization_rows = read_csv("review-harmonization-manifest.csv")
    dual_review_rows = read_csv("dual-review-sensitivity.csv")
    review_overlap_rows = read_csv("review-variant-overlap.csv")
    review_rank_shift_rows = read_csv("review-variant-rank-shifts.csv")
    bridge_rows = read_csv("interbranch-bridge-v0.csv")
    sensitivity_rows = read_csv("interbranch-bridge-v0-sensitivity.csv")
    stability_rows = read_csv("interbranch-bridge-v0-stability.csv")
    stability_definition_rows = read_csv("interbranch-bridge-v0-stability-definitions.csv")
    adaptive_rows = read_csv("adaptive-bridge-v1.csv")
    adaptive_summary_rows = read_csv("adaptive-bridge-v1-summary.csv")
    adaptive_coefficient_rows = read_csv("adaptive-bridge-v1-coefficients.csv")
    adaptive_assumptions = read_json("adaptive-bridge-v1-assumptions.json")

    macros = parse_macros()
    legislature = source_for_kind(inventory, "legislature")
    review = source_for_kind(inventory, "review")
    anti_capture = source_for_kind(inventory, "anti_capture")

    require_macro(macros, "LegislativeRowCount", fmt_int(legislature["rows"]))
    require_macro(macros, "ReviewRowCount", fmt_int(review["rows"]))
    require_macro(macros, "AntiCaptureRowCount", fmt_int(anti_capture["rows"]))
    require_macro(macros, "SourcePaperCrosswalkCount", fmt_int(len(source_paper_crosswalk.get("sources", []))))
    reconciliation_counts = {
        category: sum(1 for row in review_reconciliation_rows if row["comparisonStatus"] == category)
        for category in [
            "shared configured metric",
            "imported-only configured metric",
            "companion-only configured metric",
            "companion adaptive candidate",
        ]
    }
    require(reconciliation_counts["shared configured metric"] > 0, "Review reconciliation lost shared configured metrics")
    require(reconciliation_counts["companion adaptive candidate"] > 0, "Review reconciliation lost companion adaptive candidates")
    require_macro(macros, "ReviewSharedConfiguredMetricCount", fmt_int(reconciliation_counts["shared configured metric"]))
    require_macro(macros, "ReviewImportedOnlyConfiguredMetricCount", fmt_int(reconciliation_counts["imported-only configured metric"]))
    require_macro(macros, "ReviewCompanionOnlyConfiguredMetricCount", fmt_int(reconciliation_counts["companion-only configured metric"]))
    require_macro(macros, "ReviewAdaptiveCandidateCount", fmt_int(reconciliation_counts["companion adaptive candidate"]))
    harmonized_included = {row["metricName"] for row in review_harmonization_rows if row["harmonizedAction"] == "included"}
    require(len(harmonized_included) > 0, "Review harmonization manifest has no included static metrics")
    require_macro(macros, "ReviewHarmonizedMetricCount", fmt_int(len(harmonized_included)))
    dual_by_key = {row["runKey"]: row for row in dual_review_rows}
    require("current-imported-review" in dual_by_key, "Dual-review sensitivity lost current imported review run")
    require("companion-review-first-pass" in dual_by_key, "Dual-review sensitivity lost companion review run")
    require("harmonized-review-source" in dual_by_key, "Review sensitivity lost harmonized source run")
    companion_review_run = dual_by_key["companion-review-first-pass"]
    require(companion_review_run["status"] == "completed", "Companion review sensitivity run did not complete")
    require(int(companion_review_run["portfolioCount"]) > 0, "Companion review sensitivity run has no portfolios")
    require_macro(macros, "DualReviewCompanionPortfolioCount", fmt_int(companion_review_run["portfolioCount"]))
    require_macro(macros, "DualReviewTopTwentyFiveOverlap", fmt_int(companion_review_run["top25OverlapWithPrimary"]))
    require_macro(macros, "DualReviewPrimaryWinnerRankInCompanion", companion_review_run["primaryWinnerRankInRun"])
    harmonized_review_run = dual_by_key["harmonized-review-source"]
    require(harmonized_review_run["status"] == "completed", "Harmonized review sensitivity run did not complete")
    require(int(harmonized_review_run["portfolioCount"]) > 0, "Harmonized review sensitivity run has no portfolios")
    require(int(harmonized_review_run["configuredMetricCount"]) == len(harmonized_included), "Harmonized metric count mismatch")
    require_macro(macros, "HarmonizedReviewPortfolioCount", fmt_int(harmonized_review_run["portfolioCount"]))
    require_macro(macros, "HarmonizedReviewTopTwentyFiveOverlap", fmt_int(harmonized_review_run["top25OverlapWithPrimary"]))
    require_macro(macros, "HarmonizedReviewPrimaryWinnerRank", harmonized_review_run["primaryWinnerRankInRun"])
    require_macro(macros, "HarmonizedReviewWinnerName", harmonized_review_run["balancedWinner"])
    require(len(review_overlap_rows) == 3, "Review variant pairwise overlap table should compare all three variant pairs")
    require(len(review_rank_shift_rows) >= 25, "Review variant rank-shift table lost top-25 union rows")
    current_harmonized_overlap = next(
        row
        for row in review_overlap_rows
        if row["leftRunKey"] == "current-imported-review" and row["rightRunKey"] == "harmonized-review-source"
    )
    require_macro(macros, "CurrentHarmonizedTopHundredOverlap", fmt_int(current_harmonized_overlap["top100Overlap"]))
    require_macro(macros, "ReviewVariantRankShiftRowCount", fmt_int(len(review_rank_shift_rows)))
    require_macro(macros, "PortfolioCount", fmt_int(len(portfolios)))
    require_macro(macros, "ParetoPortfolioCount", fmt_int(len(pareto_rows)))
    require_macro(macros, "EpsilonParetoPortfolioCount", fmt_int(len(epsilon_pareto_rows)))
    require_macro(macros, "UncertaintyParetoPortfolioCount", fmt_int(len(uncertainty_pareto_rows)))
    require_macro(macros, "BridgePeriodCount", fmt_int(assumptions["periods"]))
    baseline = ranked(rows_for(bridge_rows, stressProfile="baseline"), "bridgeRank")
    require_macro(macros, "BridgeCaseCount", fmt_int(len(baseline)))
    require_macro(macros, "BridgeUnmodeledPortfolioCount", fmt_int(len(portfolios) - len(baseline)))
    require_macro(macros, "StressProfileCount", fmt_int(len({row["stressProfile"] for row in sensitivity_rows})))
    require_macro(macros, "AdaptiveBridgePeriodCount", fmt_int(adaptive_assumptions["periods"]))
    require_macro(macros, "AdaptiveBridgePortfolioCount", fmt_int(len(adaptive_summary_rows)))
    require_macro(macros, "AdaptiveBridgeRunCount", fmt_int(len(adaptive_rows)))

    scenario_product = 1
    for source in inventory["sources"]:
        scenario_product *= int(source["scenarioCount"])
    require(
        scenario_product == len(portfolios),
        f"Portfolio count {len(portfolios)} does not match source scenario product {scenario_product}",
    )

    for source in inventory["sources"]:
        require(int(source["configuredMetricCount"]) == len(source["metricColumnsConfigured"]), f"Configured metric count mismatch for {source['kind']}")

    require_unique_ranks(portfolios, "rank")
    require_unique_ranks(adaptive_summary_rows, "adaptiveOverallRank")
    require_unique_ranks(adaptive_rows, "adaptiveRank", "stressProfile")
    require_unique_ranks(uncertainty_rows, "uncertaintyLowerBoundRank")
    require_unique_ranks(uncertainty_rows, "uncertaintyUpperBoundRank")
    require_unique_ranks(uncertainty_rows, "uncertaintyDominanceRank")
    require_unique_ranks(pareto_rows, "paretoRank")
    require_unique_ranks(epsilon_pareto_rows, "epsilonParetoRank")
    require_unique_ranks(uncertainty_pareto_rows, "uncertaintyParetoRank")
    require(
        len(epsilon_pareto_rows) <= len(pareto_rows) <= len(uncertainty_pareto_rows),
        "Pareto front sizes violate expected epsilon <= exact <= uncertainty-aware relationship",
    )

    balanced = ranked(portfolios, "rank")[0]
    require_macro(macros, "BalancedWinnerName", portfolio(balanced))
    require_macro(macros, "BalancedWinnerScore", fmt_float(balanced["overallScore"]))
    require_macro(macros, "BalancedWinnerUncertaintyLow", fmt_float(balanced["uncertaintyLow"]))
    require_macro(macros, "BalancedWinnerUncertaintyHigh", fmt_float(balanced["uncertaintyHigh"]))
    require_macro(macros, "BalancedWinnerUncertaintyBand", fmt_float(balanced["modelUncertaintyBand"]))
    require(float(balanced["modelUncertaintyBand"]) > 0.0, "Balanced uncertainty band is missing")
    balanced_uncertainty = [row for row in uncertainty_rows if row["balancedRank"] == "1"][0]
    overlap_count = sum(1 for row in uncertainty_rows if row["balancedIntervalRelation"] == "overlaps-balanced")
    below_count = sum(1 for row in uncertainty_rows if row["balancedIntervalRelation"] == "below-balanced")
    above_count = sum(1 for row in uncertainty_rows if row["balancedIntervalRelation"] == "above-balanced")
    require_macro(macros, "BalancedUncertaintyOverlapCount", fmt_int(overlap_count))
    require_macro(macros, "BalancedUncertaintyBelowCount", fmt_int(below_count))
    require_macro(macros, "BalancedUncertaintyAboveCount", fmt_int(above_count))
    require_macro(macros, "BalancedUncertaintyLowerBoundRank", fmt_int(balanced_uncertainty["uncertaintyLowerBoundRank"]))
    lower_bound_leader = ranked(uncertainty_rows, "uncertaintyLowerBoundRank")[0]
    require_macro(macros, "UncertaintyLowerBoundWinnerName", portfolio(lower_bound_leader))
    require_macro(macros, "UncertaintyLowerBoundWinnerBalancedRank", fmt_int(lower_bound_leader["balancedRank"]))

    robust = ranked(robustness_rows, "robustRank")[0]
    require_unique_ranks(robustness_rows, "robustRank")
    require_macro(macros, "RobustWinnerName", portfolio(robust))
    require_macro(macros, "RobustWinnerScore", fmt_float(robust["robustScore"]))
    require_macro(macros, "RobustWinnerBalancedRank", fmt_int(robust["rank"]))
    adaptive_by_key = {
        "|".join([row["legislatureKey"], row["reviewKey"], row["antiCaptureKey"]]): row
        for row in adaptive_summary_rows
    }
    adaptive_leader = ranked(adaptive_summary_rows, "adaptiveOverallRank")[0]
    balanced_key = "|".join([balanced["legislatureKey"], balanced["reviewKey"], balanced["antiCaptureKey"]])
    robust_key = "|".join([robust["legislatureKey"], robust["reviewKey"], robust["antiCaptureKey"]])
    balanced_adaptive = adaptive_by_key[balanced_key]
    robust_adaptive = adaptive_by_key[robust_key]
    gate_counts = {
        gate: sum(1 for row in adaptive_summary_rows if row["recommendationGate"] == gate)
        for gate in [
            "provisional shortlist",
            "calibration gray zone, not recommendation",
            "review priority, not recommendation",
            "do not recommend yet",
        ]
    }
    require_macro(macros, "AdaptiveProvisionalShortlistCount", fmt_int(gate_counts["provisional shortlist"]))
    require_macro(macros, "AdaptiveCalibrationGrayZoneCount", fmt_int(gate_counts["calibration gray zone, not recommendation"]))
    require_macro(macros, "AdaptiveReviewPriorityCount", fmt_int(gate_counts["review priority, not recommendation"]))
    require_macro(macros, "AdaptiveDoNotRecommendCount", fmt_int(gate_counts["do not recommend yet"]))
    require_macro(macros, "AdaptiveLeaderName", adaptive_leader["portfolio"])
    require_macro(macros, "AdaptiveLeaderScore", fmt_float(adaptive_leader["avgAdaptiveScore"]))
    require_macro(macros, "AdaptiveLeaderWorstStressRank", fmt_int(adaptive_leader["worstAdaptiveRank"]))
    require_macro(macros, "AdaptiveLeaderMaxStressRegret", fmt_float(adaptive_leader["maxStressRegret"]))
    require_macro(macros, "AdaptiveLeaderGate", adaptive_leader["recommendationGate"])
    require_macro(macros, "BalancedAdaptiveRank", fmt_int(balanced_adaptive["adaptiveOverallRank"]))
    require_macro(macros, "BalancedAdaptiveScore", fmt_float(balanced_adaptive["avgAdaptiveScore"]))
    require_macro(macros, "BalancedAdaptiveWorstStressRank", fmt_int(balanced_adaptive["worstAdaptiveRank"]))
    require_macro(macros, "BalancedAdaptiveMaxStressRegret", fmt_float(balanced_adaptive["maxStressRegret"]))
    require_macro(macros, "BalancedAdaptiveGate", balanced_adaptive["recommendationGate"])
    require_macro(macros, "RobustAdaptiveRank", fmt_int(robust_adaptive["adaptiveOverallRank"]))
    require_macro(macros, "RobustAdaptiveScore", fmt_float(robust_adaptive["avgAdaptiveScore"]))
    require_macro(macros, "RobustAdaptiveWorstStressRank", fmt_int(robust_adaptive["worstAdaptiveRank"]))
    require_macro(macros, "RobustAdaptiveGate", robust_adaptive["recommendationGate"])
    require(
        set(adaptive_assumptions["stressProfiles"].keys()) == {row["stressProfile"] for row in adaptive_rows},
        "Adaptive bridge stress profiles do not match adaptive assumptions",
    )
    require(
        adaptive_assumptions.get("researchCalibration", {}).get("status") == "evidence-informed priors; not empirically fitted",
        "Adaptive bridge assumptions must preserve the evidence-informed/non-fitted calibration boundary",
    )
    require(
        len(adaptive_assumptions.get("researchCalibration", {}).get("priors", [])) >= 6,
        "Adaptive bridge research calibration notes lost expected priors",
    )
    coefficient_families = adaptive_assumptions.get("portfolioAdjustmentFamilies", [])
    require(len(coefficient_families) >= 10, "Adaptive bridge lost configured coefficient families")
    require(len(adaptive_coefficient_rows) == len(coefficient_families), "Adaptive coefficient report does not match assumptions")
    for stress_profile in {row["stressProfile"] for row in adaptive_rows}:
        winners = [
            row
            for row in adaptive_rows
            if row["stressProfile"] == stress_profile and row["adaptiveRank"] == "1"
        ]
        require(len(winners) == 1, f"Adaptive stress profile {stress_profile} does not have exactly one winner")

    require_unique_ranks(regret_rows, "minimaxRegretRank")
    minimax = ranked(regret_rows, "minimaxRegretRank")[0]
    require_macro(macros, "MinimaxWinnerName", portfolio(minimax))
    require_macro(macros, "MinimaxWinnerBalancedRank", fmt_int(minimax["balancedRank"]))
    require_macro(macros, "MinimaxWinnerMaxProfileRegret", fmt_float(minimax["maxProfileRegret"]))
    require(len(tradeoff_rows) >= 6, "Focused profile tradeoff table lost expected cases")
    require(len(watchlist_rows) > 0, "Do-not-recommend-yet watchlist is empty")
    require_macro(macros, "FragileWatchlistCount", fmt_int(len(watchlist_rows)))

    profile_winners = [row for row in profile_rows if row["profileRank"] == "1"]
    require(len(profile_winners) == len({row["profile"] for row in profile_rows}), "Missing profile winner rows")
    require_unique_ranks(profile_rows, "profileRank", "profile")

    require_unique_ranks(bridge_rows, "bridgeRank", "stressProfile")
    require_macro(macros, "BaselineBridgeWinnerName", baseline[0]["caseLabel"])
    require_macro(macros, "BaselineBridgeWinnerPortfolio", portfolio(baseline[0]))
    require_macro(macros, "BaselineBridgeWinnerScore", fmt_float(baseline[0]["bridgeScore"]))
    baseline_by_key = {row["caseKey"]: row for row in baseline}
    require("balanced-winner" in baseline_by_key, "Focused bridge set no longer includes balanced winner")
    require("efficiency-caution" in baseline_by_key, "Focused bridge set no longer includes efficiency caution case")
    require("current-system-baseline" in baseline_by_key, "Focused bridge set no longer includes current-system-ish baseline")
    require_macro(macros, "BalancedBridgeScore", fmt_float(baseline_by_key["balanced-winner"]["bridgeScore"]))

    high_capture = ranked(rows_for(sensitivity_rows, stressProfile="high-capture-pressure"), "bridgeRank")
    emergency_abuse = ranked(rows_for(sensitivity_rows, stressProfile="emergency-abuse-stress"), "bridgeRank")
    require_unique_ranks(sensitivity_rows, "bridgeRank", "stressProfile")
    configured_stresses = set(assumptions["stressProfiles"].keys())
    observed_stresses = {row["stressProfile"] for row in sensitivity_rows}
    require(configured_stresses == observed_stresses, "Sensitivity report stress profiles do not match bridge config")
    for stress_profile in observed_stresses:
        require(
            len([row for row in sensitivity_rows if row["stressProfile"] == stress_profile and row["bridgeRank"] == "1"]) == 1,
            f"Stress profile {stress_profile} does not have exactly one winner",
        )
    require_macro(macros, "HighCaptureWinnerName", high_capture[0]["caseLabel"])
    require_macro(macros, "HighCaptureWinnerPortfolio", portfolio(high_capture[0]))
    balanced_high_capture = [row for row in high_capture if row["caseKey"] == "balanced-winner"][0]
    require_macro(macros, "BalancedHighCaptureRank", balanced_high_capture["bridgeRank"])
    balanced_emergency_abuse = [row for row in emergency_abuse if row["caseKey"] == "balanced-winner"][0]
    require_macro(macros, "BalancedEmergencyAbuseRank", balanced_emergency_abuse["bridgeRank"])
    require_macro(macros, "EmergencyAbuseWinnerName", emergency_abuse[0]["caseLabel"])

    stability = ranked(stability_rows, "winTopTwoStabilityRank")
    for field in [
        "stressStabilityRank",
        "winTopTwoStabilityRank",
        "averageRankStabilityRank",
        "averageScoreStabilityRank",
        "minimaxStressRegretRank",
        "scoreSpreadStabilityRank",
    ]:
        require_unique_ranks(stability_rows, field)
    require(
        all(row["stressStabilityRank"] == row["winTopTwoStabilityRank"] for row in stability_rows),
        "stressStabilityRank must remain the backwards-compatible wins/top-two alias",
    )
    balanced_stability = [row for row in stability if row["caseKey"] == "balanced-winner"][0]
    require_macro(macros, "BalancedAverageStressRank", fmt_float(balanced_stability["averageStressRank"]))
    require_macro(macros, "BalancedWinTopTwoStabilityRank", fmt_int(balanced_stability["winTopTwoStabilityRank"]))
    require_macro(macros, "BalancedAverageRankStabilityRank", fmt_int(balanced_stability["averageRankStabilityRank"]))
    require_macro(macros, "BalancedAverageScoreStabilityRank", fmt_int(balanced_stability["averageScoreStabilityRank"]))
    require_macro(macros, "BalancedMinimaxStressRegretRank", fmt_int(balanced_stability["minimaxStressRegretRank"]))
    criterion_macro_names = {
        "win-top-two": "WinTopTwoStressWinnerName",
        "average-rank": "AverageRankStressWinnerName",
        "average-score": "AverageScoreStressWinnerName",
        "minimax-stress-regret": "MinimaxStressRegretWinnerName",
        "score-spread": "ScoreSpreadStressWinnerName",
    }
    for row in stability_definition_rows:
        rank_field = row["rankField"]
        winner = min(stability_rows, key=lambda item: int(item[rank_field]))
        require(row["winnerCaseKey"] == winner["caseKey"], f"Stability definition {row['criterionKey']} has stale winner")
        macro_name = criterion_macro_names.get(row["criterionKey"])
        if macro_name:
            require_macro(macros, macro_name, row["winnerCaseLabel"])

    print("Paper claims verified against current report artifacts.")


if __name__ == "__main__":
    main()
