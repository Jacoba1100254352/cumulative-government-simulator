#!/usr/bin/env python3
"""Generate LaTeX paper fragments from current report artifacts."""

from __future__ import annotations

import csv
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = Path(os.environ.get("REPORTS_DIR", ROOT / "reports"))
GENERATED = Path(os.environ.get("PAPER_GENERATED_DIR", ROOT / "paper" / "generated"))
SIMULATORS_ROOT = ROOT.parent


DIAGNOSTIC_FORMULAS = [
    (
        "Policy delivery",
        "Mean of legislature productivity, welfare, public alignment, inverse gridlock, and inverse time-to-correct-bad-law when available.",
    ),
    (
        "Public alignment",
        "Mean of legislative representative quality, legislative public alignment, legislative and review democratic responsiveness, anti-capture representation, and anti-capture public interest.",
    ),
    (
        "Rights safeguard",
        "Mean of review rights protection, legal stability, stability-rights score, inverse shadow-docket abuse, inverse emergency legitimacy risk, inverse constitutional conflict, inverse weak public-mandate passage, and inverse concentrated-harm passage.",
    ),
    (
        "Capture resistance",
        "Mean of anti-capture control, anti-capture success, detection, sanctions, transparency gain, inverse capture rate, inverse public-preference distortion, inverse hidden influence, inverse legislative lobby capture, and legislative anti-lobbying success.",
    ),
    (
        "Legitimacy",
        "Mean of legislative legitimacy, review legitimacy, review public confidence, review legitimacy-control score, and anti-capture representation.",
    ),
    (
        "Complexity score",
        "Mean of administrative feasibility, inverse administrative costs, inverse review institutional cost, inverse implementation complexity, anti-capture reform feasibility, and inverse anti-capture administrative cost.",
    ),
    (
        "Efficiency",
        "0.65 times policy delivery plus 0.35 times complexity score.",
    ),
    (
        "Resilience floor",
        "Minimum of legislature component score, review component score, anti-capture component score, rights safeguard, capture resistance, and complexity score.",
    ),
]


SIBLING_SOURCE_CROSSWALK = [
    {
        "project": "Congress Institutional Simulator",
        "paper": SIMULATORS_ROOT / "Congress Institutional Simulator" / "paper" / "main.tex",
        "pdf": SIMULATORS_ROOT / "Congress Institutional Simulator" / "paper" / "main.pdf",
        "report": SIMULATORS_ROOT / "Congress Institutional Simulator" / "reports" / "simulation-campaign-v21-paper.csv",
        "cumulativeUse": "Imported legislative source.",
        "readingRule": "Treat the updated portfolio-hybrid legislature as a synthesized candidate; pairwise alternatives remain the cleaner non-default productivity and compromise comparator.",
    },
    {
        "project": "Supreme Court Simulator Design",
        "paper": SIMULATORS_ROOT / "Supreme Court Simulator Design" / "paper" / "main.tex",
        "pdf": SIMULATORS_ROOT / "Supreme Court Simulator Design" / "paper" / "main.pdf",
        "report": SIMULATORS_ROOT / "Supreme Court Simulator Design" / "reports" / "constitutional-review-campaign-v2.csv",
        "cumulativeUse": "Imported constitutional-review source.",
        "readingRule": "Keep review metrics pathway-specific and proxy-aware; the updated denominator audit does not permit pooled validation claims.",
    },
    {
        "project": "Constitutional Review Simulator",
        "paper": SIMULATORS_ROOT / "Constitutional Review Simulator" / "paper" / "main.tex",
        "pdf": SIMULATORS_ROOT / "Constitutional Review Simulator" / "paper" / "main.pdf",
        "report": SIMULATORS_ROOT / "Constitutional Review Simulator" / "reports" / "constitutional-review-sensitivity-v1.csv",
        "cumulativeUse": "Referenced review cross-check; not imported into rankings yet.",
        "readingRule": "Use the richer compliance, defiance, implementation, emergency, and public-trust fields to guide schema reconciliation before any row merge.",
    },
    {
        "project": "Lobby Capture Simulator",
        "paper": SIMULATORS_ROOT / "Lobby Capture Simulator" / "paper" / "main.tex",
        "pdf": SIMULATORS_ROOT / "Lobby Capture Simulator" / "paper" / "main.pdf",
        "report": SIMULATORS_ROOT / "Lobby Capture Simulator" / "reports" / "lobby-capture-campaign.csv",
        "cumulativeUse": "Imported anti-capture source.",
        "readingRule": "Read low observed capture through total distortion, hidden influence, venue-shifting, and validation partial/miss diagnostics.",
    },
]


def read_csv(name: str) -> list[dict[str, str]]:
    path = REPORTS / name
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def load_portfolio_module():
    path = ROOT / "scripts" / "build_portfolios.py"
    spec = importlib.util.spec_from_file_location("cumulative_build_portfolios", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_recorded_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (ROOT / path).resolve()


def portable_path(path: Path) -> str:
    absolute = path if path.is_absolute() else (ROOT / path).resolve()
    try:
        return str(absolute.relative_to(ROOT))
    except ValueError:
        try:
            return str(Path("..") / absolute.relative_to(SIMULATORS_ROOT))
        except ValueError:
            return absolute.name


def csv_row_count(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def paper_title(path: Path) -> str:
    if not path.exists():
        return "missing paper"
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"\\title(?:\[[^\]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}", text, flags=re.S)
    if not match:
        return path.stem
    return re.sub(r"\s+", " ", match.group(1)).strip()


def artifact_record(path: Path, *, count_rows: bool = False) -> dict[str, object]:
    record: dict[str, object] = {
        "path": portable_path(path),
        "exists": path.exists(),
    }
    if not path.exists():
        return record
    stat = path.stat()
    record["modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds")
    record["sha256"] = sha256(path)
    if count_rows and path.suffix == ".csv":
        record["rows"] = csv_row_count(path)
    return record


def tex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def breakable_texttt(value: object) -> str:
    text = tex_escape(value)
    text = text.replace("-", r"-\allowbreak{}")
    text = text.replace("/", r"/\allowbreak{}")
    return rf"\texttt{{{text}}}"


def fmt_int(value: int | str) -> str:
    return f"{int(value):,}"


def fmt_float(value: str | float, digits: int = 3) -> str:
    return f"{float(value):.{digits}f}"


def portfolio(row: dict[str, str]) -> str:
    return f"{row['legislature']} + {row['review']} + {row['antiCapture']}"


def portfolio_key(row: dict[str, str]) -> str:
    return "|".join([row["legislatureKey"], row["reviewKey"], row["antiCaptureKey"]])


def source_for_kind(inventory: dict, kind: str) -> dict:
    for source in inventory["sources"]:
        if source["kind"] == kind:
            return source
    raise KeyError(kind)


def ranked(rows: list[dict[str, str]], key: str) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: int(row[key]))


def rows_for(rows: list[dict[str, str]], **filters: str) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if all(row.get(field) == value for field, value in filters.items())
    ]


def write_fragment(name: str, body: str) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    path = GENERATED / name
    body = body.replace(r"\begin{table}[htbp]", r"\begin{table}[!htbp]")
    body = body.replace(r"\begin{figure}[htbp]", r"\begin{figure}[!htbp]")
    path.write_text(
        "% Generated by paper/scripts/generate_tables.py; do not edit by hand.\n"
        + body.strip()
        + "\n",
        encoding="utf-8",
    )


def write_json(name: str, data: object) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def macro(name: str, value: object) -> str:
    return rf"\newcommand{{\{name}}}{{{tex_escape(value)}}}"


def percent(value: float) -> str:
    return f"{value * 100:.0f}\\%"


def compact_weights(weights: dict[str, float]) -> str:
    return "; ".join(
        f"{tex_escape(key)} {percent(weight)}"
        for key, weight in sorted(weights.items(), key=lambda item: item[1], reverse=True)
    )


def short_case_label(label: str) -> str:
    replacements = {
        "Balanced winner": "Balanced",
        "Legitimacy-first winner": "Legitimacy",
        "Minimax-regret winner": "Minimax",
        "Robustness winner": "Robust",
        "Rights/capture winner": "Rights/capture",
        "Efficiency caution case": "Efficiency caution",
        "Current-system-ish baseline": "Current baseline",
    }
    return replacements.get(label, label)


def short_run_label(label: str) -> str:
    replacements = {
        "current-imported-review": "current",
        "companion-review-first-pass": "companion",
        "harmonized-review-source": "harmonized",
    }
    return replacements.get(label, label)


def short_coefficient_key(label: str) -> str:
    replacements = {
        "agendaCapacityBonus": "agendaCap",
        "agendaOverloadAdd": "agendaLoad",
        "captureControlBonus": "capCtrl",
        "capturePressureAdd": "capPress",
        "courtCurbingReduction": "courtCurb",
        "deliveryBottleneckAdd": "deliverGap",
        "emergencySafeguardBonus": "emergSafe",
        "feedbackCorrectionBonus": "feedback",
        "lobbyAdaptationMultiplier": "lobbyAdapt",
        "partyAdaptationMultiplier": "partyAdapt",
        "recoveryCapacityBonus": "recovery",
        "reviewCapacityBonus": "reviewCap",
        "rightsRiskAdd": "rightsRisk",
        "transitionLoadAdd": "transLoad",
        "transitionReadinessBonus": "transReady",
    }
    return replacements.get(label, label)


