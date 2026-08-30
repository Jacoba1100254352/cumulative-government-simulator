#!/usr/bin/env python3
"""Build interbranch feedback bridge reports from focused portfolio cases."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DEFAULT_CONFIG = ROOT / "config" / "interbranch-bridge-v0.json"
BASELINE_PROFILE = "baseline"


@dataclass(frozen=True)
class SelectedCase:
    case_key: str
    case_label: str
    rationale: str
    legislature_key: str
    review_key: str
    anti_capture_key: str
    selector_source: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=REPORTS)
    parser.add_argument("--output-dir", type=Path, default=REPORTS)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--periods", type=int, help="Override configured period count.")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def resolved(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing bridge config: {path}")
    with path.open(encoding="utf-8") as handle:
        config = json.load(handle)
    if "coefficients" not in config:
        raise RuntimeError("Bridge config must define coefficients.")
    if "stressProfiles" not in config or BASELINE_PROFILE not in config["stressProfiles"]:
        raise RuntimeError("Bridge config must define a baseline stress profile.")
    return config


def nested(config: dict[str, Any], path: str, default: float) -> float:
    current: Any = config
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    if isinstance(current, (int, float)):
        return float(current)
    return default


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing input CSV: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def number(row: dict[str, str], key: str, default: float = 0.0) -> float:
    value = row.get(key)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def case_id(legislature_key: str, review_key: str, anti_capture_key: str) -> tuple[str, str, str]:
    return (legislature_key, review_key, anti_capture_key)


def portfolio_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], dict[str, str]]:
    lookup: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        lookup[case_id(row["legislatureKey"], row["reviewKey"], row["antiCaptureKey"])] = row
    return lookup


def first_profile_row(rows: list[dict[str, str]], profile: str) -> dict[str, str]:
    matches = [row for row in rows if row["profile"] == profile and row["profileRank"] == "1"]
    if not matches:
        raise RuntimeError(f"No rank-1 row found for profile {profile}")
    return matches[0]


def select_cases(input_dir: Path) -> tuple[list[SelectedCase], dict[tuple[str, str, str], dict[str, str]]]:
    portfolios = read_csv(input_dir / "cumulative-government-portfolios.csv")
    robustness = read_csv(input_dir / "portfolio-robustness.csv")
    regret = read_csv(input_dir / "portfolio-minimax-regret.csv")
    profiles = read_csv(input_dir / "profile-sensitivity.csv")
    lookup = portfolio_lookup(portfolios)

    balanced = portfolios[0]
    robust = robustness[0]
    minimax = regret[0]
    rights = first_profile_row(profiles, "rights-first")
    legitimacy = first_profile_row(profiles, "legitimacy-first")
    efficiency = first_profile_row(profiles, "efficiency-first")

    cases = [
        SelectedCase(
            case_key="balanced-winner",
            case_label="Balanced winner",
            rationale="Highest balanced portfolio score.",
            legislature_key=balanced["legislatureKey"],
            review_key=balanced["reviewKey"],
            anti_capture_key=balanced["antiCaptureKey"],
            selector_source="cumulative-government-portfolios.csv rank 1",
        ),
        SelectedCase(
            case_key="robustness-winner",
            case_label="Robustness winner",
            rationale="Highest cross-profile robustness score.",
            legislature_key=robust["legislatureKey"],
            review_key=robust["reviewKey"],
            anti_capture_key=robust["antiCaptureKey"],
            selector_source="portfolio-robustness.csv rank 1",
        ),
        SelectedCase(
            case_key="minimax-regret-winner",
            case_label="Minimax-regret winner",
            rationale="Lowest maximum regret across configured value profiles.",
            legislature_key=minimax["legislatureKey"],
            review_key=minimax["reviewKey"],
            anti_capture_key=minimax["antiCaptureKey"],
            selector_source="portfolio-minimax-regret.csv rank 1",
        ),
        SelectedCase(
            case_key="rights-capture-winner",
            case_label="Rights/capture winner",
            rationale="Highest rights-first profile row, which weights rights while preserving capture resistance.",
            legislature_key=rights["legislatureKey"],
            review_key=rights["reviewKey"],
            anti_capture_key=rights["antiCaptureKey"],
            selector_source="profile-sensitivity.csv rights-first rank 1",
        ),
        SelectedCase(
            case_key="legitimacy-winner",
            case_label="Legitimacy-first winner",
            rationale="Highest legitimacy-first profile row.",
            legislature_key=legitimacy["legislatureKey"],
            review_key=legitimacy["reviewKey"],
            anti_capture_key=legitimacy["antiCaptureKey"],
            selector_source="profile-sensitivity.csv legitimacy-first rank 1",
        ),
        SelectedCase(
            case_key="efficiency-caution",
            case_label="Efficiency caution case",
            rationale="Highest efficiency-first profile row, included as a stress case for weak-floor risks.",
            legislature_key=efficiency["legislatureKey"],
            review_key=efficiency["reviewKey"],
            anti_capture_key=efficiency["antiCaptureKey"],
            selector_source="profile-sensitivity.csv efficiency-first rank 1",
        ),
        SelectedCase(
            case_key="current-system-baseline",
            case_label="Current-system-ish baseline",
            rationale="Stylized current institutional package for comparison.",
            legislature_key="current-system",
            review_key="current-us-like",
            anti_capture_key="open-access-lobbying",
            selector_source="fixed baseline keys",
        ),
    ]

    missing = [case for case in cases if case_id(case.legislature_key, case.review_key, case.anti_capture_key) not in lookup]
    if missing:
        labels = ", ".join(case.case_label for case in missing)
        raise RuntimeError(f"Selected cases missing from portfolio CSV: {labels}")
    return cases, lookup


def modifier(stress: dict[str, Any], key: str, default: float) -> float:
    modifiers = stress.get("modifiers", {})
    value = modifiers.get(key, default) if isinstance(modifiers, dict) else default
    if isinstance(value, (int, float)):
        return float(value)
    return default


def adjusted_metric(portfolio: dict[str, str], column: str, stress: dict[str, Any], prefix: str) -> float:
    return clamp01(
        number(portfolio, column)
        * modifier(stress, f"{prefix}Multiplier", 1.0)
        + modifier(stress, f"{prefix}Add", 0.0)
    )


def weighted_average(values: dict[str, float], weights: dict[str, Any]) -> float:
    numerator = 0.0
    denominator = 0.0
    for key, weight in weights.items():
        if key not in values or not isinstance(weight, (int, float)):
            continue
        numerator += values[key] * float(weight)
        denominator += float(weight)
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def failure_modes(summary: dict[str, float], thresholds: dict[str, Any]) -> str:
    modes: list[str] = []
    checks = [
        ("baseResilienceFloor", "weakStartingFloor", "weak starting floor", "lt"),
        ("finalPolicyQuality", "lowPolicyQuality", "low policy quality", "lt"),
        ("finalPublicAlignment", "publicAlignmentErosion", "public alignment erosion", "lt"),
        ("finalCapturePressure", "captureDrift", "capture drift", "gte"),
        ("finalCorrectionBacklog", "uncorrectedRightsBacklog", "uncorrected rights backlog", "gte"),
        ("finalCourtCurbingPressure", "courtCurbingRisk", "court-curbing risk", "gte"),
        ("finalLegitimacy", "legitimacyErosion", "legitimacy erosion", "lt"),
        ("averageDelivery", "deliveryBottleneck", "delivery bottleneck", "lt"),
    ]
    for value_key, threshold_key, label, operator in checks:
        threshold = thresholds.get(threshold_key)
        if not isinstance(threshold, (int, float)):
            continue
        value = summary[value_key]
        if operator == "lt" and value < float(threshold):
            modes.append(label)
        if operator == "gte" and value >= float(threshold):
            modes.append(label)
    if not modes:
        modes.append("no dominant failure mode")
    return "; ".join(modes)


def simulate(
    case: SelectedCase,
    portfolio: dict[str, str],
    periods: int,
    config: dict[str, Any],
    stress_key: str,
    stress: dict[str, Any],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    coefficients = config["coefficients"]
    initial = coefficients["initialState"]

    base_delivery = adjusted_metric(portfolio, "policyDelivery", stress, "baseDelivery")
    base_alignment = adjusted_metric(portfolio, "publicAlignment", stress, "baseAlignment")
    base_rights = adjusted_metric(portfolio, "rightsSafeguard", stress, "baseRights")
    base_capture_resistance = adjusted_metric(portfolio, "captureResistance", stress, "baseCaptureResistance")
    base_legitimacy = adjusted_metric(portfolio, "legitimacy", stress, "baseLegitimacy")
    base_complexity = adjusted_metric(portfolio, "complexityScore", stress, "baseComplexity")
    base_floor = adjusted_metric(portfolio, "resilienceFloor", stress, "baseFloor")

    base_values = {
        "baseAlignment": base_alignment,
        "baseRights": base_rights,
        "baseCaptureResistance": base_capture_resistance,
        "baseLegitimacy": base_legitimacy,
        "baseComplexity": base_complexity,
    }
    policy_quality = clamp01(weighted_average(base_values, initial["policyQualityWeights"]))
    public_alignment_state = base_alignment
    capture_pressure = clamp01(
        (1.0 - base_capture_resistance)
        * nested(coefficients, "initialState.capturePressure.inverseCaptureResistanceWeight", 1.0)
        * modifier(stress, "initialCapturePressureMultiplier", 1.0)
        + modifier(stress, "initialCapturePressureAdd", 0.0)
    )
    correction_backlog = clamp01(
        (1.0 - base_rights) * nested(coefficients, "initialState.correctionBacklog.rightsGapWeight", 0.35)
        + (1.0 - base_alignment) * nested(coefficients, "initialState.correctionBacklog.alignmentGapWeight", 0.15)
        + modifier(stress, "initialCorrectionBacklogAdd", 0.0)
    )
    court_curbing_pressure = clamp01(modifier(stress, "initialCourtCurbingPressureAdd", 0.0))
    legitimacy_state = base_legitimacy
    compliance = clamp01(
        base_legitimacy * nested(coefficients, "initialState.compliance.legitimacyWeight", 0.45)
        + base_rights * nested(coefficients, "initialState.compliance.rightsWeight", 0.30)
        + base_complexity * nested(coefficients, "initialState.compliance.complexityWeight", 0.25)
        + modifier(stress, "initialComplianceAdd", 0.0)
    )

    total_delivery = 0.0
    total_useful_policy = 0.0
    total_bad_policy = 0.0
    total_docket = 0.0
    total_corrected = 0.0
    total_uncorrected = 0.0
    total_net_benefit = 0.0
    trace: list[dict[str, object]] = []

    for period in range(1, periods + 1):
        delivery = clamp01(
            base_delivery
            * (
                nested(coefficients, "delivery.legitimacyBase", 0.65)
                + nested(coefficients, "delivery.legitimacyWeight", 0.35) * legitimacy_state
            )
            * (
                nested(coefficients, "delivery.complexityBase", 0.82)
                + nested(coefficients, "delivery.complexityWeight", 0.18) * base_complexity
            )
            * modifier(stress, "deliveryMultiplier", 1.0)
            - capture_pressure
            * nested(coefficients, "delivery.capturePenalty", 0.05)
            * modifier(stress, "deliveryCapturePenaltyMultiplier", 1.0)
            - court_curbing_pressure
            * nested(coefficients, "delivery.courtCurbingPenalty", 0.04)
            * modifier(stress, "deliveryCourtCurbingPenaltyMultiplier", 1.0)
        )
        useful_policy = (
            delivery
            * (
                nested(coefficients, "usefulPolicy.publicAlignmentStateWeight", 0.45) * public_alignment_state
                + nested(coefficients, "usefulPolicy.baseAlignmentWeight", 0.25) * base_alignment
                + nested(coefficients, "usefulPolicy.captureControlWeight", 0.20) * (1.0 - capture_pressure)
                + nested(coefficients, "usefulPolicy.legitimacyWeight", 0.10) * legitimacy_state
            )
            * modifier(stress, "usefulPolicyMultiplier", 1.0)
        )
        bad_policy_inflow = (
            delivery
            * (
                nested(coefficients, "badPolicy.publicAlignmentGapWeight", 0.42) * (1.0 - public_alignment_state)
                + nested(coefficients, "badPolicy.capturePressureWeight", 0.30) * capture_pressure
                + nested(coefficients, "badPolicy.rightsGapWeight", 0.28) * (1.0 - base_rights)
            )
            * modifier(stress, "badPolicyMultiplier", 1.0)
        )
        rights_threat = (
            bad_policy_inflow
            * (
                nested(coefficients, "rightsThreat.base", 0.60)
                + nested(coefficients, "rightsThreat.rightsGapWeight", 0.40) * (1.0 - base_rights)
            )
            + court_curbing_pressure * nested(coefficients, "rightsThreat.courtCurbingWeight", 0.05)
        ) * modifier(stress, "rightsThreatMultiplier", 1.0)
        docket_pressure = clamp01(
            (
                rights_threat
                + correction_backlog * nested(coefficients, "reviewDocket.correctionBacklogWeight", 0.35)
                + capture_pressure * nested(coefficients, "reviewDocket.capturePressureWeight", 0.15)
            )
            * modifier(stress, "docketPressureMultiplier", 1.0)
            + modifier(stress, "docketPressureAdd", 0.0)
        )
        review_capacity = clamp01(
            base_rights
            * (
                nested(coefficients, "reviewCapacity.complexityBase", 0.55)
                + nested(coefficients, "reviewCapacity.complexityWeight", 0.45) * base_complexity
            )
            * (
                nested(coefficients, "reviewCapacity.legitimacyBase", 0.75)
                + nested(coefficients, "reviewCapacity.legitimacyWeight", 0.25) * legitimacy_state
            )
            * modifier(stress, "reviewCapacityMultiplier", 1.0)
            - court_curbing_pressure
            * nested(coefficients, "reviewCapacity.courtCurbingPenalty", 0.08)
            * modifier(stress, "reviewCurbingPenaltyMultiplier", 1.0)
        )
        corrected = min(
            docket_pressure,
            review_capacity
            * nested(coefficients, "correction.correctedShare", 0.45)
            * modifier(stress, "correctionShareMultiplier", 1.0),
        )
        uncorrected = max(0.0, docket_pressure - corrected)

        capture_growth = (
            delivery
            * (1.0 - base_capture_resistance)
            * nested(coefficients, "capture.growth.deliveryCaptureGapWeight", 0.18)
            + (1.0 - public_alignment_state)
            * nested(coefficients, "capture.growth.publicAlignmentGapWeight", 0.04)
            + (1.0 - base_complexity) * nested(coefficients, "capture.growth.complexityGapWeight", 0.03)
        ) * modifier(stress, "captureGrowthMultiplier", 1.0) + modifier(stress, "captureGrowthAdd", 0.0)
        capture_control = (
            base_capture_resistance
            * (
                nested(coefficients, "capture.control.base", 0.10)
                + nested(coefficients, "capture.control.legitimacyWeight", 0.10) * legitimacy_state
            )
            + corrected * nested(coefficients, "capture.control.correctedWeight", 0.04)
        ) * modifier(stress, "captureControlMultiplier", 1.0)
        capture_pressure = clamp01(capture_pressure + capture_growth - capture_control)

        correction_backlog = clamp01(
            correction_backlog * nested(coefficients, "backlog.retention", 0.72)
            + uncorrected
            * nested(coefficients, "backlog.uncorrectedWeight", 0.55)
            * modifier(stress, "uncorrectedBacklogMultiplier", 1.0)
            + bad_policy_inflow
            * nested(coefficients, "backlog.badPolicyWeight", 0.20)
            * modifier(stress, "badPolicyBacklogMultiplier", 1.0)
            - corrected
            * nested(coefficients, "backlog.correctedWeight", 0.20)
            * modifier(stress, "correctedBacklogMultiplier", 1.0)
        )
        court_curbing_growth = (
            max(
                0.0,
                corrected
                - ((legitimacy_state + base_alignment) / 2.0)
                * nested(coefficients, "courtCurbing.legitimacyAlignmentTolerance", 0.45),
            )
            * nested(coefficients, "courtCurbing.correctedExcessWeight", 0.16)
            + uncorrected * nested(coefficients, "courtCurbing.uncorrectedWeight", 0.04)
        ) * modifier(stress, "courtCurbingGrowthMultiplier", 1.0) + modifier(stress, "courtCurbingGrowthAdd", 0.0)
        court_curbing_decay = (
            base_rights * base_complexity * nested(coefficients, "courtCurbing.decay.rightsComplexityWeight", 0.05)
            + legitimacy_state * nested(coefficients, "courtCurbing.decay.legitimacyWeight", 0.03)
        ) * modifier(stress, "courtCurbingDecayMultiplier", 1.0)
        court_curbing_pressure = clamp01(court_curbing_pressure + court_curbing_growth - court_curbing_decay)

        compliance = clamp01(
            (
                nested(coefficients, "compliance.legitimacyWeight", 0.45) * legitimacy_state
                + nested(coefficients, "compliance.rightsWeight", 0.25) * base_rights
                + nested(coefficients, "compliance.complexityWeight", 0.20) * base_complexity
                + nested(coefficients, "compliance.courtCurbingControlWeight", 0.10)
                * (1.0 - court_curbing_pressure)
            )
            * modifier(stress, "complianceMultiplier", 1.0)
            + modifier(stress, "complianceAdd", 0.0)
        )
        policy_quality = clamp01(
            policy_quality * nested(coefficients, "policyQuality.retention", 0.82)
            + useful_policy
            * nested(coefficients, "policyQuality.usefulPolicyWeight", 0.18)
            * modifier(stress, "usefulPolicyQualityMultiplier", 1.0)
            + corrected * nested(coefficients, "policyQuality.correctedWeight", 0.08)
            - bad_policy_inflow
            * nested(coefficients, "policyQuality.badPolicyPenalty", 0.10)
            * modifier(stress, "badPolicyQualityPenaltyMultiplier", 1.0)
            - capture_pressure
            * nested(coefficients, "policyQuality.capturePenalty", 0.04)
            * modifier(stress, "captureQualityPenaltyMultiplier", 1.0)
        )
        public_alignment_state = clamp01(
            public_alignment_state * nested(coefficients, "publicAlignment.retention", 0.86)
            + base_alignment * nested(coefficients, "publicAlignment.baseAlignmentWeight", 0.08)
            + base_capture_resistance
            * nested(coefficients, "publicAlignment.captureResistanceWeight", 0.04)
            + corrected * nested(coefficients, "publicAlignment.correctedWeight", 0.03)
            - capture_pressure
            * nested(coefficients, "publicAlignment.capturePenalty", 0.07)
            * modifier(stress, "publicAlignmentCapturePenaltyMultiplier", 1.0)
            - uncorrected
            * nested(coefficients, "publicAlignment.uncorrectedPenalty", 0.04)
            * modifier(stress, "publicAlignmentUncorrectedPenaltyMultiplier", 1.0)
        )
        legitimacy_state = clamp01(
            legitimacy_state * nested(coefficients, "legitimacy.retention", 0.86)
            + base_legitimacy * nested(coefficients, "legitimacy.baseLegitimacyWeight", 0.08)
            + compliance * nested(coefficients, "legitimacy.complianceWeight", 0.05)
            + policy_quality * nested(coefficients, "legitimacy.policyQualityWeight", 0.04)
            - court_curbing_pressure
            * nested(coefficients, "legitimacy.courtCurbingPenalty", 0.06)
            * modifier(stress, "legitimacyCurbingPenaltyMultiplier", 1.0)
            - uncorrected
            * nested(coefficients, "legitimacy.uncorrectedPenalty", 0.05)
            * modifier(stress, "legitimacyUncorrectedPenaltyMultiplier", 1.0)
            - capture_pressure
            * nested(coefficients, "legitimacy.capturePenalty", 0.04)
            * modifier(stress, "legitimacyCapturePenaltyMultiplier", 1.0)
        )
        net_benefit = (
            useful_policy
            - bad_policy_inflow
            * nested(coefficients, "netBenefit.badPolicyPenalty", 0.45)
            * modifier(stress, "netBenefitBadPolicyPenaltyMultiplier", 1.0)
            - uncorrected
            * nested(coefficients, "netBenefit.uncorrectedPenalty", 0.25)
            * modifier(stress, "netBenefitUncorrectedPenaltyMultiplier", 1.0)
        )

        total_delivery += delivery
        total_useful_policy += useful_policy
        total_bad_policy += bad_policy_inflow
        total_docket += docket_pressure
        total_corrected += corrected
        total_uncorrected += uncorrected
        total_net_benefit += net_benefit

        trace.append(
            {
                "stressProfile": stress_key,
                "stressLabel": stress.get("label", stress_key),
                "caseKey": case.case_key,
                "period": period,
                "delivery": delivery,
                "usefulPolicy": useful_policy,
                "badPolicyInflow": bad_policy_inflow,
                "reviewDocketPressure": docket_pressure,
                "correctedPressure": corrected,
                "uncorrectedPressure": uncorrected,
                "policyQuality": policy_quality,
                "publicAlignmentState": public_alignment_state,
                "capturePressure": capture_pressure,
                "correctionBacklog": correction_backlog,
                "courtCurbingPressure": court_curbing_pressure,
                "legitimacyState": legitimacy_state,
                "compliance": compliance,
                "netPolicyBenefit": net_benefit,
            }
        )

    average_delivery = total_delivery / periods
    average_docket = total_docket / periods
    average_correction_rate = total_corrected / total_docket if total_docket else 0.0
    average_net_benefit = total_net_benefit / periods
    score_weights = coefficients["bridgeScore"]
    bridge_score = clamp01(
        policy_quality * score_weights["policyQuality"]
        + legitimacy_state * score_weights["legitimacy"]
        + (1.0 - capture_pressure) * score_weights["captureControl"]
        + (1.0 - correction_backlog) * score_weights["backlogControl"]
        + compliance * score_weights["compliance"]
        + average_delivery * score_weights["averageDelivery"]
        + (1.0 - court_curbing_pressure) * score_weights["courtCurbingControl"]
    )

    summary_values = {
        "bridgeScore": bridge_score,
        "averageDelivery": average_delivery,
        "averageReviewDocketPressure": average_docket,
        "averageCorrectionRate": average_correction_rate,
        "averageNetPolicyBenefit": average_net_benefit,
        "finalPolicyQuality": policy_quality,
        "finalPublicAlignment": public_alignment_state,
        "finalCapturePressure": capture_pressure,
        "finalCorrectionBacklog": correction_backlog,
        "finalCourtCurbingPressure": court_curbing_pressure,
        "finalLegitimacy": legitimacy_state,
        "finalCompliance": compliance,
        "cumulativeUsefulPolicy": total_useful_policy,
        "cumulativeBadPolicyInflow": total_bad_policy,
        "cumulativeUncorrectedPressure": total_uncorrected,
        "baseResilienceFloor": base_floor,
    }
    summary: dict[str, object] = {
        "stressProfile": stress_key,
        "stressLabel": stress.get("label", stress_key),
        "stressDescription": stress.get("description", ""),
        "caseKey": case.case_key,
        "caseLabel": case.case_label,
        "rationale": case.rationale,
        "selectorSource": case.selector_source,
        "legislatureKey": case.legislature_key,
        "legislature": portfolio["legislature"],
        "reviewKey": case.review_key,
        "review": portfolio["review"],
        "antiCaptureKey": case.anti_capture_key,
        "antiCapture": portfolio["antiCapture"],
        "balancedRank": portfolio["rank"],
        "balancedScore": number(portfolio, "overallScore"),
        **summary_values,
    }
    summary["failureModes"] = failure_modes(summary_values, config.get("thresholds", {}))
    return summary, trace


def rank_within_stress(summaries: list[dict[str, object]]) -> None:
    stress_keys = sorted({str(row["stressProfile"]) for row in summaries})
    for stress_key in stress_keys:
        ranked = sorted(
            [row for row in summaries if row["stressProfile"] == stress_key],
            key=lambda row: float(row["bridgeScore"]),
            reverse=True,
        )
        for rank, row in enumerate(ranked, start=1):
            row["bridgeRank"] = rank


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: fmt(row.get(key, "")) for key in fieldnames})


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return "\n".join(lines)


def write_baseline_markdown(path: Path, summaries: list[dict[str, object]], periods: int, config_path: Path) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    ranked = sorted(summaries, key=lambda row: int(row["bridgeRank"]))

    table = markdown_table(
        [
            "Bridge Rank",
            "Bridge Score",
            "Case",
            "Avg Delivery",
            "Final Quality",
            "Final Capture",
            "Final Backlog",
            "Final Legitimacy",
            "Failure Modes",
        ],
        [
            [
                row["bridgeRank"],
                row["bridgeScore"],
                row["caseLabel"],
                row["averageDelivery"],
                row["finalPolicyQuality"],
                row["finalCapturePressure"],
                row["finalCorrectionBacklog"],
                row["finalLegitimacy"],
                row["failureModes"],
            ]
            for row in ranked
        ],
    )
    detail_sections: list[str] = []
    for row in ranked:
        detail_sections.append(f"### {row['caseLabel']}")
        detail_sections.append(str(row["rationale"]))
        detail_sections.append("")
        detail_sections.append(
            markdown_table(
                ["Legislature", "Review", "Anti-capture", "Balanced Rank", "Selector"],
                [[row["legislature"], row["review"], row["antiCapture"], row["balancedRank"], row["selectorSource"]]],
            )
        )
        detail_sections.append("")

    text = f"""# Interbranch Bridge v0

