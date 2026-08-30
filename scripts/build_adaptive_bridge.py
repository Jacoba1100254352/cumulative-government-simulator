#!/usr/bin/env python3
"""Build adaptive all-portfolio bridge reports from cumulative portfolio rows."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = ROOT / "reports"
DEFAULT_OUTPUT_DIR = ROOT / "reports"
DEFAULT_V0_CONFIG = ROOT / "config" / "interbranch-bridge-v0.json"
DEFAULT_V1_CONFIG = ROOT / "config" / "adaptive-bridge-v1.json"


SUMMARY_FIELDS = [
    "stressProfile",
    "stressLabel",
    "adaptiveRank",
    "portfolioKey",
    "portfolio",
    "legislatureKey",
    "legislature",
    "reviewKey",
    "review",
    "antiCaptureKey",
    "antiCapture",
    "balancedRank",
    "balancedScore",
    "minimaxRegretRank",
    "maxProfileRegret",
    "modelUncertaintyBand",
    "resilienceFloor",
    "policyDelivery",
    "publicAlignment",
    "rightsSafeguard",
    "captureResistance",
    "legitimacy",
    "complexityScore",
    "evidenceStrength",
    "adaptiveScore",
    "averageDelivery",
    "averageUsefulPolicy",
    "averageHarmfulPolicy",
    "finalPolicyQuality",
    "finalPublicAlignment",
    "finalLegitimacy",
    "finalCapturePressure",
    "finalReviewBacklog",
    "finalCourtCurbingPressure",
    "finalPartyAdaptation",
    "finalCourtAdaptation",
    "finalLobbyAdaptation",
    "finalAgencyImplementationGap",
    "finalVoterFeedbackPressure",
    "finalCitizenAgendaCapacity",
    "sequencingReadiness",
    "finalFederalismResistance",
    "finalDeliveryBottleneck",
    "finalRecoveryCapacity",
    "finalFeedbackCorrectionCapacity",
    "finalTransitionLoad",
    "survivalFailureModes",
]


AGGREGATE_FIELDS = [
    "adaptiveOverallRank",
    "portfolioKey",
    "portfolio",
    "avgAdaptiveScore",
    "bestAdaptiveScore",
    "worstAdaptiveScore",
    "bestAdaptiveRank",
    "worstAdaptiveRank",
    "averageAdaptiveRank",
    "adaptiveWins",
    "top25StressCount",
    "top100StressCount",
    "maxStressRegret",
    "averageStressRegret",
    "scoreSpread",
    "recommendationGate",
    "gateReasons",
    "evidenceStrength",
    "balancedRank",
    "balancedScore",
    "minimaxRegretRank",
    "maxProfileRegret",
    "modelUncertaintyBand",
    "resilienceFloor",
    "policyDelivery",
    "publicAlignment",
    "rightsSafeguard",
    "captureResistance",
    "legitimacy",
    "complexityScore",
    "averageSequencingReadiness",
    "averageFederalismResistance",
    "averageDeliveryBottleneck",
    "averageRecoveryCapacity",
    "averageFeedbackCorrectionCapacity",
    "legislatureKey",
    "legislature",
    "reviewKey",
    "review",
    "antiCaptureKey",
    "antiCapture",
]


TRACE_FIELDS = [
    "portfolioKey",
    "portfolio",
    "stressProfile",
    "stressLabel",
    "period",
    "delivery",
    "usefulPolicy",
    "harmfulPolicy",
    "policyQuality",
    "publicAlignmentState",
    "legitimacyState",
    "capturePressure",
    "reviewBacklog",
    "courtCurbingPressure",
    "partyAdaptationPressure",
    "courtAdaptationPressure",
    "lobbyAdaptationPressure",
    "agencyImplementationGap",
    "voterFeedbackPressure",
    "citizenAgendaCapacity",
    "sequencingReadiness",
    "federalismResistance",
    "deliveryBottleneck",
    "recoveryCapacity",
    "feedbackCorrectionCapacity",
    "transitionLoad",
]


GATE_FIELDS = [
    "adaptiveOverallRank",
    "portfolioKey",
    "portfolio",
    "recommendationGate",
    "gateReasons",
    "avgAdaptiveScore",
    "worstAdaptiveRank",
    "maxStressRegret",
    "modelUncertaintyBand",
    "maxProfileRegret",
    "resilienceFloor",
    "evidenceStrength",
    "balancedRank",
    "minimaxRegretRank",
]

COEFFICIENT_FIELDS = [
    "family",
    "evidenceTier",
    "sourceReports",
    "tokens",
    "additiveCoefficients",
    "multiplierCoefficients",
    "calibrationUse",
    "claimBoundary",
]

DEFAULT_PORTFOLIO_ADJUSTMENT_FAMILIES: list[dict[str, Any]] = [
    {
        "family": "audit-and-sanctions anti-capture",
        "tokens": ["audit-and-sanctions", "randomized-audit-sanctions", "full anti-capture bundle"],
        "add": {"captureControlBonus": 0.060, "transitionReadinessBonus": 0.025, "recoveryCapacityBonus": 0.020},
        "multiply": {"lobbyAdaptationMultiplier": 0.92},
    },
    {
        "family": "venue-shifting detection",
        "tokens": ["venue-shifting-detection", "machine-readable-meeting-logs"],
        "add": {"captureControlBonus": 0.050, "transitionReadinessBonus": 0.035, "feedbackCorrectionBonus": 0.020},
        "multiply": {"lobbyAdaptationMultiplier": 0.88},
    },
    {
        "family": "democracy vouchers",
        "tokens": ["democracy-vouchers", "democracy vouchers"],
        "add": {"agendaCapacityBonus": 0.040, "captureControlBonus": 0.020, "feedbackCorrectionBonus": 0.025},
        "multiply": {"lobbyAdaptationMultiplier": 0.98},
    },
    {
        "family": "budgeted disclosed lobbying",
        "tokens": ["budgeted-disclosed-lobbying", "budgeted disclosed lobbying", "hard-lobbying-budgets"],
        "add": {"captureControlBonus": 0.025, "capturePressureAdd": 0.012, "transitionReadinessBonus": 0.010},
        "multiply": {"lobbyAdaptationMultiplier": 0.98},
    },
    {
        "family": "intermediary and dark-money substitution",
        "tokens": ["intermediary-substitution", "dark-money", "revolving-door", "campaign-finance-dominant", "low-salience"],
        "add": {"capturePressureAdd": 0.050, "agendaOverloadAdd": 0.020},
        "multiply": {"lobbyAdaptationMultiplier": 1.12},
    },
    {
        "family": "emergency integrity",
        "tokens": [
            "emergency-integrity-package",
            "no emergency relief without merits review",
            "automatic-merits-follow-up",
            "mandatory-written-emergency-reasoning",
            "emergency-restraint-court",
            "recusal-and-emergency-reform",
        ],
        "add": {
            "emergencySafeguardBonus": 0.100,
            "reviewCapacityBonus": 0.050,
            "courtCurbingReduction": 0.045,
            "transitionReadinessBonus": 0.040,
            "recoveryCapacityBonus": 0.030,
        },
    },
    {
        "family": "jurisdiction and pre-enactment review",
        "tokens": ["jurisdiction-stripping-constraints", "constitutional-council", "pre-enactment"],
        "add": {
            "emergencySafeguardBonus": 0.040,
            "reviewCapacityBonus": 0.030,
            "courtCurbingReduction": 0.030,
            "transitionReadinessBonus": 0.030,
        },
    },
    {
        "family": "citizen assembly threshold",
        "tokens": ["citizen-assembly-threshold", "citizen assembly"],
        "add": {
            "agendaCapacityBonus": 0.070,
            "agendaOverloadAdd": 0.025,
            "feedbackCorrectionBonus": 0.055,
            "transitionReadinessBonus": 0.020,
        },
        "multiply": {"partyAdaptationMultiplier": 0.96},
    },
    {
        "family": "random public review panel",
        "tokens": ["random-public-review-panel", "random public review panel"],
        "add": {"agendaCapacityBonus": 0.060, "rightsRiskAdd": -0.025, "feedbackCorrectionBonus": 0.050},
        "multiply": {"partyAdaptationMultiplier": 0.97},
    },
    {
        "family": "citizens agenda petition",
        "tokens": ["citizens-agenda-petition", "citizen agenda petition"],
        "add": {"agendaCapacityBonus": 0.060, "agendaOverloadAdd": 0.035, "feedbackCorrectionBonus": 0.035},
        "multiply": {"partyAdaptationMultiplier": 0.97},
    },
    {
        "family": "citizen initiative referendum",
        "tokens": ["citizen-initiative-referendum", "citizen initiative and referendum"],
        "add": {
            "agendaCapacityBonus": 0.080,
            "rightsRiskAdd": 0.045,
            "agendaOverloadAdd": 0.050,
            "capturePressureAdd": 0.020,
            "feedbackCorrectionBonus": 0.025,
        },
    },
    {
        "family": "authenticated public participation",
        "tokens": ["comment-authenticity-rules", "public-interest-representation", "public-advocate-office"],
        "add": {
            "agendaCapacityBonus": 0.035,
            "captureControlBonus": 0.030,
            "feedbackCorrectionBonus": 0.035,
            "transitionReadinessBonus": 0.020,
        },
    },
    {
        "family": "pairwise alternatives",
        "tokens": ["pairwise amendment", "pairwise alternatives"],
        "add": {"transitionLoadAdd": 0.035, "deliveryBottleneckAdd": 0.015, "feedbackCorrectionBonus": 0.025},
        "multiply": {"partyAdaptationMultiplier": 0.98},
    },
    {
        "family": "portfolio hybrid",
        "tokens": ["portfolio hybrid"],
        "add": {"transitionLoadAdd": 0.045, "deliveryBottleneckAdd": 0.020, "transitionReadinessBonus": -0.020},
    },
    {
        "family": "default pass",
        "tokens": ["default-pass"],
        "add": {"rightsRiskAdd": 0.060, "capturePressureAdd": 0.020, "partyAdaptationMultiplier": 0.020},
    },
]


@dataclass(frozen=True)
class PortfolioMetrics:
    key: str
    name: str
    legislature_key: str
    legislature: str
    review_key: str
    review: str
    anti_capture_key: str
    anti_capture: str
    balanced_rank: int
    balanced_score: float
    minimax_regret_rank: int
    max_profile_regret: float
    model_uncertainty_band: float
    resilience_floor: float
    policy_delivery: float
    public_alignment: float
    rights_safeguard: float
    capture_resistance: float
    legitimacy: float
    complexity_score: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--v0-config", type=Path, default=DEFAULT_V0_CONFIG)
    parser.add_argument("--v1-config", type=Path, default=DEFAULT_V1_CONFIG)
    parser.add_argument("--periods", type=int)
    parser.add_argument("--trace-limit", type=int, default=18)
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required report: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required config: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def number(row: dict[str, str], key: str, default: float = 0.0) -> float:
    raw = row.get(key, "")
    if raw == "":
        return default
    return float(raw)


def integer(row: dict[str, str], key: str, default: int = 0) -> int:
    raw = row.get(key, "")
    if raw == "":
        return default
    return int(raw)


def fmt(value: float) -> str:
    return f"{value:.3f}"


def portfolio_key(row: dict[str, str]) -> str:
    return "|".join([row["legislatureKey"], row["reviewKey"], row["antiCaptureKey"]])


def portfolio_name(row: dict[str, str]) -> str:
    return f"{row['legislature']} + {row['review']} + {row['antiCapture']}"


def portfolio_from_row(row: dict[str, str]) -> PortfolioMetrics:
    return PortfolioMetrics(
        key=portfolio_key(row),
        name=portfolio_name(row),
        legislature_key=row["legislatureKey"],
        legislature=row["legislature"],
        review_key=row["reviewKey"],
        review=row["review"],
        anti_capture_key=row["antiCaptureKey"],
        anti_capture=row["antiCapture"],
        balanced_rank=integer(row, "rank"),
        balanced_score=number(row, "overallScore"),
        minimax_regret_rank=integer(row, "minimaxRegretRank"),
        max_profile_regret=number(row, "maxProfileRegret"),
        model_uncertainty_band=number(row, "modelUncertaintyBand"),
        resilience_floor=number(row, "resilienceFloor"),
        policy_delivery=number(row, "policyDelivery"),
        public_alignment=number(row, "publicAlignment"),
        rights_safeguard=number(row, "rightsSafeguard"),
        capture_resistance=number(row, "captureResistance"),
        legitimacy=number(row, "legitimacy"),
        complexity_score=number(row, "complexityScore"),
    )


def modifier(stress: dict[str, Any], key: str, default: float = 1.0) -> float:
    return float(stress.get("modifiers", {}).get(key, default))


def adaptive_modifier(stress: dict[str, Any], key: str, default: float = 1.0) -> float:
    return float(stress.get(key, default))


def adjusted_metric(metric: float, stress: dict[str, Any], prefix: str) -> float:
    return clamp(metric * modifier(stress, f"{prefix}Multiplier", 1.0) + modifier(stress, f"{prefix}Add", 0.0))


def current_system_transition_discount(portfolio: PortfolioMetrics) -> float:
    if (
        portfolio.legislature_key == "current-system"
        and portfolio.review_key == "current-us-like"
        and portfolio.anti_capture_key == "open-access-lobbying"
    ):
        return 0.35
    return 1.0


def portfolio_text(portfolio: PortfolioMetrics) -> str:
    return " ".join(
        [
            portfolio.legislature_key,
            portfolio.review_key,
            portfolio.anti_capture_key,
            portfolio.legislature,
            portfolio.review,
            portfolio.anti_capture,
        ]
    ).lower()


def contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def evidence_strength(portfolio: PortfolioMetrics) -> str:
    text = portfolio_text(portfolio)
    low_direct = contains_any(
        text,
        [
            "pairwise amendment",
            "pairwise alternatives",
            "portfolio hybrid",
            "budgeted-disclosed-lobbying",
            "budgeted disclosed lobbying",
            "hard-lobbying-budgets",
            "hard lobbying budgets",
        ],
    )
    strong_direct = contains_any(
        text,
        [
            "audit-and-sanctions",
            "randomized-audit-sanctions",
            "democracy-vouchers",
            "democracy vouchers",
            "emergency-integrity-package",
            "no emergency relief without merits review",
            "mandatory-written-emergency-reasoning",
            "citizen-assembly",
            "random-public-review-panel",
            "comment-authenticity-rules",
        ],
    )
    if low_direct and strong_direct:
        return "mixed; low-direct-evidence family included"
    if low_direct:
        return "low direct evidence"
    if strong_direct:
        return "evidence-informed"
    return "synthetic extrapolation"


def portfolio_adjustments(
    portfolio: PortfolioMetrics,
    adjustment_families: list[dict[str, Any]] | None = None,
) -> dict[str, float | str]:
    text = portfolio_text(portfolio)
    adjustments: dict[str, float | str] = {
        "agendaCapacityBonus": 0.0,
        "agendaOverloadAdd": 0.0,
        "rightsRiskAdd": 0.0,
        "emergencySafeguardBonus": 0.0,
        "reviewCapacityBonus": 0.0,
        "courtCurbingReduction": 0.0,
        "lobbyAdaptationMultiplier": 1.0,
        "capturePressureAdd": 0.0,
        "captureControlBonus": 0.0,
        "transitionReadinessBonus": 0.0,
        "transitionLoadAdd": 0.0,
        "federalismResistanceAdd": 0.0,
        "deliveryBottleneckAdd": 0.0,
        "recoveryCapacityBonus": 0.0,
        "partyAdaptationMultiplier": 1.0,
        "feedbackCorrectionBonus": 0.0,
        "evidenceStrength": evidence_strength(portfolio),
    }

    def add(key: str, value: float) -> None:
        adjustments[key] = float(adjustments[key]) + value

    def multiply(key: str, value: float) -> None:
        adjustments[key] = float(adjustments[key]) * value

    for family in adjustment_families or DEFAULT_PORTFOLIO_ADJUSTMENT_FAMILIES:
        tokens = [str(token).lower() for token in family.get("tokens", [])]
        if not contains_any(text, tokens):
            continue
        for key, value in family.get("add", {}).items():
            add(str(key), float(value))
        for key, value in family.get("multiply", {}).items():
            multiply(str(key), float(value))

    for key in [
        "agendaCapacityBonus",
        "agendaOverloadAdd",
        "rightsRiskAdd",
        "emergencySafeguardBonus",
        "reviewCapacityBonus",
        "courtCurbingReduction",
        "capturePressureAdd",
        "captureControlBonus",
        "transitionReadinessBonus",
        "transitionLoadAdd",
        "federalismResistanceAdd",
        "deliveryBottleneckAdd",
        "recoveryCapacityBonus",
        "feedbackCorrectionBonus",
    ]:
        adjustments[key] = clamp(float(adjustments[key]), -0.12, 0.16)
    adjustments["lobbyAdaptationMultiplier"] = clamp(float(adjustments["lobbyAdaptationMultiplier"]), 0.78, 1.18)
    adjustments["partyAdaptationMultiplier"] = clamp(float(adjustments["partyAdaptationMultiplier"]), 0.88, 1.12)
    return adjustments


def agenda_capacity_bonus(portfolio: PortfolioMetrics) -> float:
    bonus = 0.0
    joined = " ".join(
        [
            portfolio.legislature_key,
            portfolio.review_key,
            portfolio.anti_capture_key,
            portfolio.legislature,
            portfolio.review,
            portfolio.anti_capture,
        ]
    ).lower()
    for token in ["agenda", "public", "democracy", "voucher", "pairwise", "portfolio", "mediation", "disclosed"]:
        if token in joined:
            bonus += 0.015
    if "open-access" in joined:
        bonus -= 0.02
    if "default-pass" in joined:
        bonus -= 0.025
    return clamp(bonus, -0.05, 0.08)


def sequencing_readiness(
    portfolio: PortfolioMetrics,
    base_floor: float,
    base_complexity: float,
    base_rights: float,
    base_capture_resistance: float,
    base_legitimacy: float,
    adjustments: dict[str, float | str],
) -> float:
    uncertainty_drag = 0.040 * min(portfolio.model_uncertainty_band / 0.12, 1.5)
    regret_drag = 0.030 * min(portfolio.max_profile_regret / 0.10, 1.5)
    raw = (
        0.18
        + 0.20 * base_complexity
        + 0.16 * base_floor
        + 0.16 * base_rights
        + 0.12 * base_capture_resistance
        + 0.10 * base_legitimacy
        + float(adjustments["transitionReadinessBonus"])
        - uncertainty_drag
        - regret_drag
    )
    return clamp(raw)


def initial_transition_load(
    portfolio: PortfolioMetrics,
    base_floor: float,
    base_complexity: float,
    stress: dict[str, Any],
) -> float:
    uncertainty_pressure = min(portfolio.model_uncertainty_band / 0.12, 1.5)
    regret_pressure = min(portfolio.max_profile_regret / 0.10, 1.5)
    raw = (
        0.09
        + 0.18 * (1.0 - base_floor)
        + 0.16 * (1.0 - base_complexity)
        + 0.10 * uncertainty_pressure
        + 0.08 * regret_pressure
        + adaptive_modifier(stress, "transitionLoadAdd", 0.0)
    )
    return clamp(raw * current_system_transition_discount(portfolio))


def failure_modes(summary: dict[str, object]) -> list[str]:
    failures: list[str] = []
    if float(summary["finalPolicyQuality"]) < 0.38:
        failures.append("low-policy-quality")
    if float(summary["finalPublicAlignment"]) < 0.42:
        failures.append("public-alignment-erosion")
    if float(summary["finalLegitimacy"]) < 0.44:
        failures.append("legitimacy-erosion")
    if float(summary["finalCapturePressure"]) > 0.55:
        failures.append("capture-adaptation")
    if float(summary["finalReviewBacklog"]) > 0.55:
        failures.append("uncorrected-review-backlog")
    if float(summary["finalCourtCurbingPressure"]) > 0.46:
        failures.append("court-curbing-risk")
    if float(summary["finalPartyAdaptation"]) > 0.57:
        failures.append("party-obstruction")
    if float(summary["finalCourtAdaptation"]) > 0.56:
        failures.append("court-adaptation")
    if float(summary["finalLobbyAdaptation"]) > 0.57:
        failures.append("lobby-venue-shifting")
    if float(summary["finalAgencyImplementationGap"]) > 0.52:
        failures.append("agency-overload")
    if float(summary["finalVoterFeedbackPressure"]) > 0.54:
        failures.append("voter-backlash")
    if float(summary["finalFederalismResistance"]) > 0.55:
        failures.append("federalism-resistance")
    if float(summary["finalDeliveryBottleneck"]) > 0.58:
        failures.append("delivery-bottleneck")
    if float(summary["finalRecoveryCapacity"]) < 0.38:
        failures.append("weak-recovery-capacity")
    if float(summary["finalFeedbackCorrectionCapacity"]) < 0.38 and float(summary["finalVoterFeedbackPressure"]) > 0.46:
        failures.append("uncorrected-public-feedback")
    if float(summary["finalTransitionLoad"]) > 0.55:
        failures.append("transition-overload")
    return failures


def simulate(
    portfolio: PortfolioMetrics,
    periods: int,
    v0_stress_key: str,
    v0_stress: dict[str, Any],
    v1_stress: dict[str, Any],
    score_weights: dict[str, float],
    adjustment_families: list[dict[str, Any]] | None,
    keep_trace: bool,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    base_delivery = adjusted_metric(portfolio.policy_delivery, v0_stress, "baseDelivery")
    base_alignment = adjusted_metric(portfolio.public_alignment, v0_stress, "baseAlignment")
    base_rights = adjusted_metric(portfolio.rights_safeguard, v0_stress, "baseRights")
    base_capture_resistance = adjusted_metric(portfolio.capture_resistance, v0_stress, "baseCaptureResistance")
    base_legitimacy = adjusted_metric(portfolio.legitimacy, v0_stress, "baseLegitimacy")
    base_complexity = adjusted_metric(portfolio.complexity_score, v0_stress, "baseComplexity")
    base_floor = adjusted_metric(portfolio.resilience_floor, v0_stress, "baseFloor")
    adjustments = portfolio_adjustments(portfolio, adjustment_families)
    sequence_ready = sequencing_readiness(
        portfolio,
        base_floor,
        base_complexity,
        base_rights,
        base_capture_resistance,
        base_legitimacy,
        adjustments,
    )
    transition_load = clamp(
        initial_transition_load(portfolio, base_floor, base_complexity, v1_stress)
        * (1.0 - 0.24 * sequence_ready)
        + float(adjustments["transitionLoadAdd"])
    )
    emergency_safeguard = clamp(
        (0.28 * base_rights + float(adjustments["emergencySafeguardBonus"]))
        * adaptive_modifier(v1_stress, "emergencySafeguardMultiplier", 1.0)
    )
    agenda_overload = clamp(
        (float(adjustments["agendaOverloadAdd"]) + max(0.0, transition_load - 0.35) * 0.12)
        * adaptive_modifier(v1_stress, "agendaOverloadMultiplier", 1.0)
    )
    federalism_resistance = clamp(
        0.08
        + 0.16 * (1.0 - base_legitimacy)
        + 0.13 * (1.0 - base_alignment)
        + 0.10 * transition_load
        + 0.07 * (1.0 - base_complexity)
        + float(adjustments["federalismResistanceAdd"])
        + adaptive_modifier(v1_stress, "federalismResistanceAdd", 0.0)
        - 0.10 * sequence_ready
    )
    delivery_bottleneck = clamp(
        0.18
        + 0.30 * (1.0 - base_complexity)
        + 0.22 * transition_load
        + 0.18 * federalism_resistance
        + 0.10 * (1.0 - base_floor)
        + float(adjustments["deliveryBottleneckAdd"])
        + adaptive_modifier(v1_stress, "deliveryBottleneckAdd", 0.0)
        - 0.10 * sequence_ready
    )
    recovery_capacity = clamp(
        (
            0.18
            + 0.25 * base_complexity
            + 0.18 * base_legitimacy
            + 0.16 * base_rights
            + 0.13 * base_capture_resistance
            + 0.12 * sequence_ready
            + float(adjustments["recoveryCapacityBonus"])
        )
        * adaptive_modifier(v1_stress, "recoveryCapacityMultiplier", 1.0)
    )

    citizen_agenda_capacity = clamp(
        (0.34 * base_alignment)
        + (0.23 * base_legitimacy)
        + (0.18 * base_capture_resistance)
        + (0.13 * base_complexity)
        + (0.12 * base_floor)
        + agenda_capacity_bonus(portfolio)
        + float(adjustments["agendaCapacityBonus"])
        - agenda_overload
    )
    citizen_agenda_capacity = clamp(
        citizen_agenda_capacity * adaptive_modifier(v1_stress, "citizenAgendaMultiplier", 1.0)
    )
    feedback_correction_capacity = clamp(
        (
            0.22
            + 0.24 * citizen_agenda_capacity
            + 0.18 * base_legitimacy
            + 0.16 * base_alignment
            + 0.11 * base_complexity
            + 0.09 * base_capture_resistance
            + float(adjustments["feedbackCorrectionBonus"])
            - 0.12 * delivery_bottleneck
        )
        * adaptive_modifier(v1_stress, "publicFeedbackEfficacyMultiplier", 1.0)
    )

    policy_quality = clamp((base_alignment + base_rights + base_capture_resistance + base_floor) / 4.0)
    public_alignment_state = base_alignment
    legitimacy_state = clamp(base_legitimacy - 0.10 * transition_load)
    capture_pressure = clamp(
        0.48 * (1.0 - base_capture_resistance)
        + 0.14 * base_delivery
        + 0.10 * transition_load
        + float(adjustments["capturePressureAdd"])
        + modifier(v0_stress, "initialCapturePressureAdd", 0.0)
    )
    review_backlog = clamp(
        0.28 * (1.0 - base_rights)
        + 0.16 * (1.0 - base_alignment)
        + 0.12 * transition_load
        - 0.05 * emergency_safeguard
        + modifier(v0_stress, "initialCorrectionBacklogAdd", 0.0)
    )
    court_curbing_pressure = clamp(
        0.08 * (1.0 - base_legitimacy)
        + 0.08 * (1.0 - base_alignment)
        + 0.08 * transition_load
        - float(adjustments["courtCurbingReduction"])
        + modifier(v0_stress, "initialCourtCurbingPressureAdd", 0.0)
    )
    party_adaptation = clamp(
        (
            0.24 * (1.0 - base_alignment)
            + 0.18 * (1.0 - base_legitimacy)
            + 0.14 * transition_load
            + 0.10 * base_delivery
            + 0.08 * capture_pressure
        )
        * adaptive_modifier(v1_stress, "partyAdaptationMultiplier", 1.0)
        * float(adjustments["partyAdaptationMultiplier"])
    )
    court_adaptation = clamp(
        (
            0.28 * (1.0 - base_rights)
            + 0.16 * (1.0 - base_legitimacy)
            + 0.14 * review_backlog
            + 0.10 * transition_load
            - 0.06 * emergency_safeguard
        )
        * adaptive_modifier(v1_stress, "courtAdaptationMultiplier", 1.0)
    )
    lobby_adaptation = clamp(
        (
            0.34 * (1.0 - base_capture_resistance)
            + 0.15 * base_delivery
            + 0.11 * (1.0 - base_alignment)
            + 0.09 * transition_load
        )
        * adaptive_modifier(v1_stress, "lobbyAdaptationMultiplier", 1.0)
        * adaptive_modifier(v1_stress, "lobbyVenueShiftMultiplier", 1.0)
        * float(adjustments["lobbyAdaptationMultiplier"])
    )
    agency_gap = clamp(
        (
            0.34 * (1.0 - base_complexity)
            + 0.16 * transition_load
            + 0.12 * (1.0 - base_floor)
            + 0.06 * review_backlog
            + 0.10 * federalism_resistance
            + 0.10 * delivery_bottleneck
            - 0.06 * recovery_capacity
        )
        * adaptive_modifier(v1_stress, "agencyGapMultiplier", 1.0)
    )
    voter_feedback = clamp(
        (
            0.24 * (1.0 - base_legitimacy)
            + 0.23 * (1.0 - base_alignment)
            + 0.11 * transition_load
            + 0.09 * capture_pressure
        )
        * adaptive_modifier(v1_stress, "voterFeedbackMultiplier", 1.0)
    )

    delivery_values: list[float] = []
    useful_values: list[float] = []
    harmful_values: list[float] = []
    traces: list[dict[str, object]] = []

    for period in range(1, periods + 1):
        transition_decay = 1.0 - min(period / max(periods, 1), 1.0)
        live_transition = clamp(transition_load * (0.72 + 0.28 * transition_decay))
        delivery = clamp(
            base_delivery
            * (0.62 + 0.38 * legitimacy_state)
            * (0.72 + 0.28 * base_complexity)
            * (0.84 + 0.16 * recovery_capacity)
            * (1.0 - 0.18 * capture_pressure)
            * (1.0 - 0.15 * court_curbing_pressure)
            * (1.0 - 0.24 * agency_gap)
            * (1.0 - 0.18 * delivery_bottleneck)
            * modifier(v0_stress, "deliveryMultiplier", 1.0)
        )
        useful_policy = clamp(
            delivery
            * (
                0.34 * public_alignment_state
                + 0.18 * base_alignment
                + 0.16 * (1.0 - lobby_adaptation)
                + 0.13 * legitimacy_state
                + 0.11 * citizen_agenda_capacity
                + 0.08 * (1.0 - agency_gap)
            )
            * modifier(v0_stress, "usefulPolicyMultiplier", 1.0)
        )
        harmful_policy = clamp(
            delivery
            * (
                0.26 * (1.0 - public_alignment_state)
                + 0.22 * capture_pressure
                + 0.16 * (1.0 - base_rights)
                + 0.14 * lobby_adaptation
                + 0.10 * party_adaptation
                + 0.07 * live_transition
                + max(0.0, float(adjustments["rightsRiskAdd"]))
                + 0.05 * max(0.0, adaptive_modifier(v1_stress, "emergencyAbuseMultiplier", 1.0) - 1.0)
            )
            * modifier(v0_stress, "badPolicyMultiplier", 1.0)
        )
        rights_threat = clamp(
            (
                harmful_policy
                * (0.58 + 0.42 * (1.0 - base_rights))
                * (0.92 + 0.08 * court_curbing_pressure)
                * adaptive_modifier(v1_stress, "emergencyAbuseMultiplier", 1.0)
                * (1.0 - 0.24 * emergency_safeguard)
                + max(0.0, float(adjustments["rightsRiskAdd"])) * 0.035
            )
            * modifier(v0_stress, "rightsThreatMultiplier", 1.0)
        )
        docket_pressure = clamp(
            (rights_threat + 0.34 * review_backlog + 0.12 * court_adaptation + 0.08 * capture_pressure)
            * modifier(v0_stress, "docketPressureMultiplier", 1.0)
            + modifier(v0_stress, "docketPressureAdd", 0.0)
        )
        review_capacity = clamp(
            (
                base_rights
                * (0.58 + 0.42 * base_complexity)
                * (0.72 + 0.28 * legitimacy_state)
                * (0.88 + 0.12 * recovery_capacity)
                * (1.0 - 0.18 * court_curbing_pressure)
                * (1.0 - 0.16 * agency_gap)
                + float(adjustments["reviewCapacityBonus"])
                + 0.05 * emergency_safeguard
            )
            * modifier(v0_stress, "reviewCapacityMultiplier", 1.0)
        )
        corrected = min(docket_pressure, review_capacity * 0.42)
        uncorrected = clamp(docket_pressure - corrected)

        capture_growth = clamp(
            (
                0.13 * delivery * (1.0 - base_capture_resistance)
                + 0.12 * lobby_adaptation
                + 0.08 * (1.0 - public_alignment_state)
                + 0.04 * agency_gap
                + 0.03 * delivery_bottleneck
            )
            * modifier(v0_stress, "captureGrowthMultiplier", 1.0)
            + modifier(v0_stress, "captureGrowthAdd", 0.0)
        )
        capture_control = clamp(
            0.12 * base_capture_resistance
            + 0.07 * legitimacy_state
            + 0.04 * citizen_agenda_capacity
            + 0.03 * corrected
            + float(adjustments["captureControlBonus"])
        ) * modifier(v0_stress, "captureControlMultiplier", 1.0)
        capture_pressure = clamp(0.88 * capture_pressure + capture_growth - capture_control)

        court_curbing_growth = clamp(
            (
                0.09 * corrected * max(0.0, 0.50 - legitimacy_state)
                + 0.08 * party_adaptation
                + 0.06 * court_adaptation
                + 0.04 * uncorrected
                + 0.03 * federalism_resistance
                - 0.05 * emergency_safeguard
            )
            * modifier(v0_stress, "courtCurbingGrowthMultiplier", 1.0)
            + modifier(v0_stress, "courtCurbingGrowthAdd", 0.0)
        )
        court_curbing_decay = clamp(
            0.04 * base_rights
            + 0.03 * base_complexity
            + 0.03 * legitimacy_state
            + 0.02 * citizen_agenda_capacity
            + float(adjustments["courtCurbingReduction"])
        ) * modifier(v0_stress, "courtCurbingDecayMultiplier", 1.0)
        court_curbing_pressure = clamp(0.90 * court_curbing_pressure + court_curbing_growth - court_curbing_decay)

        review_backlog = clamp(
            0.74 * review_backlog
            + 0.54 * uncorrected * modifier(v0_stress, "uncorrectedBacklogMultiplier", 1.0)
            + 0.18 * harmful_policy * modifier(v0_stress, "badPolicyBacklogMultiplier", 1.0)
            + 0.05 * court_adaptation
            - 0.18 * corrected
            - 0.05 * emergency_safeguard
            - 0.03 * recovery_capacity
        )

        federalism_resistance = clamp(
            0.88 * federalism_resistance
            + 0.06 * party_adaptation
            + 0.05 * voter_feedback
            + 0.04 * delivery_bottleneck
            + 0.03 * (1.0 - legitimacy_state)
            - 0.05 * sequence_ready
            - 0.04 * recovery_capacity
        )
        recovery_capacity = clamp(
            0.90 * recovery_capacity
            + 0.04 * base_complexity
            + 0.04 * legitimacy_state
            + 0.03 * corrected
            + 0.02 * citizen_agenda_capacity
            - 0.05 * delivery_bottleneck
            - 0.03 * federalism_resistance
        )
        delivery_bottleneck = clamp(
            0.87 * delivery_bottleneck
            + 0.07 * federalism_resistance
            + 0.06 * live_transition
            + 0.05 * (1.0 - recovery_capacity)
            + 0.04 * agency_gap
            - 0.05 * base_complexity
            - 0.03 * sequence_ready
        )
        agency_gap = clamp(
            0.86 * agency_gap
            + 0.09 * live_transition
            + 0.07 * (1.0 - base_complexity)
            + 0.05 * harmful_policy
            + 0.04 * court_curbing_pressure
            + 0.06 * federalism_resistance
            + 0.06 * delivery_bottleneck
            - 0.05 * base_complexity
            - 0.03 * legitimacy_state
            - 0.02 * citizen_agenda_capacity
            - 0.04 * recovery_capacity
        )
        party_adaptation = clamp(
            0.88 * party_adaptation
            + 0.07 * (1.0 - public_alignment_state)
            + 0.05 * voter_feedback
            + 0.04 * capture_pressure
            + 0.03 * live_transition
            - 0.04 * legitimacy_state
            - 0.03 * citizen_agenda_capacity
        )
        court_adaptation = clamp(
            0.87 * court_adaptation
            + 0.07 * rights_threat
            + 0.05 * court_curbing_pressure
            + 0.04 * uncorrected
            - 0.04 * base_rights
            - 0.02 * legitimacy_state
        )
        lobby_adaptation = clamp(
            0.89 * lobby_adaptation
            + 0.08 * delivery * (1.0 - base_capture_resistance)
            + 0.05 * capture_pressure
            + 0.04 * agency_gap
            - 0.05 * base_capture_resistance
            - 0.03 * citizen_agenda_capacity
        )
        voter_feedback = clamp(
            0.86 * voter_feedback
            + 0.09 * (1.0 - policy_quality)
            + 0.07 * capture_pressure
            + 0.06 * uncorrected
            + 0.04 * live_transition
            + 0.03 * delivery_bottleneck
            - 0.06 * legitimacy_state
            - 0.04 * useful_policy
            - 0.05 * feedback_correction_capacity
        )
        feedback_correction_capacity = clamp(
            0.88 * feedback_correction_capacity
            + 0.05 * citizen_agenda_capacity
            + 0.04 * legitimacy_state
            + 0.03 * public_alignment_state
            + 0.03 * recovery_capacity
            - 0.05 * delivery_bottleneck
            - 0.04 * capture_pressure
        )
        citizen_agenda_capacity = clamp(
            0.92 * citizen_agenda_capacity
            + 0.04 * public_alignment_state
            + 0.03 * legitimacy_state
            + 0.02 * base_capture_resistance
            - 0.05 * party_adaptation
            - 0.04 * capture_pressure
            - 0.03 * agency_gap
            - 0.03 * agenda_overload
        )

        policy_quality = clamp(
            0.78 * policy_quality
            + 0.08 * ((base_alignment + base_rights + base_capture_resistance + base_floor) / 4.0)
            + 0.14 * useful_policy * modifier(v0_stress, "usefulPolicyQualityMultiplier", 1.0)
            + 0.07 * corrected
            + 0.03 * voter_feedback * feedback_correction_capacity
            - 0.08 * harmful_policy * modifier(v0_stress, "badPolicyQualityPenaltyMultiplier", 1.0)
            - 0.04 * capture_pressure * modifier(v0_stress, "captureQualityPenaltyMultiplier", 1.0)
            - 0.03 * agency_gap
        )
        public_alignment_state = clamp(
            0.84 * public_alignment_state
            + 0.10 * base_alignment
            + 0.04 * citizen_agenda_capacity
            + 0.03 * corrected
            + 0.04 * voter_feedback * feedback_correction_capacity
            - 0.055 * capture_pressure * modifier(v0_stress, "publicAlignmentCapturePenaltyMultiplier", 1.0)
            - 0.04 * uncorrected * modifier(v0_stress, "publicAlignmentUncorrectedPenaltyMultiplier", 1.0)
            - 0.03 * party_adaptation
            - 0.02 * agenda_overload
        )
        compliance = clamp(
            0.42 * legitimacy_state
            + 0.23 * base_rights
            + 0.18 * base_complexity
            + 0.10 * (1.0 - court_curbing_pressure)
            + 0.07 * citizen_agenda_capacity
            - 0.07 * federalism_resistance
            - 0.06 * delivery_bottleneck
        ) * modifier(v0_stress, "complianceMultiplier", 1.0)
        legitimacy_state = clamp(
            0.85 * legitimacy_state
            + 0.07 * base_legitimacy
            + 0.05 * compliance
            + 0.04 * policy_quality
            + 0.03 * citizen_agenda_capacity
            + 0.03 * voter_feedback * feedback_correction_capacity * adaptive_modifier(v1_stress, "trustRecoveryMultiplier", 1.0)
            - 0.06 * court_curbing_pressure * modifier(v0_stress, "legitimacyCurbingPenaltyMultiplier", 1.0) * adaptive_modifier(v1_stress, "legitimacyErosionMultiplier", 1.0)
            - 0.05 * uncorrected * modifier(v0_stress, "legitimacyUncorrectedPenaltyMultiplier", 1.0) * adaptive_modifier(v1_stress, "legitimacyErosionMultiplier", 1.0)
            - 0.04 * capture_pressure * modifier(v0_stress, "legitimacyCapturePenaltyMultiplier", 1.0) * adaptive_modifier(v1_stress, "legitimacyErosionMultiplier", 1.0)
            - 0.03 * voter_feedback * (1.0 - 0.45 * feedback_correction_capacity)
        )

        delivery_values.append(delivery)
        useful_values.append(useful_policy)
        harmful_values.append(harmful_policy)
        if keep_trace:
            traces.append(
                {
                    "portfolioKey": portfolio.key,
                    "portfolio": portfolio.name,
                    "stressProfile": v0_stress_key,
                    "stressLabel": v0_stress.get("label", v0_stress_key),
                    "period": period,
                    "delivery": fmt(delivery),
                    "usefulPolicy": fmt(useful_policy),
                    "harmfulPolicy": fmt(harmful_policy),
                    "policyQuality": fmt(policy_quality),
                    "publicAlignmentState": fmt(public_alignment_state),
                    "legitimacyState": fmt(legitimacy_state),
                    "capturePressure": fmt(capture_pressure),
                    "reviewBacklog": fmt(review_backlog),
                    "courtCurbingPressure": fmt(court_curbing_pressure),
                    "partyAdaptationPressure": fmt(party_adaptation),
                    "courtAdaptationPressure": fmt(court_adaptation),
                    "lobbyAdaptationPressure": fmt(lobby_adaptation),
                    "agencyImplementationGap": fmt(agency_gap),
                    "voterFeedbackPressure": fmt(voter_feedback),
                    "citizenAgendaCapacity": fmt(citizen_agenda_capacity),
                    "sequencingReadiness": fmt(sequence_ready),
                    "federalismResistance": fmt(federalism_resistance),
                    "deliveryBottleneck": fmt(delivery_bottleneck),
                    "recoveryCapacity": fmt(recovery_capacity),
                    "feedbackCorrectionCapacity": fmt(feedback_correction_capacity),
                    "transitionLoad": fmt(live_transition),
                }
            )

    average_delivery = sum(delivery_values) / len(delivery_values)
    average_useful = sum(useful_values) / len(useful_values)
    average_harmful = sum(harmful_values) / len(harmful_values)
    adaptation_pressure = (
        party_adaptation
        + court_adaptation
        + lobby_adaptation
        + voter_feedback
        + federalism_resistance
        + delivery_bottleneck
    ) / 6.0
    implementation_control = clamp(
        1.0
        - (
            0.54 * agency_gap
            + 0.20 * delivery_bottleneck
            + 0.16 * federalism_resistance
            + 0.10 * (1.0 - recovery_capacity)
        )
    )
    adaptive_score = clamp(
        score_weights["policyQuality"] * policy_quality
        + score_weights["legitimacy"] * legitimacy_state
        + score_weights["publicAlignment"] * public_alignment_state
        + score_weights["captureControl"] * (1.0 - capture_pressure)
        + score_weights["implementationControl"] * implementation_control
        + score_weights["courtCurbingControl"] * (1.0 - court_curbing_pressure)
        + score_weights["reviewBacklogControl"] * (1.0 - review_backlog)
        + score_weights["averageDelivery"] * average_delivery
        + score_weights["citizenAgendaCapacity"] * citizen_agenda_capacity
        + score_weights["adaptationControl"] * (1.0 - adaptation_pressure)
    )

    summary: dict[str, object] = {
        "stressProfile": v0_stress_key,
        "stressLabel": v0_stress.get("label", v0_stress_key),
        "adaptiveRank": 0,
        "portfolioKey": portfolio.key,
        "portfolio": portfolio.name,
        "legislatureKey": portfolio.legislature_key,
        "legislature": portfolio.legislature,
        "reviewKey": portfolio.review_key,
        "review": portfolio.review,
        "antiCaptureKey": portfolio.anti_capture_key,
        "antiCapture": portfolio.anti_capture,
        "balancedRank": portfolio.balanced_rank,
        "balancedScore": fmt(portfolio.balanced_score),
        "minimaxRegretRank": portfolio.minimax_regret_rank,
        "maxProfileRegret": fmt(portfolio.max_profile_regret),
        "modelUncertaintyBand": fmt(portfolio.model_uncertainty_band),
        "resilienceFloor": fmt(portfolio.resilience_floor),
        "policyDelivery": fmt(portfolio.policy_delivery),
        "publicAlignment": fmt(portfolio.public_alignment),
        "rightsSafeguard": fmt(portfolio.rights_safeguard),
        "captureResistance": fmt(portfolio.capture_resistance),
        "legitimacy": fmt(portfolio.legitimacy),
        "complexityScore": fmt(portfolio.complexity_score),
        "evidenceStrength": adjustments["evidenceStrength"],
        "adaptiveScore": fmt(adaptive_score),
        "averageDelivery": fmt(average_delivery),
        "averageUsefulPolicy": fmt(average_useful),
        "averageHarmfulPolicy": fmt(average_harmful),
        "finalPolicyQuality": fmt(policy_quality),
        "finalPublicAlignment": fmt(public_alignment_state),
        "finalLegitimacy": fmt(legitimacy_state),
        "finalCapturePressure": fmt(capture_pressure),
        "finalReviewBacklog": fmt(review_backlog),
        "finalCourtCurbingPressure": fmt(court_curbing_pressure),
        "finalPartyAdaptation": fmt(party_adaptation),
        "finalCourtAdaptation": fmt(court_adaptation),
        "finalLobbyAdaptation": fmt(lobby_adaptation),
        "finalAgencyImplementationGap": fmt(agency_gap),
        "finalVoterFeedbackPressure": fmt(voter_feedback),
        "finalCitizenAgendaCapacity": fmt(citizen_agenda_capacity),
        "sequencingReadiness": fmt(sequence_ready),
        "finalFederalismResistance": fmt(federalism_resistance),
        "finalDeliveryBottleneck": fmt(delivery_bottleneck),
        "finalRecoveryCapacity": fmt(recovery_capacity),
        "finalFeedbackCorrectionCapacity": fmt(feedback_correction_capacity),
        "finalTransitionLoad": fmt(transition_load),
        "survivalFailureModes": "",
    }
    summary["survivalFailureModes"] = "; ".join(failure_modes(summary)) or "none"
    return summary, traces


def rank_within_stress(rows: list[dict[str, object]]) -> None:
    stress_keys = sorted({str(row["stressProfile"]) for row in rows})
    for stress_key in stress_keys:
        group = [row for row in rows if row["stressProfile"] == stress_key]
        group.sort(
            key=lambda row: (
                -float(row["adaptiveScore"]),
                -float(row["resilienceFloor"]),
                float(row["modelUncertaintyBand"]),
                int(row["balancedRank"]),
                str(row["portfolioKey"]),
            )
        )
        for rank, row in enumerate(group, start=1):
            row["adaptiveRank"] = rank


def recommendation_gate(row: dict[str, object], thresholds: dict[str, float]) -> tuple[str, str]:
    reasons: list[str] = []
    if float(row["avgAdaptiveScore"]) < thresholds["shortlistMinimumAverageScore"]:
        reasons.append("average adaptive score below shortlist threshold")
    if int(row["worstAdaptiveRank"]) > int(thresholds["shortlistMaximumWorstStressRank"]):
        reasons.append("worst stress rank too low")
    if float(row["maxStressRegret"]) > thresholds["shortlistMaximumStressRegret"]:
        reasons.append("max adaptive stress regret too high")
    if float(row["modelUncertaintyBand"]) > thresholds["shortlistMaximumUncertaintyBand"]:
        reasons.append("synthetic uncertainty band too wide")
    if float(row["maxProfileRegret"]) > thresholds["shortlistMaximumProfileRegret"]:
        reasons.append("static value-profile regret too high")
    if float(row["resilienceFloor"]) < thresholds["shortlistMinimumResilienceFloor"]:
        reasons.append("resilience floor too low")
    evidence = str(row.get("evidenceStrength", "synthetic extrapolation")).lower()
    if "low direct" in evidence or "low-direct" in evidence:
        reasons.append("direct empirical evidence thin for at least one selected family")

    failure_count = int(row.get("_worstFailureCount", 0))
    if failure_count > int(thresholds["doNotRecommendMaximumFailureModes"]):
        reasons.append("too many adaptive failure modes in at least one stress")

    if not reasons:
        return "provisional shortlist", "passes current synthetic adaptive screen"

    portfolio_count = max(1, int(row.get("_portfolioCount", 1)))
    worst_rank_percentile = int(row["worstAdaptiveRank"]) / portfolio_count
    gray_zone = (
        float(row["avgAdaptiveScore"]) >= thresholds["calibrationGrayZoneMinimumAverageScore"]
        and float(row["maxStressRegret"]) <= thresholds["calibrationGrayZoneMaximumStressRegret"]
        and worst_rank_percentile <= thresholds["calibrationGrayZoneMaximumWorstStressPercentile"]
        and failure_count <= int(thresholds["calibrationGrayZoneMaximumFailureModes"])
    )
    if gray_zone:
        return "calibration gray zone, not recommendation", "; ".join(reasons)

    review_priority = (
        float(row["avgAdaptiveScore"]) >= thresholds["reviewPriorityMinimumAverageScore"]
        and int(row["worstAdaptiveRank"]) <= int(thresholds["reviewPriorityMaximumWorstStressRank"])
    )
    if review_priority:
        return "review priority, not recommendation", "; ".join(reasons)
    return "do not recommend yet", "; ".join(reasons)


def aggregate(rows: list[dict[str, object]], thresholds: dict[str, float]) -> list[dict[str, object]]:
    best_by_stress: dict[str, float] = {}
    for stress_key in sorted({str(row["stressProfile"]) for row in rows}):
        best_by_stress[stress_key] = max(
            float(row["adaptiveScore"]) for row in rows if row["stressProfile"] == stress_key
        )

    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["portfolioKey"])].append(row)

    aggregates: list[dict[str, object]] = []
    for portfolio_key, group in grouped.items():
        scores = [float(row["adaptiveScore"]) for row in group]
        ranks = [int(row["adaptiveRank"]) for row in group]
        regrets = [
            best_by_stress[str(row["stressProfile"])] - float(row["adaptiveScore"])
            for row in group
        ]
        sequencing = [float(row["sequencingReadiness"]) for row in group]
        federalism = [float(row["finalFederalismResistance"]) for row in group]
        bottlenecks = [float(row["finalDeliveryBottleneck"]) for row in group]
        recovery = [float(row["finalRecoveryCapacity"]) for row in group]
        feedback = [float(row["finalFeedbackCorrectionCapacity"]) for row in group]
        base = group[0]
        failure_counts = [
            0 if row["survivalFailureModes"] == "none" else len(str(row["survivalFailureModes"]).split("; "))
            for row in group
        ]
        aggregate_row: dict[str, object] = {
            "adaptiveOverallRank": 0,
            "portfolioKey": portfolio_key,
            "portfolio": base["portfolio"],
            "avgAdaptiveScore": fmt(sum(scores) / len(scores)),
            "bestAdaptiveScore": fmt(max(scores)),
            "worstAdaptiveScore": fmt(min(scores)),
            "bestAdaptiveRank": min(ranks),
            "worstAdaptiveRank": max(ranks),
            "averageAdaptiveRank": fmt(sum(ranks) / len(ranks)),
            "adaptiveWins": sum(1 for rank in ranks if rank == 1),
            "top25StressCount": sum(1 for rank in ranks if rank <= 25),
            "top100StressCount": sum(1 for rank in ranks if rank <= 100),
            "maxStressRegret": fmt(max(regrets)),
            "averageStressRegret": fmt(sum(regrets) / len(regrets)),
            "scoreSpread": fmt(max(scores) - min(scores)),
            "recommendationGate": "",
            "gateReasons": "",
            "evidenceStrength": base["evidenceStrength"],
            "balancedRank": base["balancedRank"],
            "balancedScore": base["balancedScore"],
            "minimaxRegretRank": base["minimaxRegretRank"],
            "maxProfileRegret": base["maxProfileRegret"],
            "modelUncertaintyBand": base["modelUncertaintyBand"],
            "resilienceFloor": base["resilienceFloor"],
            "policyDelivery": base["policyDelivery"],
            "publicAlignment": base["publicAlignment"],
            "rightsSafeguard": base["rightsSafeguard"],
            "captureResistance": base["captureResistance"],
            "legitimacy": base["legitimacy"],
            "complexityScore": base["complexityScore"],
            "averageSequencingReadiness": fmt(sum(sequencing) / len(sequencing)),
            "averageFederalismResistance": fmt(sum(federalism) / len(federalism)),
            "averageDeliveryBottleneck": fmt(sum(bottlenecks) / len(bottlenecks)),
            "averageRecoveryCapacity": fmt(sum(recovery) / len(recovery)),
            "averageFeedbackCorrectionCapacity": fmt(sum(feedback) / len(feedback)),
            "legislatureKey": base["legislatureKey"],
            "legislature": base["legislature"],
            "reviewKey": base["reviewKey"],
            "review": base["review"],
            "antiCaptureKey": base["antiCaptureKey"],
            "antiCapture": base["antiCapture"],
            "_worstFailureCount": max(failure_counts),
            "_portfolioCount": len(grouped),
        }
        gate, reasons = recommendation_gate(aggregate_row, thresholds)
        aggregate_row["recommendationGate"] = gate
        aggregate_row["gateReasons"] = reasons
        aggregates.append(aggregate_row)

    aggregates.sort(
        key=lambda row: (
            -float(row["avgAdaptiveScore"]),
            float(row["maxStressRegret"]),
            int(row["worstAdaptiveRank"]),
            float(row["modelUncertaintyBand"]),
            int(row["balancedRank"]),
        )
    )
    for rank, row in enumerate(aggregates, start=1):
        row["adaptiveOverallRank"] = rank
        row.pop("_worstFailureCount", None)
        row.pop("_portfolioCount", None)
    return aggregates


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_summary_markdown(
    path: Path,
    aggregates: list[dict[str, object]],
    stress_rows: list[dict[str, object]],
    periods: int,
    v0_config_path: Path,
    v1_config_path: Path,
    v1_config: dict[str, Any],
) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    gate_counts: dict[str, int] = defaultdict(int)
    for row in aggregates:
        gate_counts[str(row["recommendationGate"])] += 1
    research = v1_config.get("researchCalibration", {})
    leaders = aggregates[:12]
    stress_winners = [
        sorted(
            [row for row in stress_rows if row["stressProfile"] == stress],
            key=lambda row: int(row["adaptiveRank"]),
        )[0]
        for stress in sorted({str(row["stressProfile"]) for row in stress_rows})
    ]
    body = f"""# Adaptive Bridge v1