def tikz_bar_rows(rows: list[tuple[str, float, str]], max_value: float = 1.0) -> str:
    body: list[str] = []
    for index, (label, value, display_value) in enumerate(rows, start=1):
        y = -0.44 * index
        width = min(max(value / max_value, 0.0), 1.0)
        body.append(rf"\node[anchor=east] at (-0.02,{y:.2f}) {{{tex_escape(label)}}};")
        body.append(rf"\fill[black!55] (0,{y - 0.10:.2f}) rectangle ({width:.3f},{y + 0.10:.2f});")
        body.append(rf"\node[anchor=west] at ({min(width + 0.02, 1.02):.3f},{y:.2f}) {{{tex_escape(display_value)}}};")
    return "\n".join(body)


def source_summary_table(inventory: dict) -> str:
    rows = []
    for source in inventory["sources"]:
        basename = breakable_texttt(Path(source["path"]).name)
        rows.append(
            " & ".join(
                [
                    tex_escape(source["label"]),
                    fmt_int(source["rows"]),
                    fmt_int(source["scenarioCount"]),
                    fmt_int(source["configuredMetricCount"]),
                    basename,
                ]
            )
            + r" \\"
        )
    return r"""
\begin{table}[htbp]
\centering
\footnotesize
\begin{tabular}{@{}L{0.25\linewidth}r r r L{0.34\linewidth}@{}}
\toprule
Source & Rows & Scenarios & Metrics & Imported report \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Current source artifacts imported by the cumulative harness.}
\end{table}
"""


def source_provenance(inventory: dict) -> tuple[str, dict[str, object]]:
    records = []
    rows = []
    for source in inventory["sources"]:
        path = resolve_recorded_path(source["path"])
        digest = sha256(path)
        record = {
            "kind": source["kind"],
            "label": source["label"],
            "path": source["path"],
            "rows": source["rows"],
            "scenarioCount": source["scenarioCount"],
            "sha256": digest,
        }
        records.append(record)
        rows.append(
            f"{tex_escape(source['label'])} & {fmt_int(source['rows'])} & "
            f"{fmt_int(source['scenarioCount'])} & {breakable_texttt(path.name)} & "
            f"{breakable_texttt(digest[:16])} \\\\"
        )
    table = r"""
\begin{table}[htbp]
\centering
\scriptsize
\begin{tabular}{@{}L{0.24\linewidth}r r L{0.31\linewidth}L{0.17\linewidth}@{}}
\toprule
Source & Rows & Scenarios & Imported report & SHA-256 prefix \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Input source provenance for the current paper build. Full hashes are written to \texttt{paper/generated/source-provenance.json}.}
\end{table}
"""
    return table, {"sources": records}


def source_paper_crosswalk() -> tuple[str, dict[str, object]]:
    records = []
    rows = []
    for item in SIBLING_SOURCE_CROSSWALK:
        paper_path = Path(item["paper"])
        report_path = Path(item["report"])
        pdf_path = Path(item["pdf"])
        paper = artifact_record(paper_path)
        report = artifact_record(report_path, count_rows=True)
        pdf = artifact_record(pdf_path)
        record = {
            "project": item["project"],
            "title": paper_title(paper_path),
            "paper": paper,
            "pdf": pdf,
            "report": report,
            "cumulativeUse": item["cumulativeUse"],
            "readingRule": item["readingRule"],
        }
        records.append(record)

        if report.get("exists"):
            row_count = f"{fmt_int(report.get('rows', 0))} rows"
            report_label = (
                f"{breakable_texttt(report_path.name)}; {row_count}; "
                f"hash {breakable_texttt(str(report['sha256'])[:12])}"
            )
        else:
            report_label = r"\emph{report missing}"
        if paper.get("exists"):
            paper_label = (
                f"{tex_escape(record['title'])}; "
                f"{breakable_texttt(paper_path.name)}; "
                f"hash {breakable_texttt(str(paper['sha256'])[:12])}"
            )
        else:
            paper_label = r"\emph{paper missing}"
        rows.append(
            f"{tex_escape(item['project'])} & {paper_label} & {report_label} & "
            f"{tex_escape(item['cumulativeUse'])} & {tex_escape(item['readingRule'])} \\\\"
        )

    table = r"""
\begin{table}[htbp]
\centering
\scriptsize
\setlength{\tabcolsep}{3pt}
\begin{tabular}{@{}L{0.13\linewidth}L{0.18\linewidth}L{0.16\linewidth}L{0.15\linewidth}L{0.23\linewidth}@{}}
\toprule
Project & Updated paper checked & Current report artifact & Cumulative use & Reading rule after refresh \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Crosswalk from updated sibling simulator papers and reports to the cumulative synthesis. The Constitutional Review Simulator is deliberately treated as a review cross-check until its richer schema is reconciled with the imported Supreme Court Simulator Design campaign.}
\end{table}
"""
    return table, {"sources": records}


def review_reconciliation_table(rows_data: list[dict[str, str]]) -> str:
    categories = [
        "shared configured metric",
        "imported-only configured metric",
        "companion-only configured metric",
        "missing from both review sources",
        "companion adaptive candidate",
    ]
    rows = []
    for category in categories:
        count = sum(1 for row in rows_data if row["comparisonStatus"] == category)
        rows.append(f"{tex_escape(category)} & {fmt_int(count)} \\\\")
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}L{0.54\linewidth}r@{}}
\toprule
Review reconciliation category & Count \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Construct-level reconciliation between the imported Supreme Court Simulator Design review source and the companion Constitutional Review Simulator. Companion adaptive candidates are not added to the static ranking until denominator and construct ownership are resolved.}
\end{table}
"""


def dual_review_sensitivity_table(rows_data: list[dict[str, str]]) -> str:
    rows = []
    for row in rows_data:
        score = row["balancedScore"] or "--"
        scenarios = row["reviewScenarios"] or "--"
        portfolios = row["portfolioCount"] or "--"
        top25 = row["top25OverlapWithPrimary"] or "--"
        primary_rank = row["primaryWinnerRankInRun"] or "--"
        reciprocal_rank = row["runWinnerRankInPrimary"] or "--"
        notes = row["notes"]
        rows.append(
            f"{tex_escape(row['runKey'])} & {tex_escape(row['status'])} & "
            f"{tex_escape(row['reviewSource'])} & {tex_escape(scenarios)} & {tex_escape(portfolios)} & "
            f"{tex_escape(score)} & {tex_escape(top25)} & {tex_escape(primary_rank)} & "
            f"{tex_escape(reciprocal_rank)} & {tex_escape(notes)} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}L{0.15\linewidth}L{0.16\linewidth}L{0.17\linewidth}r r r r r r L{0.28\linewidth}@{}}
\toprule
Run & Status & Review source & Scen. & Ports. & Score & Top-25 overlap & Primary winner rank & Run winner primary rank & Notes \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
    \caption{Review-source static sensitivity. The companion run swaps in the Constitutional Review Simulator sensitivity campaign; the harmonized run uses only shared same-direction static review fields from both review projects. Overlap and rank columns use canonical portfolio keys with harmonized source prefixes stripped.}
    \end{table}
    """


def review_harmonization_manifest_table(rows_data: list[dict[str, str]]) -> str:
    action_order = ["included", "excluded", "not present", "adaptive candidate", "deferred"]
    rows = []
    for action in action_order:
        count = sum(1 for row in rows_data if row["harmonizedAction"] == action)
        if count:
            rows.append(f"{tex_escape(action)} & {fmt_int(count)} \\\\")
    included_metrics = sorted({row["metricName"] for row in rows_data if row["harmonizedAction"] == "included"})
    metric_text = ", ".join(included_metrics)
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}L{0.58\linewidth}r@{}}
\toprule
Harmonization action & Manifest rows \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Review harmonization manifest. Included static fields are: """ + tex_escape(metric_text) + r""". Source-specific fields remain available in source-swap sensitivity screens or adaptive calibration work, but are excluded from the harmonized static source.}
\end{table}
"""


def review_variant_overlap_table(rows_data: list[dict[str, str]]) -> str:
    rows = []
    for row in rows_data:
        rows.append(
            f"{tex_escape(short_run_label(row['leftRunKey']))} & {tex_escape(short_run_label(row['rightRunKey']))} & "
            f"{fmt_int(row['top25Overlap'])} & {fmt_int(row['top100Overlap'])} & "
            f"{fmt_int(row['sharedCanonicalPortfolioCount'])} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\small
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}L{0.18\linewidth}L{0.18\linewidth}r r r@{}}
\toprule
Left run & Right run & Top-25 overlap & Top-100 overlap & Shared canonical portfolios \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
\caption{Pairwise overlap among review-source variants. Counts use canonical portfolio keys, so harmonized rows from prefixed source scenarios can be compared to the corresponding source-run scenario when one exists.}
\end{table}
"""