Generated: `{generated_at}`

This deterministic bridge model runs `{periods}` periods for a focused set of portfolio cases. It converts static portfolio diagnostics into feedback loops among legislation, review, capture, correction, court-curbing pressure, compliance, and legitimacy. Coefficients and stress modifiers are externalized in `{config_path}`.

## Baseline Bridge Ranking

{table}

## Case Details

{chr(10).join(detail_sections)}

## Reading Notes

- `Bridge Score` is a feedback-adjusted score over final policy quality, legitimacy, capture control, correction backlog control, compliance, average delivery, and court-curbing control.
- `Final Capture` and `Final Backlog` are pressure values where lower is better.
- The baseline per-period trace is in `reports/interbranch-bridge-v0-timeseries.csv`.
- Stress sensitivity is in `reports/interbranch-bridge-v0-sensitivity.md`.
- The assumptions file is `reports/interbranch-bridge-v0-assumptions.json`.
"""
    path.write_text(text, encoding="utf-8")


def stability_rows(summaries: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    case_keys = sorted({str(row["caseKey"]) for row in summaries})
    best_score_by_stress: dict[str, float] = {}
    for stress_key in sorted({str(row["stressProfile"]) for row in summaries}):
        best_score_by_stress[stress_key] = max(
            float(row["bridgeScore"])
            for row in summaries
            if row["stressProfile"] == stress_key
        )
    for case_key in case_keys:
        case_rows = [row for row in summaries if row["caseKey"] == case_key]
        ranks = [int(row["bridgeRank"]) for row in case_rows]
        scores = [float(row["bridgeScore"]) for row in case_rows]
        regrets = [
            best_score_by_stress[str(row["stressProfile"])] - float(row["bridgeScore"])
            for row in case_rows
        ]
        wins = sum(1 for rank in ranks if rank == 1)
        top_two = sum(1 for rank in ranks if rank <= 2)
        rows.append(
            {
                "caseKey": case_key,
                "caseLabel": case_rows[0]["caseLabel"],
                "averageStressRank": sum(ranks) / len(ranks),
                "worstStressRank": max(ranks),
                "bestStressRank": min(ranks),
                "stressWins": wins,
                "topTwoStressCount": top_two,
                "averageBridgeScore": sum(scores) / len(scores),
                "scoreSpread": max(scores) - min(scores),
                "maxStressRegret": max(regrets),
                "averageStressRegret": sum(regrets) / len(regrets),
            }
        )

    def assign_rank(field: str, ordered_rows: list[dict[str, object]]) -> None:
        for rank, row in enumerate(ordered_rows, start=1):
            row[field] = rank

    assign_rank(
        "winTopTwoStabilityRank",
        sorted(
            rows,
            key=lambda row: (
                -int(row["stressWins"]),
                -int(row["topTwoStressCount"]),
                float(row["averageStressRank"]),
                -float(row["averageBridgeScore"]),
                float(row["maxStressRegret"]),
                float(row["scoreSpread"]),
            ),
        ),
    )
    assign_rank(
        "averageRankStabilityRank",
        sorted(
            rows,
            key=lambda row: (
                float(row["averageStressRank"]),
                int(row["worstStressRank"]),
                -int(row["stressWins"]),
                -float(row["averageBridgeScore"]),
            ),
        ),
    )
    assign_rank(
        "averageScoreStabilityRank",
        sorted(
            rows,
            key=lambda row: (
                -float(row["averageBridgeScore"]),
                float(row["maxStressRegret"]),
                float(row["averageStressRank"]),
            ),
        ),
    )
    assign_rank(
        "minimaxStressRegretRank",
        sorted(
            rows,
            key=lambda row: (
                float(row["maxStressRegret"]),
                float(row["averageStressRegret"]),
                float(row["averageStressRank"]),
                -float(row["averageBridgeScore"]),
            ),
        ),
    )
    assign_rank(
        "scoreSpreadStabilityRank",
        sorted(
            rows,
            key=lambda row: (
                float(row["scoreSpread"]),
                float(row["maxStressRegret"]),
                float(row["averageStressRank"]),
            ),
        ),
    )
    for row in rows:
        row["stressStabilityRank"] = row["winTopTwoStabilityRank"]
    rows.sort(
        key=lambda row: (
            int(row["winTopTwoStabilityRank"]),
            float(row["averageStressRank"]),
        )
    )
    return rows


def stability_definition_rows(stability: list[dict[str, object]]) -> list[dict[str, object]]:
    criteria = [
        (
            "win-top-two",
            "Wins/top-two rule",
            "Ranks cases by stress-profile wins, then top-two placements, then average stress rank.",
            "winTopTwoStabilityRank",
            lambda row: f"{int(row['stressWins'])} wins; {int(row['topTwoStressCount'])} top-two placements; average rank {float(row['averageStressRank']):.3f}",
        ),
        (
            "average-rank",
            "Best average stress rank",
            "Ranks cases by average rank across stress profiles, regardless of how wins are distributed.",
            "averageRankStabilityRank",
            lambda row: f"average rank {float(row['averageStressRank']):.3f}; worst rank {int(row['worstStressRank'])}",
        ),
        (
            "average-score",
            "Best average bridge score",
            "Ranks cases by mean bridge score across stress profiles.",
            "averageScoreStabilityRank",
            lambda row: f"average bridge score {float(row['averageBridgeScore']):.3f}",
        ),
        (
            "minimax-stress-regret",
            "Lowest maximum stress regret",
            "Ranks cases by the smallest worst gap from the winning score in any stress profile.",
            "minimaxStressRegretRank",
            lambda row: f"max stress regret {float(row['maxStressRegret']):.3f}; average regret {float(row['averageStressRegret']):.3f}",
        ),
        (
            "score-spread",
            "Smallest score spread",
            "Ranks cases by the smallest difference between best and worst stress-profile bridge score.",
            "scoreSpreadStabilityRank",
            lambda row: f"score spread {float(row['scoreSpread']):.3f}",
        ),
    ]
    rows = []
    for key, label, description, rank_field, summary in criteria:
        winner = min(stability, key=lambda row: int(row[rank_field]))
        rows.append(
            {
                "criterionKey": key,
                "criterionLabel": label,
                "description": description,
                "rankField": rank_field,
                "winnerCaseKey": winner["caseKey"],
                "winnerCaseLabel": winner["caseLabel"],
                "winnerMetricSummary": summary(winner),
            }
        )
    return rows


def write_sensitivity_markdown(
    path: Path,
    summaries: list[dict[str, object]],
    stability: list[dict[str, object]],
    stability_definitions: list[dict[str, object]],
    config_path: Path,
) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    stress_keys = sorted({str(row["stressProfile"]) for row in summaries})
    winners = []
    sections: list[str] = []
    for stress_key in stress_keys:
        rows = sorted(
            [row for row in summaries if row["stressProfile"] == stress_key],
            key=lambda row: int(row["bridgeRank"]),
        )
        winner = rows[0]
        winners.append(
            [
                winner["stressLabel"],
                winner["caseLabel"],
                winner["bridgeScore"],
                winner["finalPolicyQuality"],
                winner["finalLegitimacy"],
                winner["failureModes"],
            ]
        )
        sections.append(f"## {winner['stressLabel']}")
        sections.append(str(winner["stressDescription"]))
        sections.append("")
        sections.append(
            markdown_table(
                [
                    "Rank",
                    "Score",
                    "Case",
                    "Avg Delivery",
                    "Final Quality",
                    "Final Capture",
                    "Final Backlog",
                    "Final Legitimacy",
                    "Failure Modes",
                ],
                [
                    [
                        row["bridgeRank"],
                        row["bridgeScore"],
                        row["caseLabel"],
                        row["averageDelivery"],
                        row["finalPolicyQuality"],
                        row["finalCapturePressure"],
                        row["finalCorrectionBacklog"],
                        row["finalLegitimacy"],
                        row["failureModes"],
                    ]
                    for row in rows
                ],
            )
        )
        sections.append("")

    stability_table = markdown_table(
        [
            "Win/Top-2 Rank",
            "Case",
            "Avg Rank",
            "Worst Rank",
            "Wins",
            "Top-2 Profiles",
            "Avg Score",
            "Max Regret",
            "Score Spread",
        ],
        [
            [
                row["winTopTwoStabilityRank"],
                row["caseLabel"],
                row["averageStressRank"],
                row["worstStressRank"],
                row["stressWins"],
                row["topTwoStressCount"],
                row["averageBridgeScore"],
                row["maxStressRegret"],
                row["scoreSpread"],
            ]
            for row in stability
        ],
    )
    stability_definition_table = markdown_table(
        ["Criterion", "Winner", "Winner Metric", "Interpretation"],
        [
            [
                row["criterionLabel"],
                row["winnerCaseLabel"],
                row["winnerMetricSummary"],
                row["description"],
            ]
            for row in stability_definitions
        ],
    )

    text = f"""# Interbranch Bridge v0 Sensitivity