Generated: `{generated_at}`

This synthetic bridge runs `{periods}` periods for every static portfolio under every configured v0 stress profile, then adds first-pass adaptive behavior by parties, courts, lobbyists, agencies, voters, federalism/capacity constraints, sequencing, emergency safeguards, and citizen agenda channels. It is an all-portfolio screening layer, not a calibrated causal estimate.

Calibration status: `{research.get("status", "synthetic; not empirically fitted")}`

V0 stress config: `{v0_config_path}`

V1 adaptive config: `{v1_config_path}`

## Gate counts

{markdown_table(["Gate", "Count"], [[key, value] for key, value in sorted(gate_counts.items())])}

## Adaptive overall leaders

{markdown_table(
        [
            "Rank",
            "Portfolio",
            "Avg score",
            "Worst rank",
            "Max regret",
            "Evidence",
            "Gate",
        ],
        [
            [
                row["adaptiveOverallRank"],
                row["portfolio"],
                row["avgAdaptiveScore"],
                row["worstAdaptiveRank"],
                row["maxStressRegret"],
                row["evidenceStrength"],
                row["recommendationGate"],
            ]
            for row in leaders
        ],
    )}

## Stress winners

{markdown_table(
        ["Stress profile", "Winner", "Score", "Balanced rank"],
        [
            [
                row["stressLabel"],
                row["portfolio"],
                row["adaptiveScore"],
                row["balancedRank"],
            ]
            for row in stress_winners
        ],
    )}