def review_variant_rank_shift_table(rows_data: list[dict[str, str]], limit: int = 12) -> str:
    rows = []
    for row in sorted(rows_data, key=lambda item: int(item["bestObservedRank"]))[:limit]:
        portfolio_text = f"{row['legislature']} + {row['review']} + {row['antiCapture']}"
        rows.append(
            f"{tex_escape(row['currentRank'] or '--')} & {tex_escape(row['companionRank'] or '--')} & "
            f"{tex_escape(row['harmonizedRank'] or '--')} & {tex_escape(row['companionMinusCurrent'] or '--')} & "
            f"{tex_escape(row['harmonizedMinusCurrent'] or '--')} & {tex_escape(portfolio_text)} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}r r r r r L{0.50\linewidth}@{}}
\toprule
Current & Companion & Harmonized & Comp.-cur. & Harm.-cur. & Portfolio \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
\caption{Rank shifts for the best-observed portfolios across review-source variants. Blank cells mean the canonical review scenario is not available in that variant.}
\end{table}
"""


def balanced_result_table(row: dict[str, str]) -> str:
    selected = [
        ("Legislature", row["legislature"]),
        ("Review", row["review"]),
        ("Anti-capture", row["antiCapture"]),
    ]
    diagnostics = [
        ("Balanced score", row["overallScore"]),
        ("Policy delivery", row["policyDelivery"]),
        ("Public alignment", row["publicAlignment"]),
        ("Rights safeguard", row["rightsSafeguard"]),
        ("Capture resistance", row["captureResistance"]),
        ("Legitimacy", row["legitimacy"]),
        ("Complexity score", row["complexityScore"]),
        ("Resilience floor", row["resilienceFloor"]),
    ]
    selection_rows = "\n".join(
        f"{tex_escape(label)} & {tex_escape(value)} \\\\" for label, value in selected
    )
    diagnostic_rows = "\n".join(
        f"{tex_escape(label)} & {fmt_float(value)} \\\\" for label, value in diagnostics
    )
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}L{0.24\linewidth}L{0.66\linewidth}@{}}
\toprule
Portfolio component & Selected design \\
\midrule
""" + selection_rows + r"""
\bottomrule
\end{tabular}
\qquad
\begin{tabular}{@{}L{0.25\linewidth}r@{}}
\toprule
Diagnostic & Value \\
\midrule
""" + diagnostic_rows + r"""
\bottomrule
\end{tabular}
\caption{Balanced-score winner and diagnostics.}
\end{table}
"""


def profile_winners_table(profile_rows: list[dict[str, str]]) -> str:
    winners = ranked([row for row in profile_rows if row["profileRank"] == "1"], "balancedRank")
    profile_order = [
        "balanced",
        "efficiency-first",
        "rights-first",
        "anti-capture-first",
        "low-complexity",
        "legitimacy-first",
    ]
    by_profile = {row["profile"]: row for row in winners}
    rows = []
    for profile in profile_order:
        row = by_profile[profile]
        rows.append(
            f"{tex_escape(row['profileLabel'])} & {tex_escape(portfolio(row))} & "
            f"{fmt_float(row['profileScore'])} & {fmt_int(row['balancedRank'])} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}L{0.18\linewidth}L{0.55\linewidth}r r@{}}
\toprule
Profile & Winning portfolio & Score & Balanced rank \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Profile-specific portfolio winners.}
\end{table}
"""


def robustness_table(row: dict[str, str]) -> str:
    rows = [
        ("Portfolio", portfolio(row)),
        ("Robust score", fmt_float(row["robustScore"])),
        ("Balanced rank", fmt_int(row["rank"])),
        ("Average profile rank", fmt_float(row["averageProfileRank"])),
        ("Worst profile rank", fmt_int(row["worstProfileRank"])),
        ("Top-25 profile appearances", fmt_int(row["top25ProfileCount"])),
    ]
    body = "\n".join(f"{tex_escape(label)} & {tex_escape(value)} \\\\" for label, value in rows)
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}L{0.30\linewidth}L{0.58\linewidth}@{}}
\toprule
Robustness diagnostic & Value \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\caption{Cross-profile robustness winner.}
\end{table}
"""


def pareto_summary_table(portfolio_count: int, exact_count: int, epsilon_count: int, uncertainty_count: int) -> str:
    rows = [
        ("Total generated portfolios", fmt_int(portfolio_count)),
        ("Exact point-estimate Pareto front", f"{fmt_int(exact_count)} ({100.0 * exact_count / portfolio_count:.1f}\\%)"),
        ("Epsilon-Pareto front", f"{fmt_int(epsilon_count)} ({100.0 * epsilon_count / portfolio_count:.1f}\\%)"),
        (
            "Uncertainty-aware Pareto front",
            f"{fmt_int(uncertainty_count)} ({100.0 * uncertainty_count / portfolio_count:.1f}\\%)",
        ),
    ]
    body = "\n".join(f"{tex_escape(label)} & {value} \\\\" for label, value in rows)
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}L{0.42\linewidth}r@{}}
\toprule
Pareto diagnostic & Value \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\caption{Pareto-front sizes under exact, epsilon, and uncertainty-aware dominance rules.}
\end{table}
"""


def bridge_ranking_table(baseline_rows: list[dict[str, str]]) -> str:
    rows = []
    for row in ranked(baseline_rows, "bridgeRank"):
        rows.append(
            f"{row['bridgeRank']} & {tex_escape(row['caseLabel'])} & {fmt_float(row['bridgeScore'])} & "
            f"{fmt_float(row['averageDelivery'])} & {fmt_float(row['finalPolicyQuality'])} & "
            f"{fmt_float(row['finalPublicAlignment'])} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}rL{0.34\linewidth}r r r r@{}}
\toprule
Rank & Case & Score & Avg. delivery & Final quality & Final alignment \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Baseline interbranch bridge ranking.}
\end{table}
"""


def stress_stability_table(stability_rows: list[dict[str, str]]) -> str:
    rows = []
    for row in ranked(stability_rows, "winTopTwoStabilityRank"):
        rows.append(
            f"{row['winTopTwoStabilityRank']} & {tex_escape(row['caseLabel'])} & "
            f"{fmt_float(row['averageStressRank'])} & {row['worstStressRank']} & "
            f"{row['stressWins']} & {row['topTwoStressCount']} & {fmt_float(row['averageBridgeScore'])} & "
            f"{fmt_float(row['maxStressRegret'])} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\footnotesize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}rL{0.25\linewidth}r r r r r r@{}}
\toprule
Win/top-two rank & Case & Avg. rank & Worst & Wins & Top-two & Avg. score & Max regret \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
\caption{Stress-profile stability across the focused bridge cases, sorted by the wins/top-two rule.}
\end{table}
"""


def stress_stability_definitions_table(definition_rows: list[dict[str, str]]) -> str:
    rows = []
    for row in definition_rows:
        rows.append(
            f"{tex_escape(row['criterionLabel'])} & {tex_escape(row['winnerCaseLabel'])} & "
            f"{tex_escape(row['winnerMetricSummary'])} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\footnotesize
\begin{tabular}{@{}L{0.24\linewidth}L{0.28\linewidth}L{0.38\linewidth}@{}}
\toprule
Criterion & Winner & Winner metric \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Alternative bridge-stability definitions. The wins/top-two rule is the default report sort, not the only stability interpretation.}
\end{table}
"""


def bridge_case_scope_table(baseline_rows: list[dict[str, str]], portfolio_count: int) -> str:
    rows = []
    for row in ranked(baseline_rows, "bridgeRank"):
        rows.append(
            f"{row['bridgeRank']} & {tex_escape(row['caseLabel'])} & {fmt_int(row['balancedRank'])} & "
            f"{tex_escape(row['selectorSource'])} \\\\"
        )
    unbridged = portfolio_count - len(baseline_rows)
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}rL{0.27\linewidth}rL{0.42\linewidth}@{}}
\toprule
Baseline bridge rank & Focused case & Static balanced rank & Selector \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
\caption{Bridge v0 evaluates """ + fmt_int(len(baseline_rows)) + r""" focused cases from """ + fmt_int(portfolio_count) + r""" static portfolios; """ + fmt_int(unbridged) + r""" static portfolios are not bridge-simulated in the paper workflow.}
\end{table}
"""


def high_capture_figure(high_capture_rows: list[dict[str, str]]) -> str:
    sorted_rows = ranked(high_capture_rows, "bridgeRank")
    y_min = -0.44 * (len(sorted_rows) + 0.6)
    return r"""