Generated: `{generated_at}`

This report reruns the same focused bridge cases under every stress profile defined in `{config_path}`. The question is whether the baseline bridge winner remains stable when capture pressure, public trust, rights threat, emergency abuse, institutional noncompliance, administrative overload, or federalism/agency-capacity constraints become worse. It is not a full bridge run over every portfolio.

## Stress Winners

{markdown_table(["Stress Profile", "Winner", "Score", "Final Quality", "Final Legitimacy", "Winner Failure Modes"], winners)}

## Cross-Stress Stability

The table below is sorted by the wins/top-two rule. The criterion-winner table shows how the conclusion changes under other defensible stability definitions.

{stability_table}

## Stability Criterion Winners

{stability_definition_table}

{chr(10).join(sections)}
"""
    path.write_text(text, encoding="utf-8")


def write_stability_definitions_markdown(path: Path, rows: list[dict[str, object]], config_path: Path) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    text = f"""# Interbranch Bridge v0 Stability Definitions

Generated: `{generated_at}`

These definitions are computed over the focused bridge case set in `{config_path}`. They are alternative summaries of the same stress-profile results, not separate empirical validations.

{markdown_table(
    ["Criterion", "Winner", "Winner Metric", "Interpretation"],
    [
        [
            row["criterionLabel"],
            row["winnerCaseLabel"],
            row["winnerMetricSummary"],
            row["description"],
        ]
        for row in rows
    ],
)}
"""
    path.write_text(text, encoding="utf-8")


def write_assumptions(
    path: Path,
    config: dict[str, Any],
    config_path: Path,
    periods: int,
    baseline_summaries: list[dict[str, object]],
) -> None:
    payload = {
        **config,
        "configPath": str(config_path),
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "periods": periods,
        "cases": [
            {
                "caseKey": row["caseKey"],
                "caseLabel": row["caseLabel"],
                "legislatureKey": row["legislatureKey"],
                "reviewKey": row["reviewKey"],
                "antiCaptureKey": row["antiCaptureKey"],
                "selectorSource": row["selectorSource"],
            }
            for row in baseline_summaries
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_dir = resolved(args.input_dir)
    output_dir = resolved(args.output_dir)
    config_path = resolved(args.config)
    config = load_config(config_path)
    periods = args.periods or int(config.get("defaultPeriods", 24))
    output_dir.mkdir(parents=True, exist_ok=True)

    cases, lookup = select_cases(input_dir)
    all_summaries: list[dict[str, object]] = []
    all_traces: list[dict[str, object]] = []
    stress_profiles = config["stressProfiles"]
    for stress_key, stress in stress_profiles.items():
        for case in cases:
            portfolio = lookup[case_id(case.legislature_key, case.review_key, case.anti_capture_key)]
            summary, trace = simulate(case, portfolio, periods, config, stress_key, stress)
            all_summaries.append(summary)
            all_traces.extend(trace)

    rank_within_stress(all_summaries)
    baseline_summaries = [row for row in all_summaries if row["stressProfile"] == BASELINE_PROFILE]
    baseline_traces = [row for row in all_traces if row["stressProfile"] == BASELINE_PROFILE]
    baseline_summaries.sort(key=lambda row: int(row["bridgeRank"]))
    stability = stability_rows(all_summaries)
    stability_definitions = stability_definition_rows(stability)

    summary_fields = [
        "stressProfile",
        "stressLabel",
        "bridgeRank",
        "caseKey",
        "caseLabel",
        "rationale",
        "selectorSource",
        "bridgeScore",
        "balancedRank",
        "balancedScore",
        "averageDelivery",
        "averageReviewDocketPressure",
        "averageCorrectionRate",
        "averageNetPolicyBenefit",
        "finalPolicyQuality",
        "finalPublicAlignment",
        "finalCapturePressure",
        "finalCorrectionBacklog",
        "finalCourtCurbingPressure",
        "finalLegitimacy",
        "finalCompliance",
        "cumulativeUsefulPolicy",
        "cumulativeBadPolicyInflow",
        "cumulativeUncorrectedPressure",
        "baseResilienceFloor",
        "failureModes",
        "legislatureKey",
        "legislature",
        "reviewKey",
        "review",
        "antiCaptureKey",
        "antiCapture",
    ]
    trace_fields = [
        "stressProfile",
        "stressLabel",
        "caseKey",
        "period",
        "delivery",
        "usefulPolicy",
        "badPolicyInflow",
        "reviewDocketPressure",
        "correctedPressure",
        "uncorrectedPressure",
        "policyQuality",
        "publicAlignmentState",
        "capturePressure",
        "correctionBacklog",
        "courtCurbingPressure",
        "legitimacyState",
        "compliance",
        "netPolicyBenefit",
    ]
    stability_fields = [
        "stressStabilityRank",
        "winTopTwoStabilityRank",
        "averageRankStabilityRank",
        "averageScoreStabilityRank",
        "minimaxStressRegretRank",
        "scoreSpreadStabilityRank",
        "caseKey",
        "caseLabel",
        "averageStressRank",
        "worstStressRank",
        "bestStressRank",
        "stressWins",
        "topTwoStressCount",
        "averageBridgeScore",
        "scoreSpread",
        "maxStressRegret",
        "averageStressRegret",
    ]
    stability_definition_fields = [
        "criterionKey",
        "criterionLabel",
        "description",
        "rankField",
        "winnerCaseKey",
        "winnerCaseLabel",
        "winnerMetricSummary",
    ]

    write_csv(output_dir / "interbranch-bridge-v0.csv", baseline_summaries, summary_fields)
    write_csv(output_dir / "interbranch-bridge-v0-timeseries.csv", baseline_traces, trace_fields)
    write_csv(output_dir / "interbranch-bridge-v0-sensitivity.csv", all_summaries, summary_fields)
    write_csv(output_dir / "interbranch-bridge-v0-sensitivity-timeseries.csv", all_traces, trace_fields)
    write_csv(output_dir / "interbranch-bridge-v0-stability.csv", stability, stability_fields)
    write_csv(
        output_dir / "interbranch-bridge-v0-stability-definitions.csv",
        stability_definitions,
        stability_definition_fields,
    )
    write_baseline_markdown(output_dir / "interbranch-bridge-v0.md", baseline_summaries, periods, config_path)
    write_sensitivity_markdown(
        output_dir / "interbranch-bridge-v0-sensitivity.md",
        all_summaries,
        stability,
        stability_definitions,
        config_path,
    )
    write_stability_definitions_markdown(
        output_dir / "interbranch-bridge-v0-stability-definitions.md",
        stability_definitions,
        config_path,
    )
    write_assumptions(
        output_dir / "interbranch-bridge-v0-assumptions.json",
        config,
        config_path,
        periods,
        baseline_summaries,
    )

    if not args.quiet:
        best = baseline_summaries[0]
        stable = stability[0]
        print(f"Wrote interbranch bridge v0 for {len(baseline_summaries)} baseline cases to {output_dir}")
        print(f"Stress profiles: {len(stress_profiles)}")
        print(f"Best baseline bridge case: {best['caseLabel']} ({float(best['bridgeScore']):.3f})")
        print(
            "Wins/top-two stress-stability leader: "
            f"{stable['caseLabel']} (avg rank {float(stable['averageStressRank']):.3f})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