## Interpretation guardrails

- Empirical claim: the source reports support directional priors about venue shifting, emergency abuse, sequencing, federalism/capacity failure, public feedback, and citizen agenda design.
- Synthetic finding: the ranking shows which static portfolios survive the configured adaptive equations better than peers under those priors.
- Speculative design recommendation: gate status should be treated as a research triage signal until the adaptive coefficients are calibrated against historical or political-science evidence.
"""
    path.write_text(body, encoding="utf-8")


def write_gate_markdown(path: Path, aggregates: list[dict[str, object]]) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    flagged = [
        row
        for row in aggregates
        if str(row["recommendationGate"]) != "provisional shortlist"
    ][:20]
    body = f"""# Adaptive Bridge v1 Recommendation Gate

Generated: `{generated_at}`

This report separates synthetic adaptive screening from recommendation language. Portfolios outside the provisional shortlist should not be described as recommended institutional designs without additional calibration, historical validation, or mechanism-specific simulator work.

{markdown_table(
        [
            "Overall rank",
            "Portfolio",
            "Gate",
            "Evidence",
            "Reasons",
        ],
        [
            [
                row["adaptiveOverallRank"],
                row["portfolio"],
                row["recommendationGate"],
                row["evidenceStrength"],
                row["gateReasons"],
            ]
            for row in flagged
        ],
    )}
