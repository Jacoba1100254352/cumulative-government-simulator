#!/usr/bin/env python3
"""Fail on LaTeX log issues that make the generated PDF unfit for review."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


FAIL_PATTERNS = [
    re.compile(r"^! "),
    re.compile(r"Undefined control sequence"),
    re.compile(r"LaTeX Error"),
    re.compile(r"Package .* Error"),
    re.compile(r"Overfull \\hbox"),
    re.compile(r"Overfull \\vbox"),
    re.compile(r"Underfull \\hbox"),
    re.compile(r"Underfull \\vbox"),
    re.compile(r"LaTeX Warning: (Reference|Citation).*undefined"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text = args.log.read_text(encoding="utf-8", errors="replace")
    failures: list[str] = []
    for line in text.splitlines():
        if any(pattern.search(line) for pattern in FAIL_PATTERNS):
            failures.append(line)
    if failures:
        joined = "\n".join(failures[:20])
        raise SystemExit(f"LaTeX log check failed for {args.log}:\n{joined}")
    print(f"LaTeX log clean: {args.log}")


if __name__ == "__main__":
    main()
