#!/usr/bin/env python3
"""Verify that the public paper PDF reflects the current generated build."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PAPER_PDF = ROOT / "paper" / "main.pdf"
DEFAULT_BUILD_PDF = ROOT / "paper" / "build" / "main.pdf"
DEFAULT_PAPER_TEX = ROOT / "paper" / "main.tex"
DEFAULT_GENERATED_DIR = ROOT / "paper" / "generated"
DEFAULT_REPORTS_DIR = ROOT / "reports"
DEFAULT_CONFIGS = [
    ROOT / "config" / "interbranch-bridge-v0.json",
    ROOT / "config" / "adaptive-bridge-v1.json",
]

REPORT_PATTERNS = ("*.csv", "*.json")
SCRIPT_DEPENDENCIES = [
    ROOT / "scripts" / "build_portfolios.py",
    ROOT / "scripts" / "build_interbranch_bridge.py",
    ROOT / "scripts" / "build_adaptive_bridge.py",
    ROOT / "paper" / "scripts" / "generate_tables.py",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-pdf", type=Path, default=DEFAULT_PAPER_PDF)
    parser.add_argument("--build-pdf", type=Path, default=DEFAULT_BUILD_PDF)
    parser.add_argument("--paper-tex", type=Path, default=DEFAULT_PAPER_TEX)
    parser.add_argument("--generated-dir", type=Path, default=DEFAULT_GENERATED_DIR)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--config", type=Path, action="append", dest="configs")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_exists(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path}")


def collect_report_artifacts(reports_dir: Path) -> list[Path]:
    artifacts: list[Path] = []
    for pattern in REPORT_PATTERNS:
        artifacts.extend(path for path in reports_dir.glob(pattern) if path.is_file())
    return sorted(set(artifacts))


def collect_generated_artifacts(generated_dir: Path) -> list[Path]:
    return sorted(path for path in generated_dir.glob("*") if path.is_file())


def collect_source_artifacts(inventory_path: Path) -> list[Path]:
    if not inventory_path.exists():
        return []
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    return sorted(Path(source["path"]) for source in inventory.get("sources", []))


def require_pdf_newer_than(pdf: Path, dependencies: list[Path]) -> None:
    pdf_mtime = pdf.stat().st_mtime
    stale = [
        dependency
        for dependency in dependencies
        if dependency.exists() and dependency.stat().st_mtime > pdf_mtime
    ]
    if stale:
        newest = max(stale, key=lambda path: path.stat().st_mtime)
        raise SystemExit(
            "paper/main.pdf is stale. Run `make paper`.\n"
            f"Newest newer dependency: {newest}"
        )


def require_public_pdf_matches_build(public_pdf: Path, build_pdf: Path) -> None:
    public_hash = sha256(public_pdf)
    build_hash = sha256(build_pdf)
    if public_hash != build_hash:
        raise SystemExit(
            "paper/main.pdf does not match paper/build/main.pdf. Run `make paper`."
        )


def require_source_hashes_current(provenance_path: Path) -> None:
    require_exists(provenance_path, "source provenance")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    mismatches = []
    for source in provenance.get("sources", []):
        path = Path(source["path"])
        require_exists(path, f"source artifact for {source.get('label', source.get('kind', 'unknown'))}")
        current = sha256(path)
        expected = source.get("sha256")
        if current != expected:
            mismatches.append((path, expected, current))
    if mismatches:
        path, expected, current = mismatches[0]
        raise SystemExit(
            "Imported source artifact changed after paper generation. Run `make paper`.\n"
            f"Changed source: {path}\n"
            f"Expected SHA-256: {expected}\n"
            f"Current SHA-256:  {current}"
        )


def require_crosswalk_hashes_current(crosswalk_path: Path) -> None:
    require_exists(crosswalk_path, "source-paper crosswalk")
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))
    mismatches = []
    for source in crosswalk.get("sources", []):
        project = source.get("project", "unknown project")
        for artifact_kind in ["paper", "pdf", "report"]:
            artifact = source.get(artifact_kind, {})
            path_text = artifact.get("path")
            if not path_text:
                continue
            path = Path(path_text)
            if artifact.get("exists") is False:
                if path.exists():
                    mismatches.append((path, project, artifact_kind, "missing", sha256(path)))
                continue
            require_exists(path, f"{artifact_kind} artifact for {project}")
            expected = artifact.get("sha256")
            current = sha256(path)
            if expected and current != expected:
                mismatches.append((path, project, artifact_kind, expected, current))
    if mismatches:
        path, project, artifact_kind, expected, current = mismatches[0]
        raise SystemExit(
            "Referenced sibling paper/report artifact changed after paper generation. Run `make paper`.\n"
            f"Project: {project}\n"
            f"Artifact kind: {artifact_kind}\n"
            f"Changed artifact: {path}\n"
            f"Expected SHA-256: {expected}\n"
            f"Current SHA-256:  {current}"
        )


def main() -> None:
    args = parse_args()
    require_exists(args.paper_pdf, "public paper PDF")
    require_exists(args.build_pdf, "built paper PDF")
    require_exists(args.paper_tex, "paper LaTeX source")
    require_exists(args.generated_dir, "generated paper directory")
    require_exists(args.reports_dir, "reports directory")

    dependencies = [
        args.paper_tex,
        *(args.configs or DEFAULT_CONFIGS),
        *SCRIPT_DEPENDENCIES,
        *collect_generated_artifacts(args.generated_dir),
        *collect_report_artifacts(args.reports_dir),
        *collect_source_artifacts(args.reports_dir / "source-inventory.json"),
    ]
    require_pdf_newer_than(args.paper_pdf, sorted(set(dependencies)))
    require_public_pdf_matches_build(args.paper_pdf, args.build_pdf)
    require_source_hashes_current(args.generated_dir / "source-provenance.json")
    require_crosswalk_hashes_current(args.generated_dir / "source-paper-crosswalk.json")
    print(f"Paper PDF fresh: {args.paper_pdf}")


if __name__ == "__main__":
    main()
