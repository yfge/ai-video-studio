#!/usr/bin/env python3
"""Enforce repository contracts for harness-first development."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.contract_audit_core import scan_candidates
from scripts.contract_audit_reporting import (
    build_report,
    persist_reports,
    print_failures,
    should_fail,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("diff", "audit"),
        default="diff",
        help="diff checks changed files; audit scans the whole repository and writes reports",
    )
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--report-md", type=Path)
    parser.add_argument(
        "--fail-on-violations",
        action="store_true",
        help="In audit mode, exit non-zero when violations are present",
    )
    parser.add_argument(
        "files", nargs="*", help="Changed files for diff mode; ignored by audit mode"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = scan_candidates(args.mode, args.files)
    if args.mode == "diff" and not paths:
        print("[check_repo_contracts] no changed-file diff rules were provided; skipping diff-sensitive checks")
        return 0
    report = build_report(
        args.mode, paths, fail_on_violations=args.fail_on_violations
    )
    persist_reports(report, args.report_json, args.report_md)
    if should_fail(report):
        print_failures(report)
        return 1
    print(f"[check_repo_contracts] ok ({args.mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