\begin{figure}[htbp]
\centering
\resizebox{0.92\linewidth}{!}{%
\begin{tikzpicture}[x=4.7in,y=0.80in]
\draw[->] (0,0) -- (1.05,0) node[anchor=west] {Bridge score};
\foreach \x/\lab in {0/0.00,0.25/0.25,0.50/0.50,0.75/0.75,1.00/1.00} {
  \draw[black!35] (\x,0.03) -- (\x,""" + f"{y_min:.2f}" + r""");
  \node[anchor=north] at (\x,0) {\scriptsize \lab};
}
""" + tikz_bar_rows(
        [
            (short_case_label(row["caseLabel"]), float(row["bridgeScore"]), fmt_float(row["bridgeScore"]))
            for row in sorted_rows
        ]
    ) + r"""
\end{tikzpicture}
}
\caption{High-capture bridge scores across the focused bridge cases.}
\end{figure}
"""


def high_capture_table(high_capture_rows: list[dict[str, str]]) -> str:
    rows = []
    for row in ranked(high_capture_rows, "bridgeRank"):
        rows.append(
            f"{row['bridgeRank']} & {tex_escape(row['caseLabel'])} & {fmt_float(row['bridgeScore'])} & "
            f"{fmt_float(row['finalPolicyQuality'])} & {fmt_float(row['finalCapturePressure'])} & "
            f"{fmt_float(row['finalLegitimacy'])} & {tex_escape(row['failureModes'])} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}rL{0.20\linewidth}r r r r L{0.27\linewidth}@{}}
\toprule
Rank & Case & Score & Final quality & Final capture & Final legitimacy & Failure flags \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
\caption{High-capture stress diagnostics.}
\end{table}
"""


def uncertainty_summary_table(tradeoff_rows: list[dict[str, str]]) -> str:
    rows = []
    for row in tradeoff_rows:
        label = row["caseLabels"].split("; ")[0]
        interval = f"{fmt_float(row['uncertaintyLow'])}--{fmt_float(row['uncertaintyHigh'])}"
        rows.append(
            f"{tex_escape(label)} & {fmt_int(row['balancedRank'])} & "
            f"{fmt_float(row['balancedScore'])} & {tex_escape(interval)} & "
            f"{fmt_float(row['modelUncertaintyBand'])} & {fmt_float(row['maxProfileRegret'])} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\begin{tabular}{@{}L{0.27\linewidth}r r r r r@{}}
\toprule
Case & Balanced rank & Score & Synthetic band & Half-width & Max regret \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Uncertainty and regret diagnostics for the focused candidate set. Bands are synthetic model-sensitivity bands, not empirical confidence intervals.}
\end{table}
"""


def uncertainty_resolution_table(uncertainty_rows: list[dict[str, str]], portfolio_count: int) -> str:
    balanced = next(row for row in uncertainty_rows if row["balancedRank"] == "1")
    lower_bound_leader = ranked(uncertainty_rows, "uncertaintyLowerBoundRank")[0]
    overlap_count = sum(1 for row in uncertainty_rows if row["balancedIntervalRelation"] == "overlaps-balanced")
    below_count = sum(1 for row in uncertainty_rows if row["balancedIntervalRelation"] == "below-balanced")
    above_count = sum(1 for row in uncertainty_rows if row["balancedIntervalRelation"] == "above-balanced")
    rows = [
        ("Balanced interval", f"{fmt_float(balanced['uncertaintyLow'])}--{fmt_float(balanced['uncertaintyHigh'])}"),
        ("Rows overlapping balanced interval", fmt_int(overlap_count)),
        ("Rows entirely below balanced interval", fmt_int(below_count)),
        ("Rows entirely above balanced interval", fmt_int(above_count)),
        ("Balanced lower-bound rank", fmt_int(balanced["uncertaintyLowerBoundRank"])),
        (
            "Lower-bound leader",
            f"{portfolio(lower_bound_leader)} (balanced rank {fmt_int(lower_bound_leader['balancedRank'])})",
        ),
    ]
    body = "\n".join(f"{tex_escape(label)} & {tex_escape(value)} \\\\" for label, value in rows)
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}L{0.38\linewidth}L{0.52\linewidth}@{}}
\toprule
Uncertainty diagnostic & Value \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\caption{Interval-resolution diagnostics for all """ + fmt_int(portfolio_count) + r""" portfolios. Overlap counts show whether point-estimate ranks are separated by the synthetic uncertainty bands.}
\end{table}
"""


def minimax_regret_table(regret_rows: list[dict[str, str]], limit: int = 8) -> str:
    rows = []
    for row in ranked(regret_rows, "minimaxRegretRank")[:limit]:
        rows.append(
            f"{fmt_int(row['minimaxRegretRank'])} & {fmt_float(row['maxProfileRegret'])} & "
            f"{fmt_float(row['averageProfileRegret'])} & {fmt_int(row['balancedRank'])} & "
            f"{tex_escape(portfolio(row))} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}r r r r L{0.58\linewidth}@{}}
\toprule
Regret rank & Max regret & Avg. regret & Balanced rank & Portfolio \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
\caption{Minimax-regret leaders across the configured value profiles. Low regret does not by itself make a portfolio recommendable.}
\end{table}
"""


def profile_tradeoff_table(tradeoff_rows: list[dict[str, str]]) -> str:
    profile_fields = [
        ("B", "balancedRank"),
        ("Eff.", "efficiency-firstRank"),
        ("Rights", "rights-firstRank"),
        ("Cap.", "anti-capture-firstRank"),
        ("Low-cx", "low-complexityRank"),
        ("Legit.", "legitimacy-firstRank"),
        ("Regret", "minimaxRegretRank"),
    ]
    header = " & ".join(label for label, _field in profile_fields)
    rows = []
    for row in tradeoff_rows:
        label = row["caseLabels"].split("; ")[0]
        ranks = " & ".join(fmt_int(row[field]) for _label, field in profile_fields)
        rows.append(f"{tex_escape(label)} & {ranks} \\\\")
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\begin{tabular}{@{}L{0.32\linewidth}rrrrrrr@{}}
\toprule
Focused case & """ + header + r""" \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Profile-by-profile ranks for the focused candidate set. Lower ranks are better.}
\end{table}
    """


def candidate_synthesis_table(
    tradeoff_rows: list[dict[str, str]],
    robust_row: dict[str, str],
    bridge_rows: list[dict[str, str]],
    adaptive_summary_rows: list[dict[str, str]],
) -> str:
    baseline_bridge = rows_for(bridge_rows, stressProfile="baseline")
    bridge_by_case = {row["caseKey"]: row for row in baseline_bridge}
    bridge_by_portfolio: dict[str, dict[str, str]] = {}
    for row in baseline_bridge:
        key = portfolio_key(row)
        if key not in bridge_by_portfolio or int(row["bridgeRank"]) < int(bridge_by_portfolio[key]["bridgeRank"]):
            bridge_by_portfolio[key] = row
    adaptive_by_key = {row["portfolioKey"]: row for row in adaptive_summary_rows}
    adaptive_by_name = {row["portfolio"]: row for row in adaptive_summary_rows}

    def tradeoff_case(label: str) -> dict[str, str]:
        return next(row for row in tradeoff_rows if label in row["caseLabels"])

    def tradeoff_portfolio(row: dict[str, str]) -> str:
        return f"{row['legislature']} + {row['review']} + {row['antiCapture']}"

    def adaptive_for_tradeoff(row: dict[str, str]) -> dict[str, str]:
        return adaptive_by_name[tradeoff_portfolio(row)]

    def bridge_text(row: dict[str, str]) -> str:
        return (
            f"{fmt_int(row['bridgeRank'])}/{fmt_int(len(baseline_bridge))} "
            f"({fmt_float(row['bridgeScore'])})"
        )

    current = bridge_by_case["current-system-baseline"]
    balanced = tradeoff_case("balanced winner")
    robust_tradeoff = tradeoff_case("robustness winner")
    adaptive_leader = ranked(adaptive_summary_rows, "adaptiveOverallRank")[0]
    adaptive_leader_bridge = bridge_by_portfolio.get(adaptive_leader["portfolioKey"])

    rows = [
        (
            "Current-system-ish baseline",
            "Stylized comparator, not an empirical claim about the live U.S. system.",
            f"rank {fmt_int(current['balancedRank'])}; score {fmt_float(current['balancedScore'])}; floor {fmt_float(current['baseResilienceFloor'])}",
            f"bridge {bridge_text(current)}; adaptive rank {fmt_int(adaptive_by_key[current['legislatureKey'] + '|' + current['reviewKey'] + '|' + current['antiCaptureKey']]['adaptiveOverallRank'])}",
            "Does not beat the leading synthetic portfolios; kept to show the comparison floor.",
        ),
        (
            "Balanced static winner",
            "Best point-estimate and lower-bound static screen.",
            f"rank {fmt_int(balanced['balancedRank'])}; score {fmt_float(balanced['balancedScore'])}; max regret {fmt_float(balanced['maxProfileRegret'])}",
            f"bridge {bridge_text(bridge_by_case['balanced-winner'])}; adaptive rank {fmt_int(adaptive_for_tradeoff(balanced)['adaptiveOverallRank'])}",
            f"Beats the stylized baseline in static and focused-bridge screens, but gate is {adaptive_for_tradeoff(balanced)['recommendationGate']}.",
        ),
        (
            "Robustness challenger",
            "Best cross-profile robustness row and strongest stress-regret challenger.",
            f"balanced rank {fmt_int(robust_tradeoff['balancedRank'])}; robustness rank {fmt_int(robust_row['robustRank'])}; floor {fmt_float(robust_tradeoff['resilienceFloor'])}",
            f"bridge {bridge_text(bridge_by_case['robustness-winner'])}; adaptive rank {fmt_int(adaptive_for_tradeoff(robust_tradeoff)['adaptiveOverallRank'])}",
            f"Stronger validation target than the static winner under adaptive screening; gate is {adaptive_for_tradeoff(robust_tradeoff)['recommendationGate']}.",
        ),
        (
            "Adaptive gray-zone leader",
            "Highest all-portfolio adaptive-survival score.",
            f"static rank {fmt_int(adaptive_leader['balancedRank'])}; score {fmt_float(adaptive_leader['balancedScore'])}; max regret {fmt_float(adaptive_leader['maxProfileRegret'])}",
            (
                f"bridge {bridge_text(adaptive_leader_bridge)}; adaptive rank 1"
                if adaptive_leader_bridge is not None
                else "not in focused bridge v0 set; adaptive rank 1"
            ),
            f"Best current validation target, not a recommendation; gate is {adaptive_leader['recommendationGate']}.",
        ),
    ]

    body = "\n".join(
        f"{tex_escape(candidate)} & {tex_escape(role)} & {tex_escape(static)} & "
        f"{tex_escape(feedback)} & {tex_escape(status)} \\\\"
        for candidate, role, static, feedback, status in rows
    )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}L{0.18\linewidth}L{0.24\linewidth}L{0.20\linewidth}L{0.20\linewidth}L{0.28\linewidth}@{}}