"""
    path.write_text(body, encoding="utf-8")


def compact_coefficients(values: dict[str, Any]) -> str:
    if not values:
        return ""
    return "; ".join(f"{key}={float(value):.3f}" for key, value in sorted(values.items()))


def coefficient_rows(v1_config: dict[str, Any]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in v1_config.get("portfolioAdjustmentFamilies", DEFAULT_PORTFOLIO_ADJUSTMENT_FAMILIES):
        rows.append(
            {
                "family": family.get("family", ""),
                "evidenceTier": family.get("evidenceTier", "synthetic prior"),
                "sourceReports": "; ".join(family.get("sourceReports", [])),
                "tokens": "; ".join(family.get("tokens", [])),
                "additiveCoefficients": compact_coefficients(family.get("add", {})),
                "multiplierCoefficients": compact_coefficients(family.get("multiply", {})),
                "calibrationUse": family.get("calibrationUse", ""),
                "claimBoundary": family.get("claimBoundary", "evidence-informed prior; not empirically fitted"),
            }
        )
    return rows


def write_coefficient_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    body = f"""# Adaptive Bridge v1 Coefficient Families

Generated: `{generated_at}`

These are mechanism-family coefficients loaded by `scripts/build_adaptive_bridge.py` from the v1 configuration. They are evidence-anchored priors, not fitted estimates.

