#!/usr/bin/env python3
"""Build cumulative government portfolio reports from sibling simulator CSVs."""

from __future__ import annotations

import argparse
import csv
import json
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import product
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SIMULATORS = ROOT.parent


@dataclass(frozen=True)
class MetricSpec:
    column: str
    weight: float
    direction: str = "positive"


@dataclass
class SourceConfig:
    kind: str
    label: str
    path: Path
    key_column: str
    name_column: str
    metrics: list[MetricSpec]


@dataclass(frozen=True)
class ScoringProfile:
    slug: str
    label: str
    description: str
    weights: dict[str, float]


DIMENSION_KEYS = [
    "policyDelivery",
    "publicAlignment",
    "rightsSafeguard",
    "captureResistance",
    "legitimacy",
    "efficiency",
    "complexityScore",
    "resilienceFloor",
]

PARETO_DIMENSIONS = [
    "policyDelivery",
    "publicAlignment",
    "rightsSafeguard",
    "captureResistance",
    "legitimacy",
    "complexityScore",
    "resilienceFloor",
]

SCORING_PROFILES = [
    ScoringProfile(
        slug="balanced",
        label="Balanced",
        description="Default portfolio view: delivery, public alignment, rights, capture resistance, legitimacy, efficiency, and subsystem floor.",
        weights={
            "policyDelivery": 0.22,
            "publicAlignment": 0.18,
            "rightsSafeguard": 0.18,
            "captureResistance": 0.18,
            "legitimacy": 0.10,
            "efficiency": 0.08,
            "resilienceFloor": 0.06,
        },
    ),
    ScoringProfile(
        slug="efficiency-first",
        label="Efficiency First",
        description="Rewards throughput and administrative simplicity, while keeping a smaller floor for legitimacy, rights, and capture controls.",
        weights={
            "policyDelivery": 0.32,
            "efficiency": 0.26,
            "complexityScore": 0.18,
            "publicAlignment": 0.08,
            "rightsSafeguard": 0.06,
            "captureResistance": 0.06,
            "legitimacy": 0.04,
        },
    ),
    ScoringProfile(
        slug="rights-first",
        label="Rights First",
        description="Prioritizes constitutional safeguards, legal stability, and legitimacy under review pressure.",
        weights={
            "rightsSafeguard": 0.36,
            "legitimacy": 0.18,
            "publicAlignment": 0.14,
            "captureResistance": 0.12,
            "policyDelivery": 0.08,
            "resilienceFloor": 0.08,
            "efficiency": 0.04,
        },
    ),
    ScoringProfile(
        slug="anti-capture-first",
        label="Anti-Capture First",
        description="Treats capture resistance, transparency, and public-interest alignment as the main constitutional constraint.",
        weights={
            "captureResistance": 0.38,
            "publicAlignment": 0.16,
            "legitimacy": 0.14,
            "rightsSafeguard": 0.10,
            "policyDelivery": 0.08,
            "resilienceFloor": 0.08,
            "efficiency": 0.06,
        },
    ),
    ScoringProfile(
        slug="low-complexity",
        label="Low Complexity",
        description="Favors simpler, lower-cost institutional packages that still clear basic safeguards.",
        weights={
            "complexityScore": 0.34,
            "efficiency": 0.20,
            "resilienceFloor": 0.14,
            "policyDelivery": 0.12,
            "publicAlignment": 0.08,
            "rightsSafeguard": 0.06,
            "captureResistance": 0.06,
        },
    ),
    ScoringProfile(
        slug="legitimacy-first",
        label="Legitimacy First",
        description="Prioritizes public confidence, democratic responsiveness, transparent review, and representative alignment.",
        weights={
            "legitimacy": 0.30,
            "publicAlignment": 0.24,
            "rightsSafeguard": 0.14,
            "captureResistance": 0.12,
            "policyDelivery": 0.08,
            "complexityScore": 0.06,
            "resilienceFloor": 0.06,
        },
    ),
]

DEFAULT_PROFILE = "balanced"

UNCERTAINTY_BAND_FLOOR = 0.035
SEPARATE_CALIBRATION_PENALTY = 0.025
UNCERTAINTY_BAND_CAP = 0.140
EPSILON_PARETO_MARGIN = 0.025

CURRENT_BASELINE_KEYS = {
    "legislatureKey": "current-system",
    "reviewKey": "current-us-like",
    "antiCaptureKey": "open-access-lobbying",
}

SPECULATIVE_MODELING_AGENDA = [
    (
        "Phased reform sequences",
        "Model transition paths rather than assuming all institutional changes arrive at once.",
        "Speculative extension",
    ),
    (
        "Constitutional transition costs",
        "Represent amendment difficulty, legitimacy shocks, retraining costs, litigation delay, and path-dependence.",
        "Bridge v1 first-pass synthetic; needs calibration",
    ),
    (
        "Federalism and agency capacity",
        "Add subnational veto points, administrative staffing, enforcement capacity, procurement pressure, and intergovernmental conflict.",
        "Bridge v0/v1 stress layer; needs source simulator",
    ),
    (
        "Public implementation feedback",
        "Let public trust, compliance, and perceived policy quality feed back into future agenda access and reform durability.",
        "Bridge v1 first-pass synthetic; needs calibration",
    ),
    (
        "Citizen agenda setting",
        "Test ballot access, deliberative citizen panels, public agenda petitions, and participatory budget channels as proposal-entry systems.",
        "Bridge v1 first-pass synthetic; needs mechanism rows",
    ),
]


LEGISLATURE_METRICS = [
    MetricSpec("directionalScore", 3.0),
    MetricSpec("representativeQuality", 2.0),
    MetricSpec("riskControl", 2.0),
    MetricSpec("administrativeFeasibility", 1.2),
    MetricSpec("productivity", 1.8),
    MetricSpec("welfare", 1.6),
    MetricSpec("publicAlignment", 1.8),
    MetricSpec("democraticResponsiveness", 1.5),
    MetricSpec("legitimacy", 1.2),
    MetricSpec("antiLobbyingSuccess", 1.0),
    MetricSpec("activeLawWelfare", 0.8),
    MetricSpec("gridlock", 1.2, "negative"),
    MetricSpec("lowSupport", 1.2, "negative"),
    MetricSpec("weakPublicMandatePassage", 1.2, "negative"),
    MetricSpec("concentratedHarmPassage", 1.0, "negative"),
    MetricSpec("lobbyCapture", 1.2, "negative"),
    MetricSpec("privateGainRatio", 1.0, "negative_ratio"),
    MetricSpec("administrativeCost", 0.8, "negative"),
]

REVIEW_METRICS = [
    MetricSpec("directionalScore", 3.0),
    MetricSpec("stabilityRightsScore", 2.0),
    MetricSpec("legitimacyControlScore", 2.0),
    MetricSpec("legalStability", 1.7),
    MetricSpec("rightsProtection", 1.8),
    MetricSpec("democraticResponsiveness", 1.2),
    MetricSpec("independenceAccountabilityBalance", 1.2),
    MetricSpec("legitimacy", 1.4),
    MetricSpec("publicConfidence", 1.0),
    MetricSpec("lowerCourtCompliance", 0.8),
    MetricSpec("partisanAlignment", 1.3, "negative"),
    MetricSpec("shadowDocketAbuse", 1.4, "negative"),
    MetricSpec("emergencyLegitimacyRisk", 1.2, "negative"),
    MetricSpec("constitutionalConflict", 1.2, "negative"),
    MetricSpec("reversalRate", 0.7, "negative"),
    MetricSpec("administrativeCost", 0.8, "negative"),
    MetricSpec("totalInstitutionalCost", 0.8, "negative"),
    MetricSpec("implementationComplexity", 0.5, "negative"),
]

HARMONIZED_REVIEW_METRICS = [
    MetricSpec("directionalScore", 3.0),
    MetricSpec("legalStability", 1.7),
    MetricSpec("rightsProtection", 1.8),
    MetricSpec("democraticResponsiveness", 1.2),
    MetricSpec("independenceAccountabilityBalance", 1.2),
    MetricSpec("legitimacy", 1.4),
    MetricSpec("partisanAlignment", 1.3, "negative"),
    MetricSpec("shadowDocketAbuse", 1.4, "negative"),
    MetricSpec("constitutionalConflict", 1.2, "negative"),
    MetricSpec("reversalRate", 0.7, "negative"),
]

REVIEW_SOURCE_METADATA = {
    "Supreme Court Simulator Design": {
        "prefix": "scd",
        "project": "Supreme Court Simulator Design",
        "denominator": "case-weighted scenario mean over the imported Supreme Court Design campaign rows",
    },
    "Constitutional Review Simulator": {
        "prefix": "crs",
        "project": "Constitutional Review Simulator",
        "denominator": "unweighted sensitivity-case scenario mean; caseWeight is absent and treated as 1.0",
    },
}

ANTI_CAPTURE_METRICS = [
    MetricSpec("directionalScore", 3.0),
    MetricSpec("captureControl", 2.0),
    MetricSpec("representation", 1.5),
    MetricSpec("reformFeasibility", 1.2),
    MetricSpec("antiCaptureSuccess", 1.8),
    MetricSpec("avgPublicInterest", 1.4),
    MetricSpec("darkMoneyTraceability", 1.0),
    MetricSpec("darkMoneyDirectVisibility", 1.0),
    MetricSpec("detectionRate", 1.2),
    MetricSpec("sanctionRate", 0.8),
    MetricSpec("netTransparencyGain", 1.3),
    MetricSpec("commentAuthenticity", 0.7),
    MetricSpec("commentUniqueInformationShare", 0.7),
    MetricSpec("captureRate", 1.8, "negative"),
    MetricSpec("publicPreferenceDistortion", 1.3, "negative"),
    MetricSpec("policyDistortion", 1.1, "negative"),
    MetricSpec("hiddenInfluenceShare", 1.2, "negative"),
    MetricSpec("influencePreservationRate", 1.0, "negative"),
    MetricSpec("privateGainRatio", 1.0, "negative_ratio"),
    MetricSpec("reformDecayPressure", 0.9, "negative"),
    MetricSpec("administrativeCost", 0.8, "negative"),
]

COMPANION_REVIEW_SOURCE = SourceConfig(
    kind="review",
    label="Constitutional Review Simulator",
    path=SIMULATORS / "Constitutional Review Simulator" / "reports" / "constitutional-review-sensitivity-v1.csv",
    key_column="scenarioKey",
    name_column="scenario",
    metrics=REVIEW_METRICS,
)

REVIEW_ADAPTIVE_CANDIDATE_COLUMNS = {
    "complianceRate": ("positive", "Adaptive bridge compliance/recovery input candidate."),
    "defianceRate": ("negative", "Adaptive bridge institutional noncompliance input candidate."),
    "workaroundRate": ("negative", "Adaptive bridge evasion/noncompliance input candidate."),
    "executiveImplementationRate": ("positive", "Agency/executive implementation capacity input candidate."),
    "agencyNonacquiescenceRate": ("negative", "Agency noncompliance and implementation-friction input candidate."),
    "localGovernmentComplianceRate": ("positive", "Federalism/local compliance input candidate."),
    "publicTrust": ("positive", "Public trust and legitimacy feedback input candidate."),
    "legislativeConflict": ("negative", "Interbranch conflict and court-curbing pressure input candidate."),
    "courtCurbingPressure": ("negative", "Court retaliation/adaptation input candidate."),
    "amendmentPressure": ("negative", "Constitutional transition-pressure input candidate."),
    "implementationCapacity": ("positive", "Administrative capacity input candidate."),
    "legislativeResponseCredibility": ("positive", "Weak-form response and correction-cycle input candidate."),
    "democraticConstitutionalism": ("positive", "Composite democratic constitutionalism cross-check."),
    "vetoRelocationRisk": ("negative", "Institutional veto relocation risk input candidate."),
    "legalTransplantFeasibility": ("positive", "Transition feasibility and comparative-transfer input candidate."),
    "politicalCultureSensitivity": ("negative", "Political-culture fragility input candidate."),
}