\toprule
Candidate & Why it is in the paper & Static screen & Feedback/adaptive screen & Paper status \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
}
\caption{Reader-facing synthesis of the stylized current-system baseline and the main challenger portfolios. ``Beats'' means stronger in the current synthetic screens, not empirically proven superior.}
\end{table}
"""


def fragile_watchlist_table(watchlist_rows: list[dict[str, str]], limit: int = 8) -> str:
    rows = []
    for row in watchlist_rows[:limit]:
        rows.append(
            f"{fmt_int(row['balancedRank'])} & {fmt_int(row['minimaxRegretRank'])} & "
            f"{fmt_float(row['modelUncertaintyBand'])} & {tex_escape(portfolio(row))} & "
            f"{tex_escape(row['doNotRecommendYetReason'])} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}r r r L{0.42\linewidth}L{0.38\linewidth}@{}}
\toprule
Balanced rank & Regret rank & Band & Portfolio & Do-not-recommend-yet reason \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
\caption{Fragile headline or near-headline portfolios that should not be converted into recommendations without more modeling.}
\end{table}
"""


def speculative_agenda_table(agenda: list[tuple[str, str, str]]) -> str:
    rows = "\n".join(
        f"{tex_escape(direction)} & {tex_escape(rationale)} & {tex_escape(status)} \\\\"
        for direction, rationale, status in agenda
    )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\begin{tabular}{@{}L{0.23\linewidth}L{0.54\linewidth}L{0.15\linewidth}@{}}
\toprule
Direction & Why add it & Claim status \\
\midrule
""" + rows + r"""
\bottomrule
\end{tabular}
\caption{Systems and mechanisms that should be modeled next before stronger institutional recommendations are made.}
\end{table}
"""


def bridge_baseline_figure(baseline_rows: list[dict[str, str]]) -> str:
    sorted_rows = ranked(baseline_rows, "bridgeRank")
    chart_rows = [
        (short_case_label(row["caseLabel"]), float(row["bridgeScore"]), fmt_float(row["bridgeScore"]))
        for row in sorted_rows
    ]
    y_min = -0.44 * (len(chart_rows) + 0.6)
    return r"""
\begin{figure}[htbp]
\centering
\resizebox{0.92\linewidth}{!}{%
\begin{tikzpicture}[x=4.7in,y=0.80in]
\draw[->] (0,0) -- (1.05,0) node[anchor=west] {Bridge score};
\foreach \x/\lab in {0/0.00,0.25/0.25,0.50/0.50,0.75/0.75,1.00/1.00} {
  \draw[black!35] (\x,0.03) -- (\x,""" + f"{y_min:.2f}" + r""");
  \node[anchor=north] at (\x,0) {\scriptsize \lab};
}
""" + tikz_bar_rows(chart_rows) + r"""
\end{tikzpicture}
}
\caption{Baseline bridge scores for the focused portfolio cases.}
\end{figure}
"""


def stress_stability_figure(stability_rows: list[dict[str, str]]) -> str:
    sorted_rows = ranked(stability_rows, "averageRankStabilityRank")
    # Lower average rank is better, so plot a normalized stability score.
    worst_possible = max(float(row["worstStressRank"]) for row in sorted_rows)
    chart_rows = []
    for row in sorted_rows:
        avg_rank = float(row["averageStressRank"])
        stability_score = (worst_possible + 1.0 - avg_rank) / worst_possible
        chart_rows.append((short_case_label(row["caseLabel"]), stability_score, fmt_float(avg_rank)))
    y_min = -0.44 * (len(chart_rows) + 0.6)
    return r"""
\begin{figure}[htbp]
\centering
\resizebox{0.92\linewidth}{!}{%
\begin{tikzpicture}[x=4.7in,y=0.80in]
\draw[->] (0,0) -- (1.05,0) node[anchor=west] {Normalized stability};
\foreach \x/\lab in {0/0.00,0.25/0.25,0.50/0.50,0.75/0.75,1.00/1.00} {
  \draw[black!35] (\x,0.03) -- (\x,""" + f"{y_min:.2f}" + r""");
  \node[anchor=north] at (\x,0) {\scriptsize \lab};
}
""" + tikz_bar_rows(chart_rows) + r"""
\end{tikzpicture}
}
\caption{Average-rank stress stability across the focused bridge cases. Bar labels show average stress rank; lower rank is better.}
\end{figure}
"""


def diagnostic_formula_table() -> str:
    rows = "\n".join(
        f"{tex_escape(label)} & {tex_escape(formula)} \\\\" for label, formula in DIAGNOSTIC_FORMULAS
    )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\begin{tabular}{@{}L{0.22\linewidth}L{0.70\linewidth}@{}}
\toprule
Diagnostic & Formula summary \\
\midrule
""" + rows + r"""
\bottomrule
\end{tabular}
\caption{Static portfolio diagnostic construction. Values are normalized to 0--1 before aggregation.}
\end{table}
"""


def profile_weights_table(profiles: list[object]) -> str:
    rows = "\n".join(
        f"{tex_escape(profile.label)} & {compact_weights(profile.weights)} \\\\" for profile in profiles
    )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\begin{tabular}{@{}L{0.20\linewidth}L{0.72\linewidth}@{}}
\toprule
Profile & Weights \\
\midrule
""" + rows + r"""
\bottomrule
\end{tabular}
\caption{Scoring profile weights used for static reranking.}
\end{table}
"""


def bridge_score_weights_table(assumptions: dict) -> str:
    weights = assumptions["coefficients"]["bridgeScore"]
    rows = "\n".join(
        f"{tex_escape(key)} & {percent(float(value))} \\\\"
        for key, value in sorted(weights.items(), key=lambda item: item[1], reverse=True)
    )
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}L{0.42\linewidth}r@{}}
\toprule
Bridge-score component & Weight \\
\midrule
""" + rows + r"""
\bottomrule
\end{tabular}
\caption{Bridge-score weights from \texttt{config/interbranch-bridge-v0.json}.}
\end{table}
"""


def stress_modifier_table(assumptions: dict) -> str:
    rows = []
    for key, stress in assumptions["stressProfiles"].items():
        modifiers = stress.get("modifiers", {})
        summary = "none" if not modifiers else "; ".join(
            f"{name}={value}" for name, value in modifiers.items()
        )
        rows.append(f"{tex_escape(stress.get('label', key))} & {tex_escape(summary)} \\\\")
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\begin{tabular}{@{}L{0.26\linewidth}L{0.66\linewidth}@{}}
\toprule
Stress profile & Modifiers \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Bridge stress modifiers. Multipliers and additive adjustments are applied to the baseline bridge equations.}
\end{table}
"""


def adaptive_leaders_table(adaptive_summary_rows: list[dict[str, str]], limit: int = 10) -> str:
    rows = []
    for row in ranked(adaptive_summary_rows, "adaptiveOverallRank")[:limit]:
        rows.append(
            f"{fmt_int(row['adaptiveOverallRank'])} & {fmt_float(row['avgAdaptiveScore'])} & "
            f"{fmt_int(row['worstAdaptiveRank'])} & {fmt_float(row['maxStressRegret'])} & "
            f"{tex_escape(row['evidenceStrength'])} & {tex_escape(row['recommendationGate'])} & "
            f"{tex_escape(row['portfolio'])} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}r r r r L{0.18\linewidth}L{0.20\linewidth}L{0.42\linewidth}@{}}
\toprule
Adaptive rank & Avg. score & Worst stress rank & Max regret & Evidence & Gate & Portfolio \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
\caption{Adaptive Bridge v1 all-portfolio leaders. Gate status is a synthetic screening result, not a recommendation.}
\end{table}
"""