{markdown_table(
        ["Family", "Evidence", "Additive coefficients", "Multiplier coefficients", "Boundary"],
        [
            [
                row["family"],
                row["evidenceTier"],
                row["additiveCoefficients"],
                row["multiplierCoefficients"],
                row["claimBoundary"],
            ]
            for row in rows
        ],
    )}
"""
    path.write_text(body, encoding="utf-8")


def write_calibration_markdown(path: Path, v1_config: dict[str, Any]) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    research = v1_config.get("researchCalibration", {})
    priors = research.get("priors", [])
    validation = research.get("validationRequirements", [])
    coefficients = coefficient_rows(v1_config)
    body = f"""# Adaptive Bridge v1 Research Calibration Notes

Generated: `{generated_at}`

Status: `{research.get("status", "synthetic; not empirically fitted")}`

{research.get("boundary", "The adaptive bridge remains a synthetic screening layer.")}

## Source reports

{markdown_table(["Report"], [[name] for name in research.get("sourceReports", [])])}

## Evidence-informed priors

{markdown_table(
        ["Area", "Empirical basis", "Model use"],
        [
            [
                prior.get("area", ""),
                prior.get("empiricalBasis", ""),
                prior.get("modelUse", ""),
            ]
            for prior in priors
        ],
    )}

## Validation requirements

