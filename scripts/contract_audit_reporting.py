#!/usr/bin/env python3
"""Repository contract report builders and renderers."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.check_repo_docs import collect_doc_errors
from scripts.contract_audit_core import (
    AUDIT_ROOT,
    collect_direct_queries,
    collect_legacy_references,
    collect_oversized_files,
    collect_route_handlers,
    relative,
    summarize,
)


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_report(mode: str, paths: list[Path], *, fail_on_violations: bool) -> dict[str, Any]:
    report = {
        "mode": mode,
        "generated_at": utc_now(),
        "checked_files": len(paths),
        "checked_paths": [relative(path) for path in paths] if mode == "diff" else [],
        "docs_drift": {"errors": collect_doc_errors()},
        "violations": {
            "oversized_files": collect_oversized_files(paths, mode=mode),
            "route_handlers": collect_route_handlers(paths),
            "direct_queries": collect_direct_queries(paths),
            "legacy_references": collect_legacy_references(paths),
        },
    }
    report["summary"] = summarize(report)
    report["exit_on_violation"] = mode == "diff" or fail_on_violations
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    violations = report["violations"]
    docs_errors = report["docs_drift"]["errors"]
    lines = [
        "# Repository Contracts Summary",
        "",
        f"- Mode: `{report['mode']}`",
        f"- Generated: `{report['generated_at']}`",
        f"- Checked files: `{summary['checked_files']}`",
        "",
        "## Counts",
        "",
        f"- Oversized files: `{summary['oversized_files']}`",
        f"- Route handlers over 50 lines: `{summary['route_handler_violations']}`",
        f"- Direct SQLAlchemy query files: `{summary['direct_query_files']}`",
        f"- Legacy reference files: `{summary['legacy_reference_files']}`",
        f"- Docs drift errors: `{summary['docs_drift_errors']}`",
        "",
    ]
    if docs_errors:
        lines.extend(["## Docs Drift", ""])
        lines.extend(f"- {error}" for error in docs_errors[:10])
        lines.append("")
    for title, items, metric_key in (
        ("Oversized Files", violations["oversized_files"], "line_count"),
        ("Route Handler Violations", violations["route_handlers"], "handler_lines"),
        ("Direct Query Files", violations["direct_queries"], "query_hits"),
        ("Legacy References", violations["legacy_references"], None),
    ):
        if not items:
            continue
        lines.extend([f"## {title}", ""])
        for item in items[:10]:
            metric = f" `{item[metric_key]}`" if metric_key else ""
            baseline = " (baseline exemption)" if item.get("baseline_exemption") else ""
            lines.append(f"- `{item['path']}`{metric}{baseline}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def persist_reports(report: dict[str, Any], report_json: Path | None, report_md: Path | None) -> None:
    if report["mode"] == "audit":
        report_json = report_json or AUDIT_ROOT / "contracts-report.json"
        report_md = report_md or AUDIT_ROOT / "contracts-summary.md"
    if report_json:
        write_json(report_json, report)
    if report_md:
        report_md.parent.mkdir(parents=True, exist_ok=True)
        report_md.write_text(render_markdown(report), encoding="utf-8")


def should_fail(report: dict[str, Any]) -> bool:
    summary = report["summary"]
    if not report["exit_on_violation"]:
        return False
    return any(
        summary[key] > 0
        for key in (
            "oversized_files",
            "route_handler_violations",
            "direct_query_files",
            "legacy_reference_files",
            "docs_drift_errors",
        )
    )


def print_failures(report: dict[str, Any]) -> None:
    for error in report["docs_drift"]["errors"]:
        print(f"[check_repo_contracts] {error}", file=sys.stderr)
    for key, label, metric_key in (
        ("oversized_files", "oversized", "line_count"),
        ("route_handlers", "route handler", "handler_lines"),
        ("direct_queries", "direct query", "query_hits"),
        ("legacy_references", "legacy reference", None),
    ):
        for item in report["violations"][key]:
            detail = f" ({metric_key}={item[metric_key]})" if metric_key else ""
            print(f"[check_repo_contracts] {label}: {item['path']}{detail}", file=sys.stderr)