def adaptive_gate_table(adaptive_summary_rows: list[dict[str, str]]) -> str:
    gate_order = [
        "provisional shortlist",
        "calibration gray zone, not recommendation",
        "review priority, not recommendation",
        "do not recommend yet",
    ]
    rows = []
    for gate in gate_order:
        count = sum(1 for row in adaptive_summary_rows if row["recommendationGate"] == gate)
        leader = next(
            (row for row in ranked(adaptive_summary_rows, "adaptiveOverallRank") if row["recommendationGate"] == gate),
            None,
        )
        leader_text = "none" if leader is None else f"{leader['portfolio']} (rank {fmt_int(leader['adaptiveOverallRank'])})"
        rows.append(f"{tex_escape(gate)} & {fmt_int(count)} & {tex_escape(leader_text)} \\\\")
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}L{0.26\linewidth}rL{0.55\linewidth}@{}}
\toprule
Adaptive gate & Count & Highest-ranked example \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Recommendation gate counts from Adaptive Bridge v1. Rows outside the provisional shortlist remain research targets rather than institutional recommendations.}
\end{table}
"""


def adaptive_stress_winners_table(adaptive_rows: list[dict[str, str]]) -> str:
    rows = []
    for stress in sorted({row["stressProfile"] for row in adaptive_rows}):
        winner = ranked(rows_for(adaptive_rows, stressProfile=stress), "adaptiveRank")[0]
        rows.append(
            f"{tex_escape(winner['stressLabel'])} & {tex_escape(winner['portfolio'])} & "
            f"{fmt_float(winner['adaptiveScore'])} & {fmt_int(winner['balancedRank'])} \\\\"
        )
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}L{0.23\linewidth}L{0.55\linewidth}r r@{}}
\toprule
Stress profile & Adaptive winner & Score & Static rank \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
\caption{Stress-profile winners in Adaptive Bridge v1 over all static portfolios.}
\end{table}
"""


def adaptive_mechanisms_table(adaptive_assumptions: dict) -> str:
    rows = "\n".join(
        f"{tex_escape(mechanism)} \\\\" for mechanism in adaptive_assumptions["modeledMechanisms"]
    )
    return r"""
\begin{table}[htbp]
\centering
\small
\begin{tabular}{@{}L{0.88\linewidth}@{}}
\toprule
Synthetic adaptive mechanism introduced in Bridge v1 \\
\midrule
""" + rows + r"""
\bottomrule
\end{tabular}
\caption{Adaptive Bridge v1 mechanisms. These are transparent synthetic equations, not empirically calibrated parameters.}
\end{table}
"""


def adaptive_calibration_table(adaptive_assumptions: dict) -> str:
    research = adaptive_assumptions.get("researchCalibration", {})
    priors = research.get("priors", [])
    rows = []
    for prior in priors:
        rows.append(
            f"{tex_escape(prior.get('area', ''))} & "
            f"{tex_escape(prior.get('modelUse', ''))} \\\\"
        )
    if not rows:
        rows.append("none & no research calibration notes found \\\\")
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\begin{tabular}{@{}L{0.24\linewidth}L{0.68\linewidth}@{}}
\toprule
Calibration area & Use in Adaptive Bridge v1 \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\caption{Evidence-informed priors added to Adaptive Bridge v1. The table records directional model use only; it is not an empirical fit.}
    \end{table}
    """


def adaptive_coefficients_table(adaptive_assumptions: dict, limit: int = 16) -> str:
    families = adaptive_assumptions.get("portfolioAdjustmentFamilies", [])
    rows = []
    for family in families[:limit]:
        add = "; ".join(
            f"{short_coefficient_key(key)}={float(value):.3f}"
            for key, value in sorted(family.get("add", {}).items())
        )
        multiply = "; ".join(
            f"{short_coefficient_key(key)}={float(value):.3f}"
            for key, value in sorted(family.get("multiply", {}).items())
        )
        rows.append(
            f"{tex_escape(family.get('family', ''))} & {tex_escape(family.get('evidenceTier', ''))} & "
            f"{tex_escape(add or '--')} & {tex_escape(multiply or '--')} \\\\"
        )
    if not rows:
        rows.append(r"none & no configured families & -- & -- \\")
    return r"""