{markdown_table(["Requirement"], [[item] for item in validation])}

## Configured coefficient families

{markdown_table(
        ["Family", "Evidence tier", "Use"],
        [
            [row["family"], row["evidenceTier"], row["calibrationUse"]]
            for row in coefficients
        ],
    )}

## Claim boundary

- Empirical claims belong to the named Deep Research reports and the imported simulator artifacts.
- Synthetic findings are produced by the configured bridge equations and generated CSVs.
- Speculative design recommendations remain research directions until weights, thresholds, and mechanism coefficients are calibrated.
"""
    path.write_text(body, encoding="utf-8")


def write_assumptions(
    path: Path,
    periods: int,
    v0_config_path: Path,
    v1_config_path: Path,
    v0_config: dict[str, Any],
    v1_config: dict[str, Any],
) -> None:
    data = {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "version": v1_config["version"],
        "periods": periods,
        "boundary": v1_config["boundary"],
        "v0StressConfigPath": str(v0_config_path),
        "v1AdaptiveConfigPath": str(v1_config_path),
        "modeledMechanisms": v1_config["modeledMechanisms"],
        "stateVariables": v1_config["stateVariables"],
        "scoreWeights": v1_config["scoreWeights"],
        "gateThresholds": v1_config["gateThresholds"],
        "researchCalibration": v1_config.get("researchCalibration", {}),
        "portfolioAdjustmentFamilies": v1_config.get("portfolioAdjustmentFamilies", DEFAULT_PORTFOLIO_ADJUSTMENT_FAMILIES),
        "stressProfiles": {
            key: {
                "label": value.get("label", key),
                "description": value.get("description", ""),
                "v0Modifiers": value.get("modifiers", {}),
                "v1AdaptiveModifiers": v1_config["stressModifiers"].get(key, {}),
            }
            for key, value in v0_config["stressProfiles"].items()
        },
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def select_trace_keys(aggregates: list[dict[str, object]], trace_limit: int) -> set[str]:
    selected = {str(row["portfolioKey"]) for row in aggregates[:trace_limit]}
    for row in aggregates:
        if int(row["balancedRank"]) == 1:
            selected.add(str(row["portfolioKey"]))
        if int(row["minimaxRegretRank"]) == 1:
            selected.add(str(row["portfolioKey"]))
        if row["legislatureKey"] == "current-system" and row["reviewKey"] == "current-us-like":
            selected.add(str(row["portfolioKey"]))
    return selected


def rerun_traces(
    portfolios: list[PortfolioMetrics],
    selected_keys: set[str],
    periods: int,
    v0_config: dict[str, Any],
    v1_config: dict[str, Any],
) -> list[dict[str, object]]:
    score_weights = {key: float(value) for key, value in v1_config["scoreWeights"].items()}
    adjustment_families = v1_config.get("portfolioAdjustmentFamilies", DEFAULT_PORTFOLIO_ADJUSTMENT_FAMILIES)
    by_key = {portfolio.key: portfolio for portfolio in portfolios}
    traces: list[dict[str, object]] = []
    for portfolio_key in sorted(selected_keys):
        portfolio = by_key[portfolio_key]
        for stress_key, stress in v0_config["stressProfiles"].items():
            _, trace = simulate(
                portfolio,
                periods,
                stress_key,
                stress,
                v1_config["stressModifiers"].get(stress_key, {}),
                score_weights,
                adjustment_families,
                keep_trace=True,
            )
            traces.extend(trace)
    return traces


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    portfolio_rows = read_csv(input_dir / "cumulative-government-portfolios.csv")
    portfolios = [portfolio_from_row(row) for row in portfolio_rows]
    v0_config = read_json(args.v0_config)
    v1_config = read_json(args.v1_config)
    periods = int(args.periods or v1_config.get("defaultPeriods") or v0_config.get("defaultPeriods") or 24)
    score_weights = {key: float(value) for key, value in v1_config["scoreWeights"].items()}
    adjustment_families = v1_config.get("portfolioAdjustmentFamilies", DEFAULT_PORTFOLIO_ADJUSTMENT_FAMILIES)

    missing_stresses = set(v0_config["stressProfiles"]) - set(v1_config["stressModifiers"])
    if missing_stresses:
        raise RuntimeError(f"Adaptive v1 config missing stress modifiers for: {sorted(missing_stresses)}")

    stress_rows: list[dict[str, object]] = []
    for stress_key, stress in v0_config["stressProfiles"].items():
        adaptive_stress = v1_config["stressModifiers"][stress_key]
        for portfolio in portfolios:
            summary, _trace = simulate(
                portfolio,
                periods,
                stress_key,
                stress,
                adaptive_stress,
                score_weights,
                adjustment_families,
                keep_trace=False,
            )
            stress_rows.append(summary)

    rank_within_stress(stress_rows)
    aggregates = aggregate(
        stress_rows,
        {key: float(value) for key, value in v1_config["gateThresholds"].items()},
    )
    trace_keys = select_trace_keys(aggregates, args.trace_limit)
    traces = rerun_traces(portfolios, trace_keys, periods, v0_config, v1_config)

    gate_rows = [{field: row[field] for field in GATE_FIELDS} for row in aggregates]
    configured_coefficients = coefficient_rows(v1_config)

    write_csv(output_dir / "adaptive-bridge-v1.csv", stress_rows, SUMMARY_FIELDS)
    write_csv(output_dir / "adaptive-bridge-v1-summary.csv", aggregates, AGGREGATE_FIELDS)
    write_csv(output_dir / "adaptive-bridge-v1-recommendation-gate.csv", gate_rows, GATE_FIELDS)
    write_csv(output_dir / "adaptive-bridge-v1-timeseries.csv", traces, TRACE_FIELDS)
    write_csv(output_dir / "adaptive-bridge-v1-coefficients.csv", configured_coefficients, COEFFICIENT_FIELDS)
    write_summary_markdown(
        output_dir / "adaptive-bridge-v1.md",
        aggregates,
        stress_rows,
        periods,
        args.v0_config,
        args.v1_config,
        v1_config,
    )
    write_gate_markdown(output_dir / "adaptive-bridge-v1-recommendation-gate.md", aggregates)
    write_calibration_markdown(output_dir / "adaptive-bridge-v1-calibration.md", v1_config)
    write_coefficient_markdown(output_dir / "adaptive-bridge-v1-coefficients.md", configured_coefficients)
    write_assumptions(
        output_dir / "adaptive-bridge-v1-assumptions.json",
        periods,
        args.v0_config,
        args.v1_config,
        v0_config,
        v1_config,
    )

    if not args.quiet:
        leader = aggregates[0]
        shortlist_count = sum(1 for row in aggregates if row["recommendationGate"] == "provisional shortlist")
        print(f"Wrote adaptive bridge v1 for {len(portfolios)} portfolios to {output_dir}")
        print(f"Stress profiles: {len(v0_config['stressProfiles'])}")
        print(
            "Adaptive leader: "
            f"{leader['portfolio']} (avg score {leader['avgAdaptiveScore']}, gate {leader['recommendationGate']})"
        )
        print(f"Provisional shortlist count: {shortlist_count}")


if __name__ == "__main__":
    main()