def default_sources() -> list[SourceConfig]:
    return [
        SourceConfig(
            kind="legislature",
            label="Congress Institutional Simulator",
            path=SIMULATORS / "Congress Institutional Simulator" / "reports" / "simulation-campaign-v21-paper.csv",
            key_column="scenarioKey",
            name_column="scenario",
            metrics=LEGISLATURE_METRICS,
        ),
        SourceConfig(
            kind="review",
            label="Supreme Court Simulator Design",
            path=SIMULATORS / "Supreme Court Simulator Design" / "reports" / "constitutional-review-campaign-v2.csv",
            key_column="scenarioKey",
            name_column="scenario",
            metrics=REVIEW_METRICS,
        ),
        SourceConfig(
            kind="anti_capture",
            label="Lobby Capture Simulator",
            path=SIMULATORS / "Lobby Capture Simulator" / "reports" / "lobby-capture-campaign.csv",
            key_column="scenarioKey",
            name_column="scenarioName",
            metrics=ANTI_CAPTURE_METRICS,
        ),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--congress-csv", type=Path, help="Override the legislative source CSV.")
    parser.add_argument("--review-csv", type=Path, help="Override the constitutional-review source CSV.")
    parser.add_argument("--lobby-csv", type=Path, help="Override the anti-capture source CSV.")
    parser.add_argument("--congress-label", help="Override the legislative source label used in provenance.")
    parser.add_argument("--review-label", help="Override the constitutional-review source label used in provenance.")
    parser.add_argument("--lobby-label", help="Override the anti-capture source label used in provenance.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports")
    parser.add_argument("--top", type=int, default=25, help="Number of portfolio rows to show in Markdown.")
    parser.add_argument("--quiet", action="store_true")
    return parser.parse_args()


def resolved(path: Path) -> Path:
    return path if path.is_absolute() else (ROOT / path).resolve()


def apply_overrides(sources: list[SourceConfig], args: argparse.Namespace) -> list[SourceConfig]:
    overrides = {
        "legislature": args.congress_csv,
        "review": args.review_csv,
        "anti_capture": args.lobby_csv,
    }
    label_overrides = {
        "legislature": args.congress_label,
        "review": args.review_label,
        "anti_capture": args.lobby_label,
    }
    updated: list[SourceConfig] = []
    for source in sources:
        override = overrides.get(source.kind)
        label = label_overrides.get(source.kind) or source.label
        if override is None and label == source.label:
            updated.append(source)
        else:
            updated.append(
                SourceConfig(
                    kind=source.kind,
                    label=label,
                    path=resolved(override) if override is not None else source.path,
                    key_column=source.key_column,
                    name_column=source.name_column,
                    metrics=source.metrics,
                )
            )
    return updated


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing source CSV: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def number(value: str | None) -> float | None:
    if value is None:
        return None
    text = str(value).strip().strip('"')
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def transform(value: float | None, direction: str) -> float | None:
    if value is None:
        return None
    if direction == "positive":
        return clamp01(value)
    if direction == "negative":
        return 1.0 - clamp01(value)
    if direction == "positive_ratio":
        return clamp01(max(0.0, value) / (1.0 + max(0.0, value)))
    if direction == "negative_ratio":
        return clamp01(1.0 / (1.0 + max(0.0, value)))
    raise ValueError(f"Unknown metric direction: {direction}")


def weighted_mean(values: Iterable[tuple[float | None, float]]) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for value, weight in values:
        if value is None:
            continue
        numerator += value * weight
        denominator += weight
    if denominator == 0.0:
        return None
    return numerator / denominator


def mean(values: Iterable[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def weighted_case_value(rows: list[dict[str, str]], column: str, direction: str = "positive") -> float | None:
    values: list[tuple[float | None, float]] = []
    for row in rows:
        case_weight = number(row.get("caseWeight")) or 1.0
        values.append((transform(number(row.get(column)), direction), case_weight))
    return weighted_mean(values)


def weighted_raw_value(rows: list[dict[str, str]], column: str) -> float | None:
    values: list[tuple[float | None, float]] = []
    for row in rows:
        case_weight = number(row.get("caseWeight")) or 1.0
        values.append((number(row.get(column)), case_weight))
    return weighted_mean(values)


def aggregate_source(source: SourceConfig) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows = read_csv(source.path)
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        key = row.get(source.key_column, "").strip().strip('"')
        if not key:
            continue
        grouped.setdefault(key, []).append(row)

    options: list[dict[str, object]] = []
    for key, group_rows in grouped.items():
        first = group_rows[0]
        metric_scores: dict[str, float] = {}
        raw_values: dict[str, float] = {}
        weighted_scores: list[tuple[float | None, float]] = []
        used_columns: list[str] = []

        for spec in source.metrics:
            value = weighted_case_value(group_rows, spec.column, spec.direction)
            if value is None:
                continue
            metric_scores[spec.column] = value
            raw = weighted_raw_value(group_rows, spec.column)
            if raw is not None:
                raw_values[spec.column] = raw
            weighted_scores.append((value, spec.weight))
            used_columns.append(spec.column)

        score = weighted_mean(weighted_scores)
        if score is None:
            continue

        options.append(
            {
                "kind": source.kind,
                "source": source.label,
                "sourcePath": str(source.path),
                "scenarioKey": key,
                "scenarioName": first.get(source.name_column, key).strip().strip('"') or key,
                "score": score,
                "rowCount": len(group_rows),
                "metricCoverage": len(used_columns),
                "configuredMetricCount": len(source.metrics),
                "metricScores": metric_scores,
                "rawValues": raw_values,
            }
        )

    options.sort(key=lambda item: float(item["score"]), reverse=True)
    inventory = {
        "kind": source.kind,
        "label": source.label,
        "path": str(source.path),
        "rows": len(rows),
        "scenarioCount": len(options),
        "configuredMetricCount": len(source.metrics),
        "metricColumnsConfigured": [spec.column for spec in source.metrics],
    }
    return options, inventory


def score_from(option: dict[str, object], column: str, direction: str = "positive") -> float | None:
    raw_values = option.get("rawValues", {})
    if isinstance(raw_values, dict) and column in raw_values:
        return transform(float(raw_values[column]), direction)
    metric_scores = option.get("metricScores", {})
    if isinstance(metric_scores, dict) and column in metric_scores:
        value = float(metric_scores[column])
        if direction == "positive":
            return value
    return None


def score_mean(items: Iterable[tuple[dict[str, object], str, str]]) -> float:
    values = [score_from(option, column, direction) for option, column, direction in items]
    return mean(values) or 0.0


def portfolio_scores(legislature: dict[str, object], review: dict[str, object], anti_capture: dict[str, object]) -> dict[str, float]:
    policy_delivery = score_mean(
        [
            (legislature, "productivity", "positive"),
            (legislature, "welfare", "positive"),
            (legislature, "publicAlignment", "positive"),
            (legislature, "gridlock", "negative"),
            (legislature, "timeToCorrectBadLaw", "negative"),
        ]
    )
    public_alignment = score_mean(
        [
            (legislature, "representativeQuality", "positive"),
            (legislature, "publicAlignment", "positive"),
            (legislature, "democraticResponsiveness", "positive"),
            (review, "democraticResponsiveness", "positive"),
            (anti_capture, "representation", "positive"),
            (anti_capture, "avgPublicInterest", "positive"),
        ]
    )
    rights_safeguard = score_mean(
        [
            (review, "rightsProtection", "positive"),
            (review, "legalStability", "positive"),
            (review, "stabilityRightsScore", "positive"),
            (review, "shadowDocketAbuse", "negative"),
            (review, "emergencyLegitimacyRisk", "negative"),
            (review, "constitutionalConflict", "negative"),
            (legislature, "weakPublicMandatePassage", "negative"),
            (legislature, "concentratedHarmPassage", "negative"),
        ]
    )
    capture_resistance = score_mean(
        [
            (anti_capture, "captureControl", "positive"),
            (anti_capture, "antiCaptureSuccess", "positive"),
            (anti_capture, "detectionRate", "positive"),
            (anti_capture, "sanctionRate", "positive"),
            (anti_capture, "netTransparencyGain", "positive"),
            (anti_capture, "captureRate", "negative"),
            (anti_capture, "publicPreferenceDistortion", "negative"),
            (anti_capture, "hiddenInfluenceShare", "negative"),
            (legislature, "lobbyCapture", "negative"),
            (legislature, "antiLobbyingSuccess", "positive"),
        ]
    )
    legitimacy = score_mean(
        [
            (legislature, "legitimacy", "positive"),
            (review, "legitimacy", "positive"),
            (review, "publicConfidence", "positive"),
            (review, "legitimacyControlScore", "positive"),
            (anti_capture, "representation", "positive"),
        ]
    )
    complexity_score = score_mean(
        [
            (legislature, "administrativeFeasibility", "positive"),
            (legislature, "administrativeCost", "negative"),
            (review, "administrativeCost", "negative"),
            (review, "totalInstitutionalCost", "negative"),
            (review, "implementationComplexity", "negative"),
            (anti_capture, "reformFeasibility", "positive"),
            (anti_capture, "administrativeCost", "negative"),
        ]
    )
    efficiency = (policy_delivery * 0.65) + (complexity_score * 0.35)
    component_balance = min(
        float(legislature["score"]),
        float(review["score"]),
        float(anti_capture["score"]),
        rights_safeguard,
        capture_resistance,
        complexity_score,
    )
    return {
        "policyDelivery": policy_delivery,
        "publicAlignment": public_alignment,
        "rightsSafeguard": rights_safeguard,
        "captureResistance": capture_resistance,
        "legitimacy": legitimacy,
        "efficiency": efficiency,
        "complexityScore": complexity_score,
        "resilienceFloor": component_balance,
    }


def tradeoff_note(row: dict[str, object]) -> str:
    notes: list[str] = []
    if float(row["policyDelivery"]) >= 0.70:
        notes.append("strong delivery")
    if float(row["rightsSafeguard"]) >= 0.75:
        notes.append("strong rights screen")
    if float(row["captureResistance"]) >= 0.75:
        notes.append("strong anti-capture")
    if float(row["complexityScore"]) < 0.55:
        notes.append("complexity risk")
    if float(row["resilienceFloor"]) < 0.55:
        notes.append("weak subsystem floor")
    if not notes:
        notes.append("balanced tradeoff")
    return "; ".join(notes)


def score_for_profile(row: dict[str, object], profile: ScoringProfile) -> float:
    numerator = 0.0
    denominator = 0.0
    for key, weight in profile.weights.items():
        value = row.get(key)
        if value is None:
            continue
        numerator += float(value) * weight
        denominator += weight
    if denominator == 0.0:
        raise RuntimeError(f"Profile has no usable dimensions: {profile.slug}")
    return numerator / denominator


def assign_profile_scores(portfolios: list[dict[str, object]]) -> None:
    for row in portfolios:
        profile_scores = {profile.slug: score_for_profile(row, profile) for profile in SCORING_PROFILES}
        row["profileScores"] = profile_scores
        row["profileRanks"] = {}
        row["overallScore"] = profile_scores[DEFAULT_PROFILE]

    for profile in SCORING_PROFILES:
        ordered = sorted(
            portfolios,
            key=lambda item: (
                float(item["profileScores"][profile.slug]),  # type: ignore[index]
                float(item["resilienceFloor"]),
                float(item["complexityScore"]),
            ),
            reverse=True,
        )
        for rank, row in enumerate(ordered, start=1):
            row["profileRanks"][profile.slug] = rank  # type: ignore[index]


def component_uncertainty(option: dict[str, object], configured_metric_count: int) -> float:
    row_count = max(1.0, float(option.get("rowCount", 1)))
    metric_coverage = max(0.0, float(option.get("metricCoverage", 0)))
    coverage_gap = max(0.0, (configured_metric_count - metric_coverage) / max(1.0, configured_metric_count))
    row_penalty = min(1.0, 1.0 / (row_count**0.5))
    return 0.012 + (0.035 * coverage_gap) + (0.025 * row_penalty)


def assign_uncertainty_bands(portfolios: list[dict[str, object]], metric_counts: dict[str, int]) -> None:
    for row in portfolios:
        component_band = mean(
            [
                component_uncertainty(
                    {
                        "rowCount": row["legislatureRowCount"],
                        "metricCoverage": row["legislatureMetricCoverage"],
                    },
                    metric_counts["legislature"],
                ),
                component_uncertainty(
                    {
                        "rowCount": row["reviewRowCount"],
                        "metricCoverage": row["reviewMetricCoverage"],
                    },
                    metric_counts["review"],
                ),
                component_uncertainty(
                    {
                        "rowCount": row["antiCaptureRowCount"],
                        "metricCoverage": row["antiCaptureMetricCoverage"],
                    },
                    metric_counts["anti_capture"],
                ),
            ]
        ) or 0.0
        component_scores = [
            float(row["legislatureScore"]),
            float(row["reviewScore"]),
            float(row["antiCaptureScore"]),
        ]
        profile_scores = list(row["profileScores"].values())  # type: ignore[union-attr]
        component_spread = max(component_scores) - min(component_scores)
        profile_spread = max(profile_scores) - min(profile_scores)
        dimension_values = [float(row[key]) for key in PARETO_DIMENSIONS]
        dimension_spread = max(dimension_values) - min(dimension_values)
        band = min(
            UNCERTAINTY_BAND_CAP,
            UNCERTAINTY_BAND_FLOOR
            + SEPARATE_CALIBRATION_PENALTY
            + component_band
            + (0.030 * component_spread)
            + (0.035 * profile_spread)
            + (0.020 * dimension_spread),
        )
        score = float(row["overallScore"])
        row["modelUncertaintyBand"] = band
        row["uncertaintyLow"] = max(0.0, score - band)
        row["uncertaintyHigh"] = min(1.0, score + band)
        row["uncertaintyNote"] = "synthetic uncertainty band, not empirical confidence interval"


def assign_minimax_regret(portfolios: list[dict[str, object]]) -> None:
    best_by_profile = {
        profile.slug: max(profile_score(row, profile.slug) for row in portfolios)
        for profile in SCORING_PROFILES
    }
    for row in portfolios:
        regrets = {
            profile.slug: best_by_profile[profile.slug] - profile_score(row, profile.slug)
            for profile in SCORING_PROFILES
        }
        max_regret = max(regrets.values())
        average_regret = sum(regrets.values()) / len(regrets)
        row["profileRegrets"] = regrets
        row["maxProfileRegret"] = max_regret
        row["averageProfileRegret"] = average_regret
        row["minimaxRegretScore"] = 1.0 - max_regret

    ordered = sorted(
        portfolios,
        key=lambda item: (
            float(item["maxProfileRegret"]),
            float(item["averageProfileRegret"]),
            -float(item["resilienceFloor"]),
            -float(item["overallScore"]),
        ),
    )
    for rank, row in enumerate(ordered, start=1):
        row["minimaxRegretRank"] = rank


def interval_relation(row: dict[str, object], reference: dict[str, object], reference_label: str) -> str:
    row_low = float(row["uncertaintyLow"])
    row_high = float(row["uncertaintyHigh"])
    reference_low = float(reference["uncertaintyLow"])
    reference_high = float(reference["uncertaintyHigh"])
    if row_low > reference_high:
        return f"above-{reference_label}"
    if row_high < reference_low:
        return f"below-{reference_label}"
    return f"overlaps-{reference_label}"


def intervals_overlap(left: dict[str, object], right: dict[str, object]) -> bool:
    return float(left["uncertaintyLow"]) <= float(right["uncertaintyHigh"]) and float(right["uncertaintyLow"]) <= float(left["uncertaintyHigh"])


def assign_uncertainty_resolution(portfolios: list[dict[str, object]]) -> None:
    balanced = portfolios[0]
    for rank, row in enumerate(
        sorted(
            portfolios,
            key=lambda item: (
                -float(item["uncertaintyLow"]),
                -float(item["overallScore"]),
                -float(item["resilienceFloor"]),
            ),
        ),
        start=1,
    ):
        row["uncertaintyLowerBoundRank"] = rank
    for rank, row in enumerate(
        sorted(
            portfolios,
            key=lambda item: (
                -float(item["uncertaintyHigh"]),
                -float(item["overallScore"]),
                -float(item["resilienceFloor"]),
            ),
        ),
        start=1,
    ):
        row["uncertaintyUpperBoundRank"] = rank

    sorted_lows = sorted(float(row["uncertaintyLow"]) for row in portfolios)
    sorted_highs = sorted(float(row["uncertaintyHigh"]) for row in portfolios)
    total = len(portfolios)
    for row in portfolios:
        row_low = float(row["uncertaintyLow"])
        row_high = float(row["uncertaintyHigh"])
        dominated_by = total - bisect_right(sorted_lows, row_high)
        dominates_count = bisect_left(sorted_highs, row_low)
        row["uncertaintyDominatedByCount"] = dominated_by
        row["uncertaintyDominatesCount"] = dominates_count
        row["balancedIntervalRelation"] = interval_relation(row, balanced, "balanced")
        row["overlapsBalancedInterval"] = "yes" if intervals_overlap(row, balanced) else "no"

    for rank, row in enumerate(
        sorted(
            portfolios,
            key=lambda item: (
                int(item["uncertaintyDominatedByCount"]),
                -float(item["uncertaintyLow"]),
                -float(item["overallScore"]),
                -float(item["resilienceFloor"]),
            ),
        ),
        start=1,
    ):
        row["uncertaintyDominanceRank"] = rank


def build_portfolios(options_by_kind: dict[str, list[dict[str, object]]], metric_counts: dict[str, int]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for legislature, review, anti_capture in product(
        options_by_kind["legislature"],
        options_by_kind["review"],
        options_by_kind["anti_capture"],
    ):
        scores = portfolio_scores(legislature, review, anti_capture)
        row: dict[str, object] = {
            **scores,
            "legislatureKey": legislature["scenarioKey"],
            "legislature": legislature["scenarioName"],
            "legislatureScore": legislature["score"],
            "legislatureRowCount": legislature["rowCount"],
            "legislatureMetricCoverage": legislature["metricCoverage"],
            "reviewKey": review["scenarioKey"],
            "review": review["scenarioName"],
            "reviewScore": review["score"],
            "reviewRowCount": review["rowCount"],
            "reviewMetricCoverage": review["metricCoverage"],
            "antiCaptureKey": anti_capture["scenarioKey"],
            "antiCapture": anti_capture["scenarioName"],
            "antiCaptureScore": anti_capture["score"],
            "antiCaptureRowCount": anti_capture["rowCount"],
            "antiCaptureMetricCoverage": anti_capture["metricCoverage"],
        }
        row["tradeoffNote"] = tradeoff_note(row)
        rows.append(row)
    assign_profile_scores(rows)
    assign_uncertainty_bands(rows, metric_counts)
    assign_minimax_regret(rows)
    rows.sort(key=lambda item: float(item["overallScore"]), reverse=True)
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    assign_uncertainty_resolution(rows)
    return rows


def fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def write_component_scores(path: Path, options_by_kind: dict[str, list[dict[str, object]]]) -> None:
    fieldnames = [
        "kind",
        "rank",
        "scenarioKey",
        "scenarioName",
        "score",
        "rowCount",
        "metricCoverage",
        "configuredMetricCount",
        "metricCoverageShare",
        "source",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for kind, options in options_by_kind.items():
            for rank, option in enumerate(options, start=1):
                writer.writerow(
                    {
                        "kind": kind,
                        "rank": rank,
                        "scenarioKey": option["scenarioKey"],
                        "scenarioName": option["scenarioName"],
                        "score": fmt(option["score"]),
                        "rowCount": option["rowCount"],
                        "metricCoverage": option["metricCoverage"],
                        "configuredMetricCount": option["configuredMetricCount"],
                        "metricCoverageShare": fmt(
                            int(option["metricCoverage"]) / max(1, int(option["configuredMetricCount"]))
                        ),
                        "source": option["source"],
                    }
                )


def write_portfolio_csv(path: Path, portfolios: list[dict[str, object]]) -> None:
    fieldnames = [
        "rank",
        "overallScore",
        "uncertaintyLow",
        "uncertaintyHigh",
        "modelUncertaintyBand",
        "uncertaintyLowerBoundRank",
        "uncertaintyUpperBoundRank",
        "uncertaintyDominanceRank",
        "uncertaintyDominatedByCount",
        "uncertaintyDominatesCount",
        "overlapsBalancedInterval",
        "balancedIntervalRelation",
        "minimaxRegretRank",
        "maxProfileRegret",
        "averageProfileRegret",
        "policyDelivery",
        "publicAlignment",
        "rightsSafeguard",
        "captureResistance",
        "legitimacy",
        "efficiency",
        "complexityScore",
        "resilienceFloor",
        "legislatureKey",
        "legislature",
        "legislatureScore",
        "reviewKey",
        "review",
        "reviewScore",
        "antiCaptureKey",
        "antiCapture",
        "antiCaptureScore",
        "uncertaintyNote",
        "tradeoffNote",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in portfolios:
            writer.writerow({key: fmt(row[key]) for key in fieldnames})


def profile_score(row: dict[str, object], profile_slug: str) -> float:
    return float(row["profileScores"][profile_slug])  # type: ignore[index]


def profile_rank(row: dict[str, object], profile_slug: str) -> int:
    return int(row["profileRanks"][profile_slug])  # type: ignore[index]


def write_profile_sensitivity_csv(path: Path, portfolios: list[dict[str, object]]) -> None:
    fieldnames = [
        "profile",
        "profileLabel",
        "profileRank",
        "profileScore",
        "balancedRank",
        "minimaxRegretRank",
        "maxProfileRegret",
        "modelUncertaintyBand",
        "legislatureKey",
        "legislature",
        "reviewKey",
        "review",
        "antiCaptureKey",
        "antiCapture",
        *DIMENSION_KEYS,
        "tradeoffNote",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for profile in SCORING_PROFILES:
            ordered = sorted(portfolios, key=lambda item: profile_rank(item, profile.slug))
            for row in ordered:
                writer.writerow(
                    {
                        "profile": profile.slug,
                        "profileLabel": profile.label,
                        "profileRank": profile_rank(row, profile.slug),
                        "profileScore": fmt(profile_score(row, profile.slug)),
                        "balancedRank": row["rank"],
                        "minimaxRegretRank": row["minimaxRegretRank"],
                        "maxProfileRegret": fmt(row["maxProfileRegret"]),
                        "modelUncertaintyBand": fmt(row["modelUncertaintyBand"]),
                        "legislatureKey": row["legislatureKey"],
                        "legislature": row["legislature"],
                        "reviewKey": row["reviewKey"],
                        "review": row["review"],
                        "antiCaptureKey": row["antiCaptureKey"],
                        "antiCapture": row["antiCapture"],
                        **{key: fmt(row[key]) for key in DIMENSION_KEYS},
                        "tradeoffNote": row["tradeoffNote"],
                    }
                )


def robustness_rows(portfolios: list[dict[str, object]]) -> list[dict[str, object]]:
    total = len(portfolios)
    rows: list[dict[str, object]] = []
    for row in portfolios:
        ranks = [profile_rank(row, profile.slug) for profile in SCORING_PROFILES]
        scores = [profile_score(row, profile.slug) for profile in SCORING_PROFILES]
        average_rank = sum(ranks) / len(ranks)
        worst_rank = max(ranks)
        best_rank = min(ranks)
        top_10 = sum(1 for rank in ranks if rank <= 10)
        top_25 = sum(1 for rank in ranks if rank <= 25)
        top_100 = sum(1 for rank in ranks if rank <= 100)
        rank_strength = 1.0 - ((average_rank - 1.0) / max(1.0, total - 1.0))
        floor_strength = 1.0 - ((worst_rank - 1.0) / max(1.0, total - 1.0))
        robust_score = (
            0.36 * rank_strength
            + 0.24 * floor_strength
            + 0.20 * (top_25 / len(SCORING_PROFILES))
            + 0.12 * (top_100 / len(SCORING_PROFILES))
            + 0.08 * (float(row["resilienceFloor"]))
        )
        rows.append(
            {
                "robustScore": robust_score,
                "averageProfileRank": average_rank,
                "bestProfileRank": best_rank,
                "worstProfileRank": worst_rank,
                "top10ProfileCount": top_10,
                "top25ProfileCount": top_25,
                "top100ProfileCount": top_100,
                "scoreSpread": max(scores) - min(scores),
                **row,
            }
        )
    rows.sort(
        key=lambda item: (
            float(item["robustScore"]),
            int(item["top25ProfileCount"]),
            -float(item["averageProfileRank"]),
        ),
        reverse=True,
    )
    for rank, row in enumerate(rows, start=1):
        row["robustRank"] = rank
    return rows


def write_robustness_csv(path: Path, robust_rows: list[dict[str, object]]) -> None:
    profile_rank_fields = [f"{profile.slug}Rank" for profile in SCORING_PROFILES]
    profile_score_fields = [f"{profile.slug}Score" for profile in SCORING_PROFILES]
    fieldnames = [
        "robustRank",
        "robustScore",
        "averageProfileRank",
        "bestProfileRank",
        "worstProfileRank",
        "top10ProfileCount",
        "top25ProfileCount",
        "top100ProfileCount",
        "scoreSpread",
        "minimaxRegretRank",
        "maxProfileRegret",
        "modelUncertaintyBand",
        "rank",
        "overallScore",
        "legislatureKey",
        "legislature",
        "reviewKey",
        "review",
        "antiCaptureKey",
        "antiCapture",
        *profile_rank_fields,
        *profile_score_fields,
        *DIMENSION_KEYS,
        "tradeoffNote",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in robust_rows:
            output = {
                "robustRank": row["robustRank"],
                "robustScore": fmt(row["robustScore"]),
                "averageProfileRank": fmt(row["averageProfileRank"]),
                "bestProfileRank": row["bestProfileRank"],
                "worstProfileRank": row["worstProfileRank"],
                "top10ProfileCount": row["top10ProfileCount"],
                "top25ProfileCount": row["top25ProfileCount"],
                "top100ProfileCount": row["top100ProfileCount"],
                "scoreSpread": fmt(row["scoreSpread"]),
                "minimaxRegretRank": row["minimaxRegretRank"],
                "maxProfileRegret": fmt(row["maxProfileRegret"]),
                "modelUncertaintyBand": fmt(row["modelUncertaintyBand"]),
                "rank": row["rank"],
                "overallScore": fmt(row["overallScore"]),
                "legislatureKey": row["legislatureKey"],
                "legislature": row["legislature"],
                "reviewKey": row["reviewKey"],
                "review": row["review"],
                "antiCaptureKey": row["antiCaptureKey"],
                "antiCapture": row["antiCapture"],
                **{key: fmt(row[key]) for key in DIMENSION_KEYS},
                "tradeoffNote": row["tradeoffNote"],
            }
            for profile in SCORING_PROFILES:
                output[f"{profile.slug}Rank"] = profile_rank(row, profile.slug)
                output[f"{profile.slug}Score"] = fmt(profile_score(row, profile.slug))
            writer.writerow(output)


def write_robustness_markdown(path: Path, robust_rows: list[dict[str, object]], top_count: int) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    text = f"""# Portfolio Robustness

Generated: `{generated_at}`

This report ranks portfolios by cross-profile durability. A robust portfolio does not need to win every value profile; it needs to remain comparatively strong when the weights shift among balanced, efficiency-first, rights-first, anti-capture-first, low-complexity, and legitimacy-first views.

{markdown_table(
    [
        "Robust Rank",
        "Robust Score",
        "Balanced Rank",
        "Avg Profile Rank",
        "Worst Rank",
        "Top-25 Profiles",
        "Score Spread",
        "Legislature",
        "Review",
        "Anti-capture",
    ],
    [
        [
            row["robustRank"],
            row["robustScore"],
            row["rank"],
            row["averageProfileRank"],
            row["worstProfileRank"],
            row["top25ProfileCount"],
            row["scoreSpread"],
            row["legislature"],
            row["review"],
            row["antiCapture"],
        ]
        for row in robust_rows[:top_count]
    ],
)}

## Profile Rank Columns

{markdown_table(
    ["Profile", "Description"],
    [[profile.label, profile.description] for profile in SCORING_PROFILES],
)}
"""
    path.write_text(text, encoding="utf-8")


def write_minimax_regret_csv(path: Path, portfolios: list[dict[str, object]]) -> None:
    profile_rank_fields = [f"{profile.slug}Rank" for profile in SCORING_PROFILES]
    profile_regret_fields = [f"{profile.slug}Regret" for profile in SCORING_PROFILES]
    fieldnames = [
        "minimaxRegretRank",
        "maxProfileRegret",
        "averageProfileRegret",
        "minimaxRegretScore",
        "balancedRank",
        "overallScore",
        "uncertaintyLow",
        "uncertaintyHigh",
        "modelUncertaintyBand",
        "resilienceFloor",
        "complexityScore",
        "legislatureKey",
        "legislature",
        "reviewKey",
        "review",
        "antiCaptureKey",
        "antiCapture",
        *profile_rank_fields,
        *profile_regret_fields,
        "tradeoffNote",
    ]
    rows = sorted(portfolios, key=lambda row: int(row["minimaxRegretRank"]))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            output = {
                "minimaxRegretRank": row["minimaxRegretRank"],
                "maxProfileRegret": fmt(row["maxProfileRegret"]),
                "averageProfileRegret": fmt(row["averageProfileRegret"]),
                "minimaxRegretScore": fmt(row["minimaxRegretScore"]),
                "balancedRank": row["rank"],
                "overallScore": fmt(row["overallScore"]),
                "uncertaintyLow": fmt(row["uncertaintyLow"]),
                "uncertaintyHigh": fmt(row["uncertaintyHigh"]),
                "modelUncertaintyBand": fmt(row["modelUncertaintyBand"]),
                "resilienceFloor": fmt(row["resilienceFloor"]),
                "complexityScore": fmt(row["complexityScore"]),
                "legislatureKey": row["legislatureKey"],
                "legislature": row["legislature"],
                "reviewKey": row["reviewKey"],
                "review": row["review"],
                "antiCaptureKey": row["antiCaptureKey"],
                "antiCapture": row["antiCapture"],
                "tradeoffNote": row["tradeoffNote"],
            }
            for profile in SCORING_PROFILES:
                output[f"{profile.slug}Rank"] = profile_rank(row, profile.slug)
                output[f"{profile.slug}Regret"] = fmt(row["profileRegrets"][profile.slug])  # type: ignore[index]
            writer.writerow(output)


def write_minimax_regret_markdown(path: Path, portfolios: list[dict[str, object]], top_count: int) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rows = sorted(portfolios, key=lambda row: int(row["minimaxRegretRank"]))[:top_count]
    text = f"""# Portfolio Minimax-Regret Ranking

Generated: `{generated_at}`

This report asks which portfolio has the smallest worst-case loss across the configured value profiles. Regret is measured against the best profile score available in the current portfolio universe for each profile. This is a synthetic sensitivity diagnostic, not an empirical confidence interval.

{markdown_table(
    [
        "Regret Rank",
        "Max Regret",
        "Avg Regret",
        "Balanced Rank",
        "Balanced Score",
        "Uncertainty Band",
        "Floor",
        "Legislature",
        "Review",
        "Anti-capture",
    ],
    [
        [
            row["minimaxRegretRank"],
            row["maxProfileRegret"],
            row["averageProfileRegret"],
            row["rank"],
            row["overallScore"],
            row["modelUncertaintyBand"],
            row["resilienceFloor"],
            row["legislature"],
            row["review"],
            row["antiCapture"],
        ]
        for row in rows
    ],
)}

## Reading Notes

- Lower regret is better.
- A portfolio can rank first on minimax regret without being the balanced-score winner.
- Regret is measured only across the value profiles currently defined in `scripts/build_portfolios.py`.
"""
    path.write_text(text, encoding="utf-8")


def uncertainty_tier_rows(portfolios: list[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for row in sorted(portfolios, key=lambda item: int(item["uncertaintyLowerBoundRank"])):
        rows.append(
            {
                "uncertaintyLowerBoundRank": row["uncertaintyLowerBoundRank"],
                "uncertaintyUpperBoundRank": row["uncertaintyUpperBoundRank"],
                "uncertaintyDominanceRank": row["uncertaintyDominanceRank"],
                "balancedRank": row["rank"],
                "overallScore": fmt(row["overallScore"]),
                "uncertaintyLow": fmt(row["uncertaintyLow"]),
                "uncertaintyHigh": fmt(row["uncertaintyHigh"]),
                "modelUncertaintyBand": fmt(row["modelUncertaintyBand"]),
                "uncertaintyDominatedByCount": row["uncertaintyDominatedByCount"],
                "uncertaintyDominatesCount": row["uncertaintyDominatesCount"],
                "overlapsBalancedInterval": row["overlapsBalancedInterval"],
                "balancedIntervalRelation": row["balancedIntervalRelation"],
                "legislatureKey": row["legislatureKey"],
                "legislature": row["legislature"],
                "reviewKey": row["reviewKey"],
                "review": row["review"],
                "antiCaptureKey": row["antiCaptureKey"],
                "antiCapture": row["antiCapture"],
                "tradeoffNote": row["tradeoffNote"],
            }
        )
    return rows


def write_uncertainty_tiers_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "uncertaintyLowerBoundRank",
        "uncertaintyUpperBoundRank",
        "uncertaintyDominanceRank",
        "balancedRank",
        "overallScore",
        "uncertaintyLow",
        "uncertaintyHigh",
        "modelUncertaintyBand",
        "uncertaintyDominatedByCount",
        "uncertaintyDominatesCount",
        "overlapsBalancedInterval",
        "balancedIntervalRelation",
        "legislatureKey",
        "legislature",
        "reviewKey",
        "review",
        "antiCaptureKey",
        "antiCapture",
        "tradeoffNote",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_uncertainty_tiers_markdown(path: Path, portfolios: list[dict[str, object]], rows: list[dict[str, object]], top_count: int) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    balanced = portfolios[0]
    overlap_count = sum(1 for row in portfolios if intervals_overlap(row, balanced))
    separated_below_count = sum(1 for row in portfolios if row["balancedIntervalRelation"] == "below-balanced")
    separated_above_count = sum(1 for row in portfolios if row["balancedIntervalRelation"] == "above-balanced")
    lower_bound_leader = rows[0]
    text = f"""# Portfolio Uncertainty Tiers

Generated: `{generated_at}`

This report is an uncertainty-aware companion to the point-estimate ranking. The lower-bound rank sorts portfolios by the bottom of their synthetic model-sensitivity interval. The interval-dominance rank counts how many portfolios have intervals entirely above a candidate. These bands are not empirical confidence intervals.

## Headline Interval Resolution

{markdown_table(
    ["Diagnostic", "Value"],
    [
        ["Balanced winner interval", f"{fmt(balanced['uncertaintyLow'])}-{fmt(balanced['uncertaintyHigh'])}"],
        ["Portfolios overlapping balanced interval", overlap_count],
        ["Portfolios entirely below balanced interval", separated_below_count],
        ["Portfolios entirely above balanced interval", separated_above_count],
        ["Balanced lower-bound rank", balanced["uncertaintyLowerBoundRank"]],
        ["Lower-bound leader", f"{lower_bound_leader['legislature']} + {lower_bound_leader['review']} + {lower_bound_leader['antiCapture']}"],
    ],
)}

## Lower-Bound Leaders

{markdown_table(
    [
        "Lower-Bound Rank",
        "Balanced Rank",
        "Score",
        "Interval",
        "Dominance Rank",
        "Balanced Relation",
        "Legislature",
        "Review",
        "Anti-capture",
    ],
    [
        [
            row["uncertaintyLowerBoundRank"],
            row["balancedRank"],
            row["overallScore"],
            f"{row['uncertaintyLow']}-{row['uncertaintyHigh']}",
            row["uncertaintyDominanceRank"],
            row["balancedIntervalRelation"],
            row["legislature"],
            row["review"],
            row["antiCapture"],
        ]
        for row in rows[:top_count]
    ],
)}
"""
    path.write_text(text, encoding="utf-8")


def portfolio_key(row: dict[str, object]) -> tuple[object, object, object]:
    return (row["legislatureKey"], row["reviewKey"], row["antiCaptureKey"])


def focused_tradeoff_rows(portfolios: list[dict[str, object]], robust_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    labels_by_key: dict[tuple[object, object, object], list[str]] = {}

    def add(label: str, row: dict[str, object]) -> None:
        labels_by_key.setdefault(portfolio_key(row), []).append(label)

    add("balanced winner", portfolios[0])
    add("robustness winner", robust_rows[0])
    add("minimax-regret winner", min(portfolios, key=lambda row: int(row["minimaxRegretRank"])))
    for profile in SCORING_PROFILES:
        if profile.slug == DEFAULT_PROFILE:
            continue
        add(f"{profile.label} winner", min(portfolios, key=lambda row: profile_rank(row, profile.slug)))
    baseline = next(
        (
            row
            for row in portfolios
            if all(row.get(key) == value for key, value in CURRENT_BASELINE_KEYS.items())
        ),
        None,
    )
    if baseline is not None:
        add("current-system-ish baseline", baseline)

    rows = []
    for row in portfolios:
        key = portfolio_key(row)
        if key not in labels_by_key:
            continue
        output: dict[str, object] = {
            "caseLabels": "; ".join(labels_by_key[key]),
            "balancedRank": row["rank"],
            "balancedScore": fmt(row["overallScore"]),
            "minimaxRegretRank": row["minimaxRegretRank"],
            "maxProfileRegret": fmt(row["maxProfileRegret"]),
            "uncertaintyLow": fmt(row["uncertaintyLow"]),
            "uncertaintyHigh": fmt(row["uncertaintyHigh"]),
            "modelUncertaintyBand": fmt(row["modelUncertaintyBand"]),
            "resilienceFloor": fmt(row["resilienceFloor"]),
            "complexityScore": fmt(row["complexityScore"]),
            "legislature": row["legislature"],
            "review": row["review"],
            "antiCapture": row["antiCapture"],
            "tradeoffNote": row["tradeoffNote"],
        }
        for profile in SCORING_PROFILES:
            output[f"{profile.slug}Rank"] = profile_rank(row, profile.slug)
            output[f"{profile.slug}Score"] = fmt(profile_score(row, profile.slug))
        rows.append(output)
    rows.sort(key=lambda row: int(row["balancedRank"]))
    return rows


def write_profile_tradeoffs_csv(path: Path, rows: list[dict[str, object]]) -> None:
    profile_rank_fields = [f"{profile.slug}Rank" for profile in SCORING_PROFILES]
    profile_score_fields = [f"{profile.slug}Score" for profile in SCORING_PROFILES]
    fieldnames = [
        "caseLabels",
        "balancedRank",
        "balancedScore",
        "minimaxRegretRank",
        "maxProfileRegret",
        "uncertaintyLow",
        "uncertaintyHigh",
        "modelUncertaintyBand",
        "resilienceFloor",
        "complexityScore",
        "legislature",
        "review",
        "antiCapture",
        *profile_rank_fields,
        *profile_score_fields,
        "tradeoffNote",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_profile_tradeoffs_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    table_rows = []
    for row in rows:
        table_rows.append(
            [
                row["caseLabels"],
                row["balancedRank"],
                row["minimaxRegretRank"],
                row["maxProfileRegret"],
                row["modelUncertaintyBand"],
                row["resilienceFloor"],
                row["legislature"],
                row["review"],
                row["antiCapture"],
            ]
        )
    profile_sections = []
    for profile in SCORING_PROFILES:
        profile_sections.append(f"## {profile.label}")
        profile_sections.append(
            markdown_table(
                ["Case", "Profile Rank", "Profile Score", "Balanced Rank", "Portfolio"],
                [
                    [
                        row["caseLabels"],
                        row[f"{profile.slug}Rank"],
                        row[f"{profile.slug}Score"],
                        row["balancedRank"],
                        f"{row['legislature']} + {row['review']} + {row['antiCapture']}",
                    ]
                    for row in sorted(rows, key=lambda item: int(item[f"{profile.slug}Rank"]))
                ],
            )
        )
        profile_sections.append("")

    text = f"""# Focused Profile Tradeoffs

Generated: `{generated_at}`

This report compares the headline portfolio families profile by profile. It is intentionally narrower than the full sensitivity CSV so the paper can discuss the candidate set rather than thousands of rows.

{markdown_table(
    [
        "Case Labels",
        "Balanced Rank",
        "Regret Rank",
        "Max Regret",
        "Uncertainty Band",
        "Floor",
        "Legislature",
        "Review",
        "Anti-capture",
    ],
    table_rows,
)}

{chr(10).join(profile_sections)}
"""
    path.write_text(text, encoding="utf-8")


def fragility_reasons(row: dict[str, object]) -> list[str]:
    reasons: list[str] = []
    if float(row["modelUncertaintyBand"]) >= 0.110:
        reasons.append("wide synthetic uncertainty band")
    if float(row["resilienceFloor"]) < 0.560:
        reasons.append("weak subsystem floor")
    if float(row["publicAlignment"]) < 0.550:
        reasons.append("weak public alignment")
    if float(row["captureResistance"]) < 0.600:
        reasons.append("capture-control vulnerability")
    if float(row["complexityScore"]) < 0.520:
        reasons.append("administrative complexity risk")
    if float(row["maxProfileRegret"]) > 0.120:
        reasons.append("large worst-profile regret")
    worst_profile_rank = max(profile_rank(row, profile.slug) for profile in SCORING_PROFILES)
    if worst_profile_rank > 1000:
        reasons.append("falls far under at least one value profile")
    if str(row["legislatureKey"]).startswith("default-pass"):
        reasons.append("throughput-specific default-passage risk")
    return reasons


def fragile_watchlist_rows(portfolios: list[dict[str, object]]) -> list[dict[str, object]]:
    candidates: dict[tuple[object, object, object], dict[str, object]] = {}
    for row in portfolios[:25]:
        candidates[portfolio_key(row)] = row
    for profile in SCORING_PROFILES:
        row = min(portfolios, key=lambda item: profile_rank(item, profile.slug))
        candidates[portfolio_key(row)] = row
    candidates[portfolio_key(min(portfolios, key=lambda row: int(row["minimaxRegretRank"])))] = min(
        portfolios,
        key=lambda row: int(row["minimaxRegretRank"]),
    )

    rows: list[dict[str, object]] = []
    for row in candidates.values():
        reasons = fragility_reasons(row)
        if not reasons:
            continue
        rows.append(
            {
                "balancedRank": row["rank"],
                "balancedScore": fmt(row["overallScore"]),
                "minimaxRegretRank": row["minimaxRegretRank"],
                "maxProfileRegret": fmt(row["maxProfileRegret"]),
                "uncertaintyLow": fmt(row["uncertaintyLow"]),
                "uncertaintyHigh": fmt(row["uncertaintyHigh"]),
                "modelUncertaintyBand": fmt(row["modelUncertaintyBand"]),
                "resilienceFloor": fmt(row["resilienceFloor"]),
                "publicAlignment": fmt(row["publicAlignment"]),
                "captureResistance": fmt(row["captureResistance"]),
                "complexityScore": fmt(row["complexityScore"]),
                "legislature": row["legislature"],
                "review": row["review"],
                "antiCapture": row["antiCapture"],
                "doNotRecommendYetReason": "; ".join(reasons),
            }
        )
    rows.sort(key=lambda item: (-len(str(item["doNotRecommendYetReason"]).split("; ")), int(item["balancedRank"])))
    return rows


def write_fragile_watchlist_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "balancedRank",
        "balancedScore",
        "minimaxRegretRank",
        "maxProfileRegret",
        "uncertaintyLow",
        "uncertaintyHigh",
        "modelUncertaintyBand",
        "resilienceFloor",
        "publicAlignment",
        "captureResistance",
        "complexityScore",
        "legislature",
        "review",
        "antiCapture",
        "doNotRecommendYetReason",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_fragile_watchlist_markdown(path: Path, rows: list[dict[str, object]], top_count: int) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    text = f"""# Do Not Recommend Yet Watchlist

Generated: `{generated_at}`

This report lists headline or near-headline portfolios that should not be converted into recommendations without more modeling. Reasons are synthetic diagnostics from the current portfolio layer, not empirical findings.

{markdown_table(
    [
        "Balanced Rank",
        "Score",
        "Regret Rank",
        "Uncertainty Band",
        "Floor",
        "Alignment",
        "Capture",
        "Complexity",
        "Portfolio",
        "Reason",
    ],
    [
        [
            row["balancedRank"],
            row["balancedScore"],
            row["minimaxRegretRank"],
            row["modelUncertaintyBand"],
            row["resilienceFloor"],
            row["publicAlignment"],
            row["captureResistance"],
            row["complexityScore"],
            f"{row['legislature']} + {row['review']} + {row['antiCapture']}",
            row["doNotRecommendYetReason"],
        ]
        for row in rows[:top_count]
    ],
)}
"""
    path.write_text(text, encoding="utf-8")


def write_research_agenda_markdown(path: Path) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    text = f"""# Speculative Modeling Agenda

Generated: `{generated_at}`

These directions are not current findings. They are systems or mechanisms the cumulative simulator should test before the paper makes stronger recommendations.

{markdown_table(
    ["Direction", "Why Add It", "Claim Status"],
    [[direction, rationale, status] for direction, rationale, status in SPECULATIVE_MODELING_AGENDA],
)}
"""
    path.write_text(text, encoding="utf-8")


def dominates(left: dict[str, object], right: dict[str, object], dimensions: list[str]) -> bool:
    strictly_better = False
    for key in dimensions:
        left_value = float(left[key])
        right_value = float(right[key])
        if left_value + 1e-12 < right_value:
            return False
        if left_value > right_value + 1e-12:
            strictly_better = True
    return strictly_better


def epsilon_dominates(left: dict[str, object], right: dict[str, object], dimensions: list[str], epsilon: float) -> bool:
    strictly_better = False
    for key in dimensions:
        left_value = float(left[key])
        right_value = float(right[key])
        if left_value + epsilon < right_value:
            return False
        if left_value > right_value + epsilon:
            strictly_better = True
    return strictly_better


def uncertainty_dominates(left: dict[str, object], right: dict[str, object], dimensions: list[str]) -> bool:
    strictly_better = False
    left_band = float(left["modelUncertaintyBand"])
    right_band = float(right["modelUncertaintyBand"])
    margin = max(EPSILON_PARETO_MARGIN, 0.50 * (left_band + right_band))
    for key in dimensions:
        left_value = float(left[key])
        right_value = float(right[key])
        if left_value + 1e-12 < right_value:
            return False
        if left_value > right_value + margin:
            strictly_better = True
    return strictly_better


def pareto_front(
    portfolios: list[dict[str, object]],
    rank_field: str = "paretoRank",
    mode: str = "exact",
) -> list[dict[str, object]]:
    if mode == "exact":
        dominance = lambda left, right: dominates(left, right, PARETO_DIMENSIONS)
    elif mode == "epsilon":
        dominance = lambda left, right: epsilon_dominates(left, right, PARETO_DIMENSIONS, EPSILON_PARETO_MARGIN)
    elif mode == "uncertainty":
        dominance = lambda left, right: uncertainty_dominates(left, right, PARETO_DIMENSIONS)
    else:
        raise ValueError(f"Unknown Pareto mode: {mode}")

    ordered = sorted(
        portfolios,
        key=lambda item: tuple(float(item[key]) for key in PARETO_DIMENSIONS),
        reverse=True,
    )
    front: list[dict[str, object]] = []
    for candidate in ordered:
        if any(dominance(other, candidate) for other in front):
            continue
        front = [other for other in front if not dominance(candidate, other)]
        front.append(candidate)
    front.sort(
        key=lambda item: (
            float(item["overallScore"]),
            float(item["resilienceFloor"]),
            float(item["complexityScore"]),
        ),
        reverse=True,
    )
    for rank, row in enumerate(front, start=1):
        row[rank_field] = rank
    return front


def write_pareto_csv(path: Path, front: list[dict[str, object]], rank_field: str, criterion: str) -> None:
    fieldnames = [
        rank_field,
        "paretoCriterion",
        "rank",
        "overallScore",
        "modelUncertaintyBand",
        *PARETO_DIMENSIONS,
        "legislatureKey",
        "legislature",
        "reviewKey",
        "review",
        "antiCaptureKey",
        "antiCapture",
        "tradeoffNote",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in front:
            output = {key: fmt(row[key]) for key in fieldnames if key != "paretoCriterion"}
            output["paretoCriterion"] = criterion
            writer.writerow(output)


def top_by(portfolios: list[dict[str, object]], key: str) -> dict[str, object]:
    return max(portfolios, key=lambda item: float(item[key]))


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(fmt(value) for value in row) + " |")
    return "\n".join(lines)


def profile_weight_summary(profile: ScoringProfile) -> str:
    ordered = sorted(profile.weights.items(), key=lambda item: item[1], reverse=True)
    return ", ".join(f"{key} {weight:.0%}" for key, weight in ordered)


def profile_winner_rows(portfolios: list[dict[str, object]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for profile in SCORING_PROFILES:
        winner = min(portfolios, key=lambda item: profile_rank(item, profile.slug))
        rows.append(
            [
                profile.label,
                profile_score(winner, profile.slug),
                winner["rank"],
                winner["legislature"],
                winner["review"],
                winner["antiCapture"],
            ]
        )
    return rows


def write_profile_sensitivity_markdown(path: Path, portfolios: list[dict[str, object]], top_count: int) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    profile_sections: list[str] = []
    for profile in SCORING_PROFILES:
        ordered = sorted(portfolios, key=lambda item: profile_rank(item, profile.slug))[:top_count]
        profile_sections.append(f"## {profile.label}")
        profile_sections.append(profile.description)
        profile_sections.append("")
        profile_sections.append(f"Weights: {profile_weight_summary(profile)}.")
        profile_sections.append("")
        profile_sections.append(
            markdown_table(
                ["Rank", "Score", "Balanced Rank", "Legislature", "Review", "Anti-capture", "Note"],
                [
                    [
                        profile_rank(row, profile.slug),
                        profile_score(row, profile.slug),
                        row["rank"],
                        row["legislature"],
                        row["review"],
                        row["antiCapture"],
                        row["tradeoffNote"],
                    ]
                    for row in ordered
                ],
            )
        )
        profile_sections.append("")

    text = f"""# Portfolio Profile Sensitivity

Generated: `{generated_at}`

This report reranks every institutional portfolio under alternative normative priorities. The goal is to find designs that remain plausible when the weighting scheme changes, not to hide the value judgments behind a single score.

## Profile Winners

{markdown_table(["Profile", "Score", "Balanced Rank", "Legislature", "Review", "Anti-capture"], profile_winner_rows(portfolios))}

{chr(10).join(profile_sections)}
"""
    path.write_text(text, encoding="utf-8")


def write_pareto_markdown(
    path: Path,
    front: list[dict[str, object]],
    total_count: int,
    top_count: int,
    rank_field: str,
    criterion: str,
    description: str,
) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    text = f"""# Pareto Front

Generated: `{generated_at}`

Criterion: `{criterion}`

{description}

Front size: `{len(front)}` of `{total_count}` portfolios.

{markdown_table(
    [
        "Pareto Rank",
        "Balanced Rank",
        "Score",
        "Delivery",
        "Alignment",
        "Rights",
        "Capture",
        "Legitimacy",
        "Complexity",
        "Floor",
        "Legislature",
        "Review",
        "Anti-capture",
    ],
    [
        [
            row[rank_field],
            row["rank"],
            row["overallScore"],
            row["policyDelivery"],
            row["publicAlignment"],
            row["rightsSafeguard"],
            row["captureResistance"],
            row["legitimacy"],
            row["complexityScore"],
            row["resilienceFloor"],
            row["legislature"],
            row["review"],
            row["antiCapture"],
        ]
        for row in front[:top_count]
    ],
)}
"""
    path.write_text(text, encoding="utf-8")


def write_markdown_report(
    path: Path,
    portfolios: list[dict[str, object]],
    robust_rows: list[dict[str, object]],
    pareto_rows: list[dict[str, object]],
    epsilon_pareto_rows: list[dict[str, object]],
    uncertainty_pareto_rows: list[dict[str, object]],
    regret_rows: list[dict[str, object]],
    tradeoff_rows: list[dict[str, object]],
    fragile_rows: list[dict[str, object]],
    uncertainty_rows: list[dict[str, object]],
    options_by_kind: dict[str, list[dict[str, object]]],
    inventory: list[dict[str, object]],
    top_count: int,
) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    top_rows = portfolios[:top_count]
    diagnostic_rows = [
        ("Best overall", top_by(portfolios, "overallScore")),
        ("Best policy delivery", top_by(portfolios, "policyDelivery")),
        ("Best rights safeguard", top_by(portfolios, "rightsSafeguard")),
        ("Best capture resistance", top_by(portfolios, "captureResistance")),
        ("Best legitimacy", top_by(portfolios, "legitimacy")),
        ("Best efficiency", top_by(portfolios, "efficiency")),
        ("Best complexity score", top_by(portfolios, "complexityScore")),
        ("Best resilience floor", top_by(portfolios, "resilienceFloor")),
    ]

    source_table = markdown_table(
        ["Kind", "Source", "Rows", "Scenarios", "Configured Metrics", "Path"],
        [
            [
                item["kind"],
                item["label"],
                item["rows"],
                item["scenarioCount"],
                item["configuredMetricCount"],
                item["path"],
            ]
            for item in inventory
        ],
    )
    portfolio_table = markdown_table(
        [
            "Rank",
            "Score",
            "Uncertainty",
            "Regret Rank",
            "Delivery",
            "Rights",
            "Capture",
            "Legitimacy",
            "Complexity",
            "Legislature",
            "Review",
            "Anti-capture",
            "Note",
        ],
        [
            [
                row["rank"],
                row["overallScore"],
                f"{fmt(row['uncertaintyLow'])}-{fmt(row['uncertaintyHigh'])}",
                row["minimaxRegretRank"],
                row["policyDelivery"],
                row["rightsSafeguard"],
                row["captureResistance"],
                row["legitimacy"],
                row["complexityScore"],
                row["legislature"],
                row["review"],
                row["antiCapture"],
                row["tradeoffNote"],
            ]
            for row in top_rows
        ],
    )
    diagnostic_table = markdown_table(
        ["Diagnostic", "Score", "Legislature", "Review", "Anti-capture"],
        [
            [
                label,
                row["overallScore"] if label == "Best overall" else row[
                    {
                        "Best policy delivery": "policyDelivery",
                        "Best rights safeguard": "rightsSafeguard",
                        "Best capture resistance": "captureResistance",
                        "Best legitimacy": "legitimacy",
                        "Best efficiency": "efficiency",
                        "Best complexity score": "complexityScore",
                        "Best resilience floor": "resilienceFloor",
                    }.get(label, "overallScore")
                ],
                row["legislature"],
                row["review"],
                row["antiCapture"],
            ]
            for label, row in diagnostic_rows
        ],
    )
    profile_table = markdown_table(
        ["Profile", "Winner Score", "Balanced Rank", "Legislature", "Review", "Anti-capture"],
        profile_winner_rows(portfolios),
    )
    robust_table = markdown_table(
        [
            "Robust Rank",
            "Robust Score",
            "Avg Profile Rank",
            "Worst Rank",
            "Top-25 Profiles",
            "Balanced Rank",
            "Legislature",
            "Review",
            "Anti-capture",
        ],
        [
            [
                row["robustRank"],
                row["robustScore"],
                row["averageProfileRank"],
                row["worstProfileRank"],
                row["top25ProfileCount"],
                row["rank"],
                row["legislature"],
                row["review"],
                row["antiCapture"],
            ]
            for row in robust_rows[:15]
        ],
    )
    uncertainty_table = markdown_table(
        [
            "Lower-Bound Rank",
            "Balanced Rank",
            "Score",
            "Interval",
            "Dominance Rank",
            "Balanced Relation",
            "Legislature",
            "Review",
            "Anti-capture",
        ],
        [
            [
                row["uncertaintyLowerBoundRank"],
                row["balancedRank"],
                row["overallScore"],
                f"{row['uncertaintyLow']}-{row['uncertaintyHigh']}",
                row["uncertaintyDominanceRank"],
                row["balancedIntervalRelation"],
                row["legislature"],
                row["review"],
                row["antiCapture"],
            ]
            for row in uncertainty_rows[:10]
        ],
    )
    pareto_table = markdown_table(
        ["Pareto Rank", "Balanced Rank", "Score", "Delivery", "Rights", "Capture", "Complexity", "Legislature", "Review", "Anti-capture"],
        [
            [
                row["paretoRank"],
                row["rank"],
                row["overallScore"],
                row["policyDelivery"],
                row["rightsSafeguard"],
                row["captureResistance"],
                row["complexityScore"],
                row["legislature"],
                row["review"],
                row["antiCapture"],
            ]
            for row in pareto_rows[:15]
        ],
    )
    regret_table = markdown_table(
        ["Regret Rank", "Max Regret", "Avg Regret", "Balanced Rank", "Score", "Legislature", "Review", "Anti-capture"],
        [
            [
                row["minimaxRegretRank"],
                row["maxProfileRegret"],
                row["averageProfileRegret"],
                row["rank"],
                row["overallScore"],
                row["legislature"],
                row["review"],
                row["antiCapture"],
            ]
            for row in regret_rows[:10]
        ],
    )
    tradeoff_table = markdown_table(
        ["Case", "Balanced Rank", "Regret Rank", "Max Regret", "Uncertainty", "Floor", "Legislature", "Review", "Anti-capture"],
        [
            [
                row["caseLabels"],
                row["balancedRank"],
                row["minimaxRegretRank"],
                row["maxProfileRegret"],
                row["modelUncertaintyBand"],
                row["resilienceFloor"],
                row["legislature"],
                row["review"],
                row["antiCapture"],
            ]
            for row in tradeoff_rows
        ],
    )
    fragile_table = markdown_table(
        ["Rank", "Score", "Regret Rank", "Portfolio", "Reason"],
        [
            [
                row["balancedRank"],
                row["balancedScore"],
                row["minimaxRegretRank"],
                f"{row['legislature']} + {row['review']} + {row['antiCapture']}",
                row["doNotRecommendYetReason"],
            ]
            for row in fragile_rows[:10]
        ],
    )
    component_sections: list[str] = []
    for kind, options in options_by_kind.items():
        component_sections.append(f"### {kind.replace('_', ' ').title()}")
        component_sections.append(
            markdown_table(
                ["Rank", "Score", "Scenario", "Rows", "Metrics"],
                [
                    [rank, option["score"], option["scenarioName"], option["rowCount"], option["metricCoverage"]]
                    for rank, option in enumerate(options[:10], start=1)
                ],
            )
        )

    text = f"""# Cumulative Government Portfolio Report

Generated: `{generated_at}`

This report combines existing simulator campaign outputs into institutional portfolios. It is a synthesis tool, not an empirical claim that the top row is objectively the best possible government.

## Source Inventory

{source_table}

## Top Portfolios

{portfolio_table}

## Diagnostic Winners

{diagnostic_table}

## Profile Winners

{profile_table}

## Minimax-Regret Ranking

{regret_table}

## Uncertainty-Aware Ranking

{uncertainty_table}

## Focused Profile Tradeoffs

{tradeoff_table}

## Robust Cross-Profile Portfolios

{robust_table}

## Do Not Recommend Yet

{fragile_table}

## Pareto Front Preview

Exact Pareto-front size: `{len(pareto_rows)}` of `{len(portfolios)}` portfolios.

Epsilon-Pareto front size: `{len(epsilon_pareto_rows)}` of `{len(portfolios)}` portfolios.

Uncertainty-aware Pareto front size: `{len(uncertainty_pareto_rows)}` of `{len(portfolios)}` portfolios.

{pareto_table}

## Top Components

{chr(10).join(component_sections)}

## Reading Notes

- `Score` is a weighted portfolio score over delivery, public alignment, rights safeguards, capture resistance, legitimacy, efficiency, and resilience.
- `Complexity` is scored positively, so a higher value means lower modeled administrative and institutional complexity.
- The `resilienceFloor` used in the CSV is conservative: it is the weakest major subsystem or safeguard score in the bundle.
- Uncertainty bands are synthetic model-sensitivity bands, not empirical confidence intervals.
- Lower-bound and interval-dominance ranks are uncertainty-aware diagnostics; they should not be collapsed back into a point-estimate winner.
- Minimax regret asks how far a portfolio falls behind the best row under its weakest scoring profile.
- Profile winners show how the result changes under alternate normative priorities.
- Exact Pareto rows use point estimates; epsilon and uncertainty-aware fronts are generated separately because exact dominance is too brittle under broad synthetic bands.
- Strong rows should be read as candidates for closer argument in `paper/main.tex`, not as final constitutional recommendations.
"""
    path.write_text(text, encoding="utf-8")


def source_config_for_kind(sources: list[SourceConfig], kind: str) -> SourceConfig:
    for source in sources:
        if source.kind == kind:
            return source
    raise KeyError(kind)


def csv_columns(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Missing source CSV: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or [])


def source_fieldnames(path: Path) -> set[str]:
    rows = read_csv(path)
    if not rows:
        return set()
    return set(rows[0].keys())


def metric_by_column(metrics: list[MetricSpec]) -> dict[str, MetricSpec]:
    return {metric.column: metric for metric in metrics}


def review_source_meta(source: SourceConfig) -> dict[str, str]:
    return REVIEW_SOURCE_METADATA.get(
        source.label,
        {
            "prefix": source.label.lower().replace(" ", "-"),
            "project": source.label,
            "denominator": "scenario-level source mean with source-native case weighting where available",
        },
    )


def harmonized_review_source_config(path: Path) -> SourceConfig:
    return SourceConfig(
        kind="review",
        label="Harmonized review source",
        path=path,
        key_column="scenarioKey",
        name_column="scenario",
        metrics=HARMONIZED_REVIEW_METRICS,
    )


def review_reconciliation_rows(imported_review: SourceConfig, companion_review: SourceConfig) -> list[dict[str, object]]:
    imported_rows = read_csv(imported_review.path)
    companion_rows = read_csv(companion_review.path)
    imported_columns = set(csv_columns(imported_review.path))
    companion_columns = set(csv_columns(companion_review.path))
    rows: list[dict[str, object]] = []

    for spec in REVIEW_METRICS:
        imported_present = spec.column in imported_columns
        companion_present = spec.column in companion_columns
        if imported_present and companion_present:
            status = "shared configured metric"
            static_eligibility = "candidate after denominator check"
            adaptive_eligibility = "possible dynamic input if period meaning is defined"
            denominator_risk = "medium"
            recommendation = "Map denominators before treating score differences as substantive."
        elif imported_present:
            status = "imported-only configured metric"
            static_eligibility = "current static metric only"
            adaptive_eligibility = "not available in companion review source"
            denominator_risk = "high"
            recommendation = "Do not impute into companion run without source-level construct mapping."
        elif companion_present:
            status = "companion-only configured metric"
            static_eligibility = "candidate static metric after mapping"
            adaptive_eligibility = "possible dynamic input"
            denominator_risk = "high"
            recommendation = "Eligible for harmonized review only after matching scale and construct ownership."
        else:
            status = "missing from both review sources"
            static_eligibility = "not eligible"
            adaptive_eligibility = "not eligible"
            denominator_risk = "blocking"
            recommendation = "Remove or replace before a harmonized review run."
        rows.append(
            {
                "construct": spec.column,
                "importedColumn": spec.column if imported_present else "",
                "companionColumn": spec.column if companion_present else "",
                "importedPresent": imported_present,
                "companionPresent": companion_present,
                "importedRows": len(imported_rows),
                "companionRows": len(companion_rows),
                "direction": spec.direction,
                "weight": spec.weight,
                "comparisonStatus": status,
                "staticScoreEligibility": static_eligibility,
                "adaptiveInputEligibility": adaptive_eligibility,
                "denominatorRisk": denominator_risk,
                "recommendation": recommendation,
            }
        )

    for column, (direction, note) in REVIEW_ADAPTIVE_CANDIDATE_COLUMNS.items():
        if column not in companion_columns:
            continue
        imported_present = column in imported_columns
        rows.append(
            {
                "construct": column,
                "importedColumn": column if imported_present else "",
                "companionColumn": column,
                "importedPresent": imported_present,
                "companionPresent": True,
                "importedRows": len(imported_rows),
                "companionRows": len(companion_rows),
                "direction": direction,
                "weight": "",
                "comparisonStatus": "companion adaptive candidate",
                "staticScoreEligibility": "do not add to static score yet",
                "adaptiveInputEligibility": note,
                "denominatorRisk": "requires calibration",
                "recommendation": "Map as Adaptive Bridge or stress input before using it as a ranking metric.",
            }
        )
    return rows


def write_review_reconciliation_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "construct",
        "importedColumn",
        "companionColumn",
        "importedPresent",
        "companionPresent",
        "importedRows",
        "companionRows",
        "direction",
        "weight",
        "comparisonStatus",
        "staticScoreEligibility",
        "adaptiveInputEligibility",
        "denominatorRisk",
        "recommendation",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fmt(row.get(field, "")) for field in fieldnames})


def write_review_reconciliation_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    configured_rows = [row for row in rows if row["comparisonStatus"] != "companion adaptive candidate"]
    adaptive_rows = [row for row in rows if row["comparisonStatus"] == "companion adaptive candidate"]
    counts = {
        "shared configured metric": sum(1 for row in configured_rows if row["comparisonStatus"] == "shared configured metric"),
        "imported-only configured metric": sum(1 for row in configured_rows if row["comparisonStatus"] == "imported-only configured metric"),
        "companion-only configured metric": sum(1 for row in configured_rows if row["comparisonStatus"] == "companion-only configured metric"),
        "missing from both review sources": sum(1 for row in configured_rows if row["comparisonStatus"] == "missing from both review sources"),
        "companion adaptive candidate": len(adaptive_rows),
    }
    text = f"""# Review Source Reconciliation

Generated: `{generated_at}`

This report compares the imported Supreme Court Simulator Design review source with the companion Constitutional Review Simulator source. It is a schema and construct audit, not a claim that the two sources can be merged.

## Summary

{markdown_table(["Category", "Count"], [[key, value] for key, value in counts.items()])}

## Configured Static Review Metrics

{markdown_table(
    ["Construct", "Imported", "Companion", "Status", "Static eligibility", "Denominator risk"],
    [
        [
            row["construct"],
            row["importedPresent"],
            row["companionPresent"],
            row["comparisonStatus"],
            row["staticScoreEligibility"],
            row["denominatorRisk"],
        ]
        for row in configured_rows
    ],
)}

## Companion Adaptive Candidates

{markdown_table(
    ["Construct", "Direction", "Adaptive use", "Recommendation"],
    [
        [row["construct"], row["direction"], row["adaptiveInputEligibility"], row["recommendation"]]
        for row in adaptive_rows
    ],
)}
"""
    path.write_text(text, encoding="utf-8")


def review_harmonization_manifest_rows(
    imported_review: SourceConfig,
    companion_review: SourceConfig,
) -> list[dict[str, object]]:
    imported_fields = source_fieldnames(imported_review.path)
    companion_fields = source_fieldnames(companion_review.path)
    configured = metric_by_column(REVIEW_METRICS)
    harmonized = metric_by_column(HARMONIZED_REVIEW_METRICS)
    rows: list[dict[str, object]] = []

    for source, fields in [(imported_review, imported_fields), (companion_review, companion_fields)]:
        meta = review_source_meta(source)
        for column, spec in configured.items():
            present = column in fields
            shared = column in imported_fields and column in companion_fields
            included = column in harmonized and present
            if included:
                static_eligibility = "included in harmonized static source"
                adaptive_eligibility = "not primary adaptive input; available as static review construct"
                relationship = "supplements existing metric with same name and direction in both review sources"
                action = "included"
                rationale = "Same column exists in both review sources with compatible 0-1 interpretation and direction."
            elif shared:
                static_eligibility = "deferred despite shared name"
                adaptive_eligibility = "possible sensitivity input after denominator review"
                relationship = "supplements but not yet harmonized"
                action = "deferred"
                rationale = "Column exists in both sources but is not in the conservative harmonized subset."
            elif present:
                static_eligibility = "source-specific only; excluded from harmonized static source"
                adaptive_eligibility = "possible source-specific sensitivity input"
                relationship = "conflicts with harmonized static scope until source ownership is assigned"
                action = "excluded"
                rationale = "Column is present in this source only, so using it would give that source an unmatched static-score advantage."
            else:
                static_eligibility = "not present in this source"
                adaptive_eligibility = "not available from this source"
                relationship = "missing relative to configured review metric"
                action = "not present"
                rationale = "Configured metric is absent from this source."

            rows.append(
                {
                    "metricName": column,
                    "sourceProject": meta["project"],
                    "sourceColumn": column if present else "",
                    "denominator": meta["denominator"],
                    "direction": spec.direction,
                    "weight": spec.weight,
                    "staticScoreEligibility": static_eligibility,
                    "adaptiveInputEligibility": adaptive_eligibility,
                    "relationshipToExistingMetric": relationship,
                    "harmonizedColumn": column if included else "",
                    "harmonizedAction": action,
                    "rationale": rationale,
                }
            )

    for column, (direction, note) in REVIEW_ADAPTIVE_CANDIDATE_COLUMNS.items():
        present = column in companion_fields
        rows.append(
            {
                "metricName": column,
                "sourceProject": review_source_meta(companion_review)["project"],
                "sourceColumn": column if present else "",
                "denominator": review_source_meta(companion_review)["denominator"],
                "direction": direction,
                "weight": "",
                "staticScoreEligibility": "not eligible for static harmonized source",
                "adaptiveInputEligibility": "eligible adaptive-input candidate after coefficient validation" if present else "not present",
                "relationshipToExistingMetric": "supplements adaptive bridge rather than replacing static review score",
                "harmonizedColumn": "",
                "harmonizedAction": "adaptive candidate",
                "rationale": note,
            }
        )
    return rows


def write_review_harmonization_manifest_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "metricName",
        "sourceProject",
        "sourceColumn",
        "denominator",
        "direction",
        "weight",
        "staticScoreEligibility",
        "adaptiveInputEligibility",
        "relationshipToExistingMetric",
        "harmonizedColumn",
        "harmonizedAction",
        "rationale",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fmt(row.get(field, "")) for field in fieldnames})


def write_review_harmonization_manifest_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    counts: dict[str, int] = {}
    for row in rows:
        key = str(row["harmonizedAction"])
        counts[key] = counts.get(key, 0) + 1
    included = [row for row in rows if row["harmonizedAction"] == "included"]
    body = f"""# Review Harmonization Manifest

Generated: `{generated_at}`

This manifest separates comparable static review fields from source-specific metrics and adaptive candidates. The harmonized source is intentionally conservative: it includes only fields with the same column name, direction, and defensible 0-1 scenario interpretation in both review projects.

## Action Counts

{markdown_table(["Action", "Count"], [[key, value] for key, value in sorted(counts.items())])}

## Included Harmonized Static Fields

{markdown_table(
        ["Metric", "Source", "Direction", "Denominator"],
        [
            [row["metricName"], row["sourceProject"], row["direction"], row["denominator"]]
            for row in included
        ],
    )}
"""
    path.write_text(body, encoding="utf-8")


def write_harmonized_review_source_csv(
    path: Path,
    imported_review: SourceConfig,
    companion_review: SourceConfig,
) -> dict[str, object]:
    fieldnames = [
        "sourceProject",
        "sourceScenarioKey",
        "sourceCaseKey",
        "caseKey",
        "caseName",
        "caseWeight",
        "scenarioKey",
        "scenario",
        *[metric.column for metric in HARMONIZED_REVIEW_METRICS],
    ]
    rows_out: list[dict[str, object]] = []

    for source in [imported_review, companion_review]:
        meta = review_source_meta(source)
        prefix = meta["prefix"]
        for row in read_csv(source.path):
            source_scenario_key = row.get(source.key_column, "").strip().strip('"')
            if not source_scenario_key:
                continue
            scenario = row.get(source.name_column, source_scenario_key).strip().strip('"') or source_scenario_key
            case_key = row.get("caseKey", source_scenario_key).strip().strip('"') or source_scenario_key
            case_name = row.get("caseName", case_key).strip().strip('"') or case_key
            output: dict[str, object] = {
                "sourceProject": meta["project"],
                "sourceScenarioKey": source_scenario_key,
                "sourceCaseKey": case_key,
                "caseKey": f"{prefix}__{case_key}",
                "caseName": f"{meta['project']}: {case_name}",
                "caseWeight": row.get("caseWeight", "").strip() or "1.0",
                "scenarioKey": f"{prefix}__{source_scenario_key}",
                "scenario": f"{meta['project']}: {scenario}",
            }
            for metric in HARMONIZED_REVIEW_METRICS:
                output[metric.column] = row.get(metric.column, "").strip()
            if any(output[metric.column] != "" for metric in HARMONIZED_REVIEW_METRICS):
                rows_out.append(output)

    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows_out:
            writer.writerow({field: row.get(field, "") for field in fieldnames})

    return {
        "rows": len(rows_out),
        "scenarioCount": len({row["scenarioKey"] for row in rows_out}),
        "configuredMetricCount": len(HARMONIZED_REVIEW_METRICS),
        "metricColumnsConfigured": [metric.column for metric in HARMONIZED_REVIEW_METRICS],
        "path": str(path),
    }


def run_review_variant(
    review_source: SourceConfig,
    options_by_kind: dict[str, list[dict[str, object]]],
    metric_counts: dict[str, int],
) -> tuple[list[dict[str, object]], dict[str, object], list[dict[str, object]]]:
    review_options, review_inventory = aggregate_source(review_source)
    variant_options = dict(options_by_kind)
    variant_options["review"] = review_options
    variant_portfolios = build_portfolios(variant_options, metric_counts)
    return variant_portfolios, review_inventory, review_options


def canonical_review_key(value: object) -> str:
    text = str(value)
    for prefix in ("scd__", "crs__"):
        if text.startswith(prefix):
            return text[len(prefix):]
    return text


def canonical_portfolio_key(row: dict[str, object]) -> tuple[str, str, str]:
    return (
        str(row["legislatureKey"]),
        canonical_review_key(row["reviewKey"]),
        str(row["antiCaptureKey"]),
    )


def portfolio_rank_map(portfolios: list[dict[str, object]]) -> dict[tuple[object, object, object], int]:
    return {portfolio_key(row): int(row["rank"]) for row in portfolios}


def canonical_rank_map(portfolios: list[dict[str, object]]) -> dict[tuple[str, str, str], int]:
    ranks: dict[tuple[str, str, str], int] = {}
    for row in portfolios:
        key = canonical_portfolio_key(row)
        rank = int(row["rank"])
        if key not in ranks or rank < ranks[key]:
            ranks[key] = rank
    return ranks


def average_metric_coverage(options: list[dict[str, object]]) -> float:
    if not options:
        return 0.0
    return sum(float(option["metricCoverage"]) for option in options) / len(options)


def dual_review_sensitivity_rows(
    primary_review_source: SourceConfig,
    primary_portfolios: list[dict[str, object]],
    primary_review_options: list[dict[str, object]],
    companion_review_source: SourceConfig,
    companion_portfolios: list[dict[str, object]],
    companion_inventory: dict[str, object],
    companion_review_options: list[dict[str, object]],
    harmonized_review_source: SourceConfig,
    harmonized_portfolios: list[dict[str, object]],
    harmonized_inventory: dict[str, object],
    harmonized_review_options: list[dict[str, object]],
) -> list[dict[str, object]]:
    def winner_text(row: dict[str, object]) -> str:
        return f"{row['legislature']} + {row['review']} + {row['antiCapture']}"

    primary_inventory = {
        "rows": len(read_csv(primary_review_source.path)),
        "scenarioCount": len(primary_review_options),
        "configuredMetricCount": len(primary_review_source.metrics),
    }

    primary_ranks = canonical_rank_map(primary_portfolios)
    primary_winner = primary_portfolios[0]
    primary_winner_key = canonical_portfolio_key(primary_winner)
    primary_top25 = {canonical_portfolio_key(row) for row in primary_portfolios[:25]}
    primary_top100 = {canonical_portfolio_key(row) for row in primary_portfolios[:100]}

    variants = [
        (
            "current-imported-review",
            primary_review_source,
            primary_portfolios,
            primary_inventory,
            primary_review_options,
            "Current ranking source.",
        ),
        (
            "companion-review-first-pass",
            companion_review_source,
            companion_portfolios,
            companion_inventory,
            companion_review_options,
            "First-pass source swap; missing configured fields are skipped, not imputed.",
        ),
        (
            "harmonized-review-source",
            harmonized_review_source,
            harmonized_portfolios,
            harmonized_inventory,
            harmonized_review_options,
            "Conservative harmonized source using only shared same-direction static review fields from both review projects.",
        ),
    ]

    rows: list[dict[str, object]] = []
    for run_key, source, portfolios, inventory, review_options, notes in variants:
        ranks = canonical_rank_map(portfolios)
        top25 = {canonical_portfolio_key(row) for row in portfolios[:25]}
        top100 = {canonical_portfolio_key(row) for row in portfolios[:100]}
        winner = portfolios[0]
        winner_key = canonical_portfolio_key(winner)
        rows.append(
            {
                "runKey": run_key,
                "status": "completed",
                "reviewSource": source.label,
                "reviewPath": str(source.path),
                "reviewRows": inventory["rows"],
                "reviewScenarios": inventory["scenarioCount"],
                "portfolioCount": len(portfolios),
                "balancedWinner": winner_text(winner),
                "balancedWinnerKey": "|".join(str(part) for part in portfolio_key(winner)),
                "canonicalWinnerKey": "|".join(winner_key),
                "balancedScore": winner["overallScore"],
                "top25OverlapWithPrimary": len(primary_top25 & top25),
                "top100OverlapWithPrimary": len(primary_top100 & top100),
                "sharedPortfolioCountWithPrimary": len(set(primary_ranks) & set(ranks)),
                "primaryWinnerRankInRun": ranks.get(primary_winner_key, "not comparable"),
                "runWinnerRankInPrimary": primary_ranks.get(winner_key, "not comparable"),
                "averageReviewMetricCoverage": average_metric_coverage(review_options),
                "configuredMetricCount": inventory["configuredMetricCount"],
                "rankComparisonBasis": "canonical legislature/review/anti-capture keys with harmonized source prefixes stripped",
                "notes": notes,
            }
        )
    return rows


def review_variant_overlap_rows(variants: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    keys = list(variants)
    for index, left_key in enumerate(keys):
        for right_key in keys[index + 1:]:
            left = variants[left_key]
            right = variants[right_key]
            left_top25 = {canonical_portfolio_key(row) for row in left[:25]}
            right_top25 = {canonical_portfolio_key(row) for row in right[:25]}
            left_top100 = {canonical_portfolio_key(row) for row in left[:100]}
            right_top100 = {canonical_portfolio_key(row) for row in right[:100]}
            left_all = {canonical_portfolio_key(row) for row in left}
            right_all = {canonical_portfolio_key(row) for row in right}
            rows.append(
                {
                    "leftRunKey": left_key,
                    "rightRunKey": right_key,
                    "top25Overlap": len(left_top25 & right_top25),
                    "top100Overlap": len(left_top100 & right_top100),
                    "sharedCanonicalPortfolioCount": len(left_all & right_all),
                    "leftPortfolioCount": len(left),
                    "rightPortfolioCount": len(right),
                    "comparisonBasis": "canonical portfolio keys; source prefixes stripped for harmonized review rows",
                }
            )
    return rows


def review_variant_rank_shift_rows(
    current: list[dict[str, object]],
    companion: list[dict[str, object]],
    harmonized: list[dict[str, object]],
) -> list[dict[str, object]]:
    variant_rows = {
        "current-imported-review": current,
        "companion-review-first-pass": companion,
        "harmonized-review-source": harmonized,
    }
    rank_maps = {key: canonical_rank_map(rows) for key, rows in variant_rows.items()}
    top_union: set[tuple[str, str, str]] = set()
    display: dict[tuple[str, str, str], dict[str, object]] = {}
    for rows in variant_rows.values():
        for row in rows[:25]:
            key = canonical_portfolio_key(row)
            top_union.add(key)
            display.setdefault(key, row)

    def rank_or_blank(run_key: str, key: tuple[str, str, str]) -> int | str:
        return rank_maps[run_key].get(key, "")

    def delta(left: int | str, right: int | str) -> int | str:
        if isinstance(left, int) and isinstance(right, int):
            return left - right
        return ""

    rows_out: list[dict[str, object]] = []
    for key in sorted(top_union, key=lambda item: min(rank for ranks in rank_maps.values() if (rank := ranks.get(item)) is not None)):
        row = display[key]
        current_rank = rank_or_blank("current-imported-review", key)
        companion_rank = rank_or_blank("companion-review-first-pass", key)
        harmonized_rank = rank_or_blank("harmonized-review-source", key)
        rows_out.append(
            {
                "canonicalPortfolioKey": "|".join(key),
                "legislature": row["legislature"],
                "review": row["review"],
                "antiCapture": row["antiCapture"],
                "currentRank": current_rank,
                "companionRank": companion_rank,
                "harmonizedRank": harmonized_rank,
                "companionMinusCurrent": delta(companion_rank, current_rank),
                "harmonizedMinusCurrent": delta(harmonized_rank, current_rank),
                "bestObservedRank": min(
                    rank for rank in [current_rank, companion_rank, harmonized_rank] if isinstance(rank, int)
                ),
            }
        )
    return rows_out


def write_dual_review_sensitivity_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "runKey",
        "status",
        "reviewSource",
        "reviewPath",
        "reviewRows",
        "reviewScenarios",
        "portfolioCount",
        "balancedWinner",
        "balancedWinnerKey",
        "canonicalWinnerKey",
        "balancedScore",
        "top25OverlapWithPrimary",
        "top100OverlapWithPrimary",
        "sharedPortfolioCountWithPrimary",
        "primaryWinnerRankInRun",
        "runWinnerRankInPrimary",
        "averageReviewMetricCoverage",
        "configuredMetricCount",
        "rankComparisonBasis",
        "notes",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fmt(row.get(field, "")) for field in fieldnames})


def write_dual_review_sensitivity_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    text = f"""# Review Variant Sensitivity

Generated: `{generated_at}`

This report compares the current imported constitutional-review source, the companion Constitutional Review Simulator source swap, and a conservative harmonized review source. Rank comparisons use canonical portfolio keys with harmonized source prefixes stripped; they remain sensitivity screens, not empirical validation.

{markdown_table(
    [
        "Run",
        "Status",
        "Review source",
        "Scenarios",
        "Portfolios",
        "Score",
        "Top-25 overlap",
        "Primary winner rank",
        "Run winner primary rank",
        "Notes",
    ],
    [
        [
            row["runKey"],
            row["status"],
            row["reviewSource"],
            row["reviewScenarios"],
            row["portfolioCount"],
            row["balancedScore"],
            row["top25OverlapWithPrimary"],
            row["primaryWinnerRankInRun"],
            row["runWinnerRankInPrimary"],
            row["notes"],
        ]
        for row in rows
    ],
)}

## Winners

{markdown_table(
    ["Run", "Balanced winner"],
    [[row["runKey"], row["balancedWinner"]] for row in rows if row["balancedWinner"]],
)}
"""
    path.write_text(text, encoding="utf-8")


def write_review_variant_overlap_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "leftRunKey",
        "rightRunKey",
        "top25Overlap",
        "top100Overlap",
        "sharedCanonicalPortfolioCount",
        "leftPortfolioCount",
        "rightPortfolioCount",
        "comparisonBasis",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fmt(row.get(field, "")) for field in fieldnames})


def write_review_variant_overlap_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    body = f"""# Review Variant Top-List Overlap

Generated: `{generated_at}`

{markdown_table(
        ["Left run", "Right run", "Top-25 overlap", "Top-100 overlap", "Shared canonical portfolios"],
        [
            [
                row["leftRunKey"],
                row["rightRunKey"],
                row["top25Overlap"],
                row["top100Overlap"],
                row["sharedCanonicalPortfolioCount"],
            ]
            for row in rows
        ],
    )}
"""
    path.write_text(body, encoding="utf-8")


def write_review_variant_rank_shift_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "canonicalPortfolioKey",
        "legislature",
        "review",
        "antiCapture",
        "currentRank",
        "companionRank",
        "harmonizedRank",
        "companionMinusCurrent",
        "harmonizedMinusCurrent",
        "bestObservedRank",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: fmt(row.get(field, "")) for field in fieldnames})


def write_review_variant_rank_shift_markdown(path: Path, rows: list[dict[str, object]]) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    body = f"""# Review Variant Rank Shifts

Generated: `{generated_at}`

This table tracks the union of the top 25 canonical portfolios from the current, companion, and harmonized review variants. Blank rank cells mean the canonical review scenario is not available in that variant.

{markdown_table(
        ["Current", "Companion", "Harmonized", "Comp.-cur.", "Harm.-cur.", "Portfolio"],
        [
            [
                row["currentRank"],
                row["companionRank"],
                row["harmonizedRank"],
                row["companionMinusCurrent"],
                row["harmonizedMinusCurrent"],
                f"{row['legislature']} + {row['review']} + {row['antiCapture']}",
            ]
            for row in rows[:40]
        ],
    )}
"""
    path.write_text(body, encoding="utf-8")


def write_inventory(path: Path, inventory: list[dict[str, object]]) -> None:
    payload = {
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "sources": inventory,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = resolved(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources = apply_overrides(default_sources(), args)
    options_by_kind: dict[str, list[dict[str, object]]] = {}
    inventories: list[dict[str, object]] = []
    for source in sources:
        options, inventory = aggregate_source(source)
        if not options:
            raise RuntimeError(f"No scorable scenarios found for {source.label}: {source.path}")
        options_by_kind[source.kind] = options
        inventories.append(inventory)

    metric_counts = {source.kind: len(source.metrics) for source in sources}
    primary_review_source = source_config_for_kind(sources, "review")
    portfolios = build_portfolios(options_by_kind, metric_counts)
    review_reconciliation = review_reconciliation_rows(primary_review_source, COMPANION_REVIEW_SOURCE)
    review_harmonization_manifest = review_harmonization_manifest_rows(primary_review_source, COMPANION_REVIEW_SOURCE)
    harmonized_review_path = output_dir / "harmonized-review-source.csv"
    write_harmonized_review_source_csv(harmonized_review_path, primary_review_source, COMPANION_REVIEW_SOURCE)
    harmonized_review_source = harmonized_review_source_config(harmonized_review_path)
    companion_portfolios, companion_review_inventory, companion_review_options = run_review_variant(
        COMPANION_REVIEW_SOURCE,
        options_by_kind,
        metric_counts,
    )
    harmonized_metric_counts = dict(metric_counts)
    harmonized_metric_counts["review"] = len(HARMONIZED_REVIEW_METRICS)
    harmonized_portfolios, harmonized_review_inventory, harmonized_review_options = run_review_variant(
        harmonized_review_source,
        options_by_kind,
        harmonized_metric_counts,
    )
    dual_review_rows = dual_review_sensitivity_rows(
        primary_review_source,
        portfolios,
        options_by_kind["review"],
        COMPANION_REVIEW_SOURCE,
        companion_portfolios,
        companion_review_inventory,
        companion_review_options,
        harmonized_review_source,
        harmonized_portfolios,
        harmonized_review_inventory,
        harmonized_review_options,
    )
    review_overlap_rows = review_variant_overlap_rows(
        {
            "current-imported-review": portfolios,
            "companion-review-first-pass": companion_portfolios,
            "harmonized-review-source": harmonized_portfolios,
        }
    )
    review_rank_shift_rows = review_variant_rank_shift_rows(
        portfolios,
        companion_portfolios,
        harmonized_portfolios,
    )
    robust = robustness_rows(portfolios)
    pareto = pareto_front(portfolios, "paretoRank", "exact")
    epsilon_pareto = pareto_front(portfolios, "epsilonParetoRank", "epsilon")
    uncertainty_pareto = pareto_front(portfolios, "uncertaintyParetoRank", "uncertainty")
    regret = sorted(portfolios, key=lambda row: int(row["minimaxRegretRank"]))
    tradeoffs = focused_tradeoff_rows(portfolios, robust)
    fragile = fragile_watchlist_rows(portfolios)
    uncertainty_rows = uncertainty_tier_rows(portfolios)
    write_component_scores(output_dir / "component-scores.csv", options_by_kind)
    write_portfolio_csv(output_dir / "cumulative-government-portfolios.csv", portfolios)
    write_profile_sensitivity_csv(output_dir / "profile-sensitivity.csv", portfolios)
    write_profile_sensitivity_markdown(output_dir / "profile-sensitivity.md", portfolios, min(10, args.top))
    write_robustness_csv(output_dir / "portfolio-robustness.csv", robust)
    write_robustness_markdown(output_dir / "portfolio-robustness.md", robust, args.top)
    write_minimax_regret_csv(output_dir / "portfolio-minimax-regret.csv", portfolios)
    write_minimax_regret_markdown(output_dir / "portfolio-minimax-regret.md", portfolios, args.top)
    write_profile_tradeoffs_csv(output_dir / "portfolio-profile-tradeoffs.csv", tradeoffs)
    write_profile_tradeoffs_markdown(output_dir / "portfolio-profile-tradeoffs.md", tradeoffs)
    write_fragile_watchlist_csv(output_dir / "fragile-portfolio-watchlist.csv", fragile)
    write_fragile_watchlist_markdown(output_dir / "fragile-portfolio-watchlist.md", fragile, args.top)
    write_uncertainty_tiers_csv(output_dir / "portfolio-uncertainty-tiers.csv", uncertainty_rows)
    write_uncertainty_tiers_markdown(output_dir / "portfolio-uncertainty-tiers.md", portfolios, uncertainty_rows, args.top)
    write_research_agenda_markdown(output_dir / "speculative-modeling-agenda.md")
    write_review_reconciliation_csv(output_dir / "review-source-reconciliation.csv", review_reconciliation)
    write_review_reconciliation_markdown(output_dir / "review-source-reconciliation.md", review_reconciliation)
    write_review_harmonization_manifest_csv(
        output_dir / "review-harmonization-manifest.csv",
        review_harmonization_manifest,
    )
    write_review_harmonization_manifest_markdown(
        output_dir / "review-harmonization-manifest.md",
        review_harmonization_manifest,
    )
    write_dual_review_sensitivity_csv(output_dir / "dual-review-sensitivity.csv", dual_review_rows)
    write_dual_review_sensitivity_markdown(output_dir / "dual-review-sensitivity.md", dual_review_rows)
    write_review_variant_overlap_csv(output_dir / "review-variant-overlap.csv", review_overlap_rows)
    write_review_variant_overlap_markdown(output_dir / "review-variant-overlap.md", review_overlap_rows)
    write_review_variant_rank_shift_csv(output_dir / "review-variant-rank-shifts.csv", review_rank_shift_rows)
    write_review_variant_rank_shift_markdown(output_dir / "review-variant-rank-shifts.md", review_rank_shift_rows)
    write_pareto_csv(output_dir / "pareto-front.csv", pareto, "paretoRank", "exact")
    write_pareto_markdown(
        output_dir / "pareto-front.md",
        pareto,
        len(portfolios),
        args.top,
        "paretoRank",
        "exact",
        "This point-estimate front excludes a portfolio when another portfolio is at least as good on every listed dimension and better on at least one.",
    )
    write_pareto_csv(output_dir / "pareto-front-epsilon.csv", epsilon_pareto, "epsilonParetoRank", "epsilon")
    write_pareto_markdown(
        output_dir / "pareto-front-epsilon.md",
        epsilon_pareto,
        len(portfolios),
        args.top,
        "epsilonParetoRank",
        "epsilon",
        f"This front uses an epsilon margin of {EPSILON_PARETO_MARGIN:.3f}; tiny point-estimate advantages are not treated as meaningful dominance.",
    )
    write_pareto_csv(
        output_dir / "pareto-front-uncertainty.csv",
        uncertainty_pareto,
        "uncertaintyParetoRank",
        "uncertainty",
    )
    write_pareto_markdown(
        output_dir / "pareto-front-uncertainty.md",
        uncertainty_pareto,
        len(portfolios),
        args.top,
        "uncertaintyParetoRank",
        "uncertainty",
        "This front requires dominance large enough to survive the synthetic model-sensitivity bands, so it should be read as a conservative exclusion test.",
    )
    write_markdown_report(
        output_dir / "cumulative-government-portfolios.md",
        portfolios,
        robust,
        pareto,
        epsilon_pareto,
        uncertainty_pareto,
        regret,
        tradeoffs,
        fragile,
        uncertainty_rows,
        options_by_kind,
        inventories,
        args.top,
    )
    write_inventory(output_dir / "source-inventory.json", inventories)

    if not args.quiet:
        best = portfolios[0]
        print(f"Wrote {len(portfolios)} portfolios to {output_dir}")
        print(f"Exact Pareto front: {len(pareto)} portfolios")
        print(f"Epsilon Pareto front: {len(epsilon_pareto)} portfolios")
        print(f"Uncertainty-aware Pareto front: {len(uncertainty_pareto)} portfolios")
        print(
            "Best: "
            f"{best['legislature']} + {best['review']} + {best['antiCapture']} "
            f"({float(best['overallScore']):.3f})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