\begin{table}[htbp]
\centering
\scriptsize
\resizebox{\linewidth}{!}{%
\begin{tabular}{@{}L{0.22\linewidth}L{0.16\linewidth}L{0.42\linewidth}L{0.24\linewidth}@{}}
\toprule
Coefficient family & Evidence tier & Additive coefficients & Multiplier coefficients \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
}
\caption{Configured Adaptive Bridge v1 coefficient families. Coefficients are loaded from the v1 configuration and are evidence-anchored priors, not fitted causal estimates.}
\end{table}
"""


def macros(
    inventory: dict,
    portfolios: list[dict[str, str]],
    pareto_rows: list[dict[str, str]],
    epsilon_pareto_rows: list[dict[str, str]],
    uncertainty_pareto_rows: list[dict[str, str]],
    uncertainty_rows: list[dict[str, str]],
    profile_rows: list[dict[str, str]],
    robust_row: dict[str, str],
    regret_rows: list[dict[str, str]],
    tradeoff_rows: list[dict[str, str]],
    watchlist_rows: list[dict[str, str]],
    bridge_rows: list[dict[str, str]],
    sensitivity_rows: list[dict[str, str]],
    stability_rows: list[dict[str, str]],
    stability_definition_rows: list[dict[str, str]],
    assumptions: dict,
    adaptive_rows: list[dict[str, str]],
    adaptive_summary_rows: list[dict[str, str]],
    adaptive_assumptions: dict,
    review_reconciliation_rows: list[dict[str, str]],
    review_harmonization_rows: list[dict[str, str]],
    dual_review_rows: list[dict[str, str]],
    review_overlap_rows: list[dict[str, str]],
    review_rank_shift_rows: list[dict[str, str]],
) -> str:
    legislature = source_for_kind(inventory, "legislature")
    review = source_for_kind(inventory, "review")
    anti_capture = source_for_kind(inventory, "anti_capture")
    balanced = ranked(portfolios, "rank")[0]
    balanced_uncertainty = next(row for row in uncertainty_rows if row["balancedRank"] == "1")
    uncertainty_lower_bound_leader = ranked(uncertainty_rows, "uncertaintyLowerBoundRank")[0]
    balanced_overlap_count = sum(1 for row in uncertainty_rows if row["balancedIntervalRelation"] == "overlaps-balanced")
    balanced_below_count = sum(1 for row in uncertainty_rows if row["balancedIntervalRelation"] == "below-balanced")
    balanced_above_count = sum(1 for row in uncertainty_rows if row["balancedIntervalRelation"] == "above-balanced")
    minimax = ranked(regret_rows, "minimaxRegretRank")[0]
    baseline = ranked(rows_for(bridge_rows, stressProfile="baseline"), "bridgeRank")
    baseline_by_key = {row["caseKey"]: row for row in baseline}
    baseline_winner = baseline[0]
    stability_by_key = {row["caseKey"]: row for row in stability_rows}
    stability_winners_by_criterion = {
        row["criterionKey"]: row
        for row in stability_definition_rows
    }
    high_capture = rows_for(sensitivity_rows, stressProfile="high-capture-pressure")
    high_capture_by_key = {row["caseKey"]: row for row in high_capture}
    high_capture_winner = ranked(high_capture, "bridgeRank")[0]
    emergency_abuse = rows_for(sensitivity_rows, stressProfile="emergency-abuse-stress")
    emergency_abuse_by_key = {row["caseKey"]: row for row in emergency_abuse}
    emergency_winner = ranked(emergency_abuse, "bridgeRank")[0]
    federalism_capacity = rows_for(sensitivity_rows, stressProfile="federalism-agency-capacity-stress")
    federalism_capacity_by_key = {row["caseKey"]: row for row in federalism_capacity}
    adaptive_leader = ranked(adaptive_summary_rows, "adaptiveOverallRank")[0]
    adaptive_by_key = {row["portfolioKey"]: row for row in adaptive_summary_rows}
    balanced_adaptive = adaptive_by_key[portfolio_key(balanced)]
    robust_adaptive = adaptive_by_key[portfolio_key(robust_row)]

    unique_profiles = {row["profile"] for row in profile_rows}
    unique_stress_profiles = {row["stressProfile"] for row in sensitivity_rows}
    adaptive_gate_counts = {
        gate: sum(1 for row in adaptive_summary_rows if row["recommendationGate"] == gate)
        for gate in [
            "provisional shortlist",
            "calibration gray zone, not recommendation",
            "review priority, not recommendation",
            "do not recommend yet",
        ]
    }
    reconciliation_counts = {
        category: sum(1 for row in review_reconciliation_rows if row["comparisonStatus"] == category)
        for category in [
            "shared configured metric",
            "imported-only configured metric",
            "companion-only configured metric",
            "companion adaptive candidate",
        ]
    }
    dual_by_key = {row["runKey"]: row for row in dual_review_rows}
    companion_review_run = dual_by_key.get("companion-review-first-pass", {})
    harmonized_review_run = dual_by_key.get("harmonized-review-source", {})
    included_harmonized_metrics = {
        row["metricName"] for row in review_harmonization_rows if row["harmonizedAction"] == "included"
    }
    overlap_by_pair = {
        (row["leftRunKey"], row["rightRunKey"]): row
        for row in review_overlap_rows
    }
    current_harmonized_overlap = overlap_by_pair.get(("current-imported-review", "harmonized-review-source"), {})

    lines = [
        macro("LegislativeRowCount", fmt_int(legislature["rows"])),
        macro("ReviewRowCount", fmt_int(review["rows"])),
        macro("AntiCaptureRowCount", fmt_int(anti_capture["rows"])),
        macro("SourcePaperCrosswalkCount", fmt_int(len(SIBLING_SOURCE_CROSSWALK))),
        macro("ReviewSharedConfiguredMetricCount", fmt_int(reconciliation_counts["shared configured metric"])),
        macro("ReviewImportedOnlyConfiguredMetricCount", fmt_int(reconciliation_counts["imported-only configured metric"])),
        macro("ReviewCompanionOnlyConfiguredMetricCount", fmt_int(reconciliation_counts["companion-only configured metric"])),
        macro("ReviewAdaptiveCandidateCount", fmt_int(reconciliation_counts["companion adaptive candidate"])),
        macro("ReviewHarmonizedMetricCount", fmt_int(len(included_harmonized_metrics))),
        macro("DualReviewCompanionPortfolioCount", fmt_int(companion_review_run.get("portfolioCount", 0) or 0)),
        macro("DualReviewTopTwentyFiveOverlap", fmt_int(companion_review_run.get("top25OverlapWithPrimary", 0) or 0)),
        macro("DualReviewPrimaryWinnerRankInCompanion", companion_review_run.get("primaryWinnerRankInRun", "not comparable")),
        macro("HarmonizedReviewPortfolioCount", fmt_int(harmonized_review_run.get("portfolioCount", 0) or 0)),
        macro("HarmonizedReviewTopTwentyFiveOverlap", fmt_int(harmonized_review_run.get("top25OverlapWithPrimary", 0) or 0)),
        macro("HarmonizedReviewPrimaryWinnerRank", harmonized_review_run.get("primaryWinnerRankInRun", "not comparable")),
        macro("HarmonizedReviewWinnerName", harmonized_review_run.get("balancedWinner", "")),
        macro("ReviewVariantRankShiftRowCount", fmt_int(len(review_rank_shift_rows))),
        macro("CurrentHarmonizedTopHundredOverlap", fmt_int(current_harmonized_overlap.get("top100Overlap", 0) or 0)),
        macro("PortfolioCount", fmt_int(len(portfolios))),
        macro("ParetoPortfolioCount", fmt_int(len(pareto_rows))),
        macro("EpsilonParetoPortfolioCount", fmt_int(len(epsilon_pareto_rows))),
        macro("UncertaintyParetoPortfolioCount", fmt_int(len(uncertainty_pareto_rows))),
        macro("ScoringProfileCount", fmt_int(len(unique_profiles))),
        macro("BridgePeriodCount", fmt_int(assumptions["periods"])),
        macro("BridgeCaseCount", fmt_int(len(baseline))),
        macro("BridgeUnmodeledPortfolioCount", fmt_int(len(portfolios) - len(baseline))),
        macro("StressProfileCount", fmt_int(len(unique_stress_profiles))),
        macro("AdaptiveBridgePeriodCount", fmt_int(adaptive_assumptions["periods"])),
        macro("AdaptiveBridgePortfolioCount", fmt_int(len(adaptive_summary_rows))),
        macro("AdaptiveBridgeRunCount", fmt_int(len(adaptive_rows))),
        macro("AdaptiveProvisionalShortlistCount", fmt_int(adaptive_gate_counts["provisional shortlist"])),
        macro("AdaptiveCalibrationGrayZoneCount", fmt_int(adaptive_gate_counts["calibration gray zone, not recommendation"])),
        macro("AdaptiveReviewPriorityCount", fmt_int(adaptive_gate_counts["review priority, not recommendation"])),
        macro("AdaptiveDoNotRecommendCount", fmt_int(adaptive_gate_counts["do not recommend yet"])),
        macro("AdaptiveLeaderName", adaptive_leader["portfolio"]),
        macro("AdaptiveLeaderScore", fmt_float(adaptive_leader["avgAdaptiveScore"])),
        macro("AdaptiveLeaderWorstStressRank", fmt_int(adaptive_leader["worstAdaptiveRank"])),
        macro("AdaptiveLeaderMaxStressRegret", fmt_float(adaptive_leader["maxStressRegret"])),
        macro("AdaptiveLeaderGate", adaptive_leader["recommendationGate"]),
        macro("BalancedAdaptiveRank", fmt_int(balanced_adaptive["adaptiveOverallRank"])),
        macro("BalancedAdaptiveScore", fmt_float(balanced_adaptive["avgAdaptiveScore"])),
        macro("BalancedAdaptiveWorstStressRank", fmt_int(balanced_adaptive["worstAdaptiveRank"])),
        macro("BalancedAdaptiveMaxStressRegret", fmt_float(balanced_adaptive["maxStressRegret"])),
        macro("BalancedAdaptiveGate", balanced_adaptive["recommendationGate"]),
        macro("RobustAdaptiveRank", fmt_int(robust_adaptive["adaptiveOverallRank"])),
        macro("RobustAdaptiveScore", fmt_float(robust_adaptive["avgAdaptiveScore"])),
        macro("RobustAdaptiveWorstStressRank", fmt_int(robust_adaptive["worstAdaptiveRank"])),
        macro("RobustAdaptiveGate", robust_adaptive["recommendationGate"]),
        macro("BalancedWinnerName", portfolio(balanced)),
        macro("BalancedWinnerScore", fmt_float(balanced["overallScore"])),
        macro("BalancedWinnerUncertaintyLow", fmt_float(balanced["uncertaintyLow"])),
        macro("BalancedWinnerUncertaintyHigh", fmt_float(balanced["uncertaintyHigh"])),
        macro("BalancedWinnerUncertaintyBand", fmt_float(balanced["modelUncertaintyBand"])),
        macro("BalancedWinnerMinimaxRegretRank", fmt_int(balanced["minimaxRegretRank"])),
        macro("BalancedWinnerMaxProfileRegret", fmt_float(balanced["maxProfileRegret"])),
        macro("BalancedUncertaintyOverlapCount", fmt_int(balanced_overlap_count)),
        macro("BalancedUncertaintyBelowCount", fmt_int(balanced_below_count)),
        macro("BalancedUncertaintyAboveCount", fmt_int(balanced_above_count)),
        macro("BalancedUncertaintyLowerBoundRank", fmt_int(balanced_uncertainty["uncertaintyLowerBoundRank"])),
        macro("UncertaintyLowerBoundWinnerName", portfolio(uncertainty_lower_bound_leader)),
        macro("UncertaintyLowerBoundWinnerBalancedRank", fmt_int(uncertainty_lower_bound_leader["balancedRank"])),
        macro("BalancedWinnerDelivery", fmt_float(balanced["policyDelivery"])),
        macro("BalancedWinnerPublicAlignment", fmt_float(balanced["publicAlignment"])),
        macro("BalancedWinnerRightsSafeguard", fmt_float(balanced["rightsSafeguard"])),
        macro("BalancedWinnerCaptureResistance", fmt_float(balanced["captureResistance"])),
        macro("BalancedWinnerLegitimacy", fmt_float(balanced["legitimacy"])),
        macro("BalancedWinnerComplexity", fmt_float(balanced["complexityScore"])),
        macro("RobustWinnerName", portfolio(robust_row)),
        macro("RobustWinnerScore", fmt_float(robust_row["robustScore"])),
        macro("RobustWinnerBalancedRank", fmt_int(robust_row["rank"])),
        macro("RobustWinnerAverageProfileRank", fmt_float(robust_row["averageProfileRank"])),
        macro("RobustWinnerWorstProfileRank", fmt_int(robust_row["worstProfileRank"])),
        macro("RobustWinnerTopTwentyFiveCount", fmt_int(robust_row["top25ProfileCount"])),
        macro("MinimaxWinnerName", portfolio(minimax)),
        macro("MinimaxWinnerBalancedRank", fmt_int(minimax["balancedRank"])),
        macro("MinimaxWinnerMaxProfileRegret", fmt_float(minimax["maxProfileRegret"])),
        macro("FragileWatchlistCount", fmt_int(len(watchlist_rows))),
        macro("BaselineBridgeWinnerName", baseline_winner["caseLabel"]),
        macro("BaselineBridgeWinnerPortfolio", portfolio(baseline_winner)),
        macro("BaselineBridgeWinnerScore", fmt_float(baseline_winner["bridgeScore"])),
        macro("BalancedBridgeScore", fmt_float(baseline_by_key["balanced-winner"]["bridgeScore"])),
        macro("BalancedBridgeAverageDelivery", fmt_float(baseline_by_key["balanced-winner"]["averageDelivery"])),
        macro("BalancedBridgeFinalPolicyQuality", fmt_float(baseline_by_key["balanced-winner"]["finalPolicyQuality"])),
        macro("EfficiencyCautionAverageDelivery", fmt_float(baseline_by_key["efficiency-caution"]["averageDelivery"])),
        macro("EfficiencyCautionFinalPolicyQuality", fmt_float(baseline_by_key["efficiency-caution"]["finalPolicyQuality"])),
        macro("EfficiencyCautionFinalPublicAlignment", fmt_float(baseline_by_key["efficiency-caution"]["finalPublicAlignment"])),
        macro("CurrentBaselineAverageDelivery", fmt_float(baseline_by_key["current-system-baseline"]["averageDelivery"])),
        macro("CurrentBaselineFinalPolicyQuality", fmt_float(baseline_by_key["current-system-baseline"]["finalPolicyQuality"])),
        macro("BalancedStressWins", fmt_int(stability_by_key["balanced-winner"]["stressWins"])),
        macro("BalancedStressTopTwo", fmt_int(stability_by_key["balanced-winner"]["topTwoStressCount"])),
        macro("BalancedAverageStressRank", fmt_float(stability_by_key["balanced-winner"]["averageStressRank"])),
        macro("BalancedWinTopTwoStabilityRank", fmt_int(stability_by_key["balanced-winner"]["winTopTwoStabilityRank"])),
        macro("BalancedAverageRankStabilityRank", fmt_int(stability_by_key["balanced-winner"]["averageRankStabilityRank"])),
        macro("BalancedAverageScoreStabilityRank", fmt_int(stability_by_key["balanced-winner"]["averageScoreStabilityRank"])),
        macro("BalancedMinimaxStressRegretRank", fmt_int(stability_by_key["balanced-winner"]["minimaxStressRegretRank"])),
        macro("WinTopTwoStressWinnerName", stability_winners_by_criterion["win-top-two"]["winnerCaseLabel"]),
        macro("AverageRankStressWinnerName", stability_winners_by_criterion["average-rank"]["winnerCaseLabel"]),
        macro("AverageScoreStressWinnerName", stability_winners_by_criterion["average-score"]["winnerCaseLabel"]),
        macro("MinimaxStressRegretWinnerName", stability_winners_by_criterion["minimax-stress-regret"]["winnerCaseLabel"]),
        macro("ScoreSpreadStressWinnerName", stability_winners_by_criterion["score-spread"]["winnerCaseLabel"]),
        macro("HighCaptureWinnerName", high_capture_winner["caseLabel"]),
        macro("HighCaptureWinnerPortfolio", portfolio(high_capture_winner)),
        macro("BalancedHighCaptureRank", fmt_int(high_capture_by_key["balanced-winner"]["bridgeRank"])),
        macro("BalancedEmergencyAbuseRank", fmt_int(emergency_abuse_by_key["balanced-winner"]["bridgeRank"])),
        macro("EmergencyAbuseWinnerName", emergency_winner["caseLabel"]),
        macro("BalancedFederalismCapacityRank", fmt_int(federalism_capacity_by_key["balanced-winner"]["bridgeRank"])),
        macro("LegitimacyAverageStressRank", fmt_float(stability_by_key["legitimacy-winner"]["averageStressRank"])),
        macro("LegitimacyStressWins", fmt_int(stability_by_key["legitimacy-winner"]["stressWins"])),
        macro("LegitimacyStressTopTwo", fmt_int(stability_by_key["legitimacy-winner"]["topTwoStressCount"])),
        macro("EfficiencyCautionStressWins", fmt_int(stability_by_key["efficiency-caution"]["stressWins"])),
        macro("EfficiencyCautionAverageStressRank", fmt_float(stability_by_key["efficiency-caution"]["averageStressRank"])),
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=REPORTS)
    parser.add_argument("--output-dir", type=Path, default=GENERATED)
    return parser.parse_args()


def main() -> None:
    global REPORTS, GENERATED
    args = parse_args()
    REPORTS = args.reports_dir
    GENERATED = args.output_dir

    portfolio_module = load_portfolio_module()
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
    adaptive_assumptions = read_json("adaptive-bridge-v1-assumptions.json")

    balanced = ranked(portfolios, "rank")[0]
    robust = ranked(robustness_rows, "robustRank")[0]
    baseline = rows_for(bridge_rows, stressProfile="baseline")
    high_capture = rows_for(sensitivity_rows, stressProfile="high-capture-pressure")
    provenance_table, provenance = source_provenance(inventory)
    crosswalk_table, crosswalk = source_paper_crosswalk()

    write_fragment(
        "report-macros.tex",
        macros(
            inventory,
            portfolios,
            pareto_rows,
            epsilon_pareto_rows,
            uncertainty_pareto_rows,
            uncertainty_rows,
            profile_rows,
            robust,
            regret_rows,
            tradeoff_rows,
            watchlist_rows,
            bridge_rows,
            sensitivity_rows,
            stability_rows,
            stability_definition_rows,
            assumptions,
            adaptive_rows,
            adaptive_summary_rows,
            adaptive_assumptions,
            review_reconciliation_rows,
            review_harmonization_rows,
            dual_review_rows,
            review_overlap_rows,
            review_rank_shift_rows,
        ),
    )
    write_fragment("source-summary-table.tex", source_summary_table(inventory))
    write_fragment("source-paper-crosswalk-table.tex", crosswalk_table)
    write_fragment("review-source-reconciliation-table.tex", review_reconciliation_table(review_reconciliation_rows))
    write_fragment("review-harmonization-manifest-table.tex", review_harmonization_manifest_table(review_harmonization_rows))
    write_fragment("dual-review-sensitivity-table.tex", dual_review_sensitivity_table(dual_review_rows))
    write_fragment("review-variant-overlap-table.tex", review_variant_overlap_table(review_overlap_rows))
    write_fragment("review-variant-rank-shift-table.tex", review_variant_rank_shift_table(review_rank_shift_rows))
    write_fragment("balanced-result-table.tex", balanced_result_table(balanced))
    write_fragment("profile-winners-table.tex", profile_winners_table(profile_rows))
    write_fragment("robustness-result-table.tex", robustness_table(robust))
    write_fragment("uncertainty-resolution-table.tex", uncertainty_resolution_table(uncertainty_rows, len(portfolios)))
    write_fragment("uncertainty-summary-table.tex", uncertainty_summary_table(tradeoff_rows))
    write_fragment("candidate-synthesis-table.tex", candidate_synthesis_table(tradeoff_rows, robust, bridge_rows, adaptive_summary_rows))
    write_fragment("minimax-regret-table.tex", minimax_regret_table(regret_rows))
    write_fragment("profile-tradeoff-table.tex", profile_tradeoff_table(tradeoff_rows))
    write_fragment("fragile-watchlist-table.tex", fragile_watchlist_table(watchlist_rows))
    write_fragment(
        "speculative-agenda-table.tex",
        speculative_agenda_table(portfolio_module.SPECULATIVE_MODELING_AGENDA),
    )
    write_fragment(
        "pareto-summary-table.tex",
        pareto_summary_table(
            len(portfolios),
            len(pareto_rows),
            len(epsilon_pareto_rows),
            len(uncertainty_pareto_rows),
        ),
    )
    write_fragment("bridge-ranking-table.tex", bridge_ranking_table(baseline))
    write_fragment("stress-stability-table.tex", stress_stability_table(stability_rows))
    write_fragment("stress-stability-definitions-table.tex", stress_stability_definitions_table(stability_definition_rows))
    write_fragment("bridge-case-scope-table.tex", bridge_case_scope_table(baseline, len(portfolios)))
    write_fragment("high-capture-stress-table.tex", high_capture_table(high_capture))
    write_fragment("figure-bridge-baseline.tex", bridge_baseline_figure(baseline))
    write_fragment("figure-stress-stability.tex", stress_stability_figure(stability_rows))
    write_fragment("figure-high-capture-exception.tex", high_capture_figure(high_capture))
    write_fragment("adaptive-bridge-v1-leaders-table.tex", adaptive_leaders_table(adaptive_summary_rows))
    write_fragment("adaptive-bridge-v1-gate-table.tex", adaptive_gate_table(adaptive_summary_rows))
    write_fragment("adaptive-bridge-v1-stress-winners-table.tex", adaptive_stress_winners_table(adaptive_rows))
    write_fragment("adaptive-bridge-v1-mechanisms-table.tex", adaptive_mechanisms_table(adaptive_assumptions))
    write_fragment("adaptive-bridge-v1-calibration-table.tex", adaptive_calibration_table(adaptive_assumptions))
    write_fragment("adaptive-bridge-v1-coefficients-table.tex", adaptive_coefficients_table(adaptive_assumptions))
    write_fragment("source-provenance-table.tex", provenance_table)
    write_fragment("diagnostic-formulas-table.tex", diagnostic_formula_table())
    write_fragment("profile-weights-table.tex", profile_weights_table(portfolio_module.SCORING_PROFILES))
    write_fragment("bridge-score-weights-table.tex", bridge_score_weights_table(assumptions))
    write_fragment("stress-modifiers-table.tex", stress_modifier_table(assumptions))
    write_json("source-provenance.json", provenance)
    write_json("source-paper-crosswalk.json", crosswalk)

    generated = sorted(path.name for path in GENERATED.glob("*.tex"))
    print(f"Wrote {len(generated)} generated LaTeX fragments to {GENERATED}")


if __name__ == "__main__":
    main()
