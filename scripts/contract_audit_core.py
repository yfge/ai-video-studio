#!/usr/bin/env python3
"""Core repository contract scanning helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
AUDIT_ROOT = REPO_ROOT / "artifacts" / "repo_audit" / "latest"

PYTHON_LIMIT = 300
SERVICE_LIMIT = 250
TS_LIMIT = 250
PAGE_LIMIT = 200
HANDLER_LIMIT = 50

ALLOWED_OVERSIZE = {
    "ai-pic-backend/app/services/ai_service_manager.py": 1510,
    "ai-pic-backend/app/services/script_agent.py": 1479,
    "ai-pic-backend/app/services/voice_catalog.py": 1171,
    "ai-pic-frontend/src/components/shared/modals/UserDetailsModal.tsx": 643,
    "ai-pic-frontend/src/app/admin/users/page.tsx": 571,
}
ALLOWED_ROUTE_HANDLERS: dict[str, int] = {}
ALLOWED_DIRECT_QUERIES: dict[str, int] = {}
LEGACY_IMPORT_RE = re.compile(r"(ai_service_manager|script_agent)")
QUERY_RE = re.compile(r"\b(?:db|session|self\.db|self\.session)\.query\(")
DECORATOR_RE = re.compile(r"^\s*@router\.(get|post|put|patch|delete)")
DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+")
SOURCE_ROOTS = (
    REPO_ROOT / "ai-pic-backend" / "app",
    REPO_ROOT / "ai-pic-backend" / "tests",
    REPO_ROOT / "ai-pic-backend" / "scripts",
    REPO_ROOT / "ai-pic-frontend" / "src",
    REPO_ROOT / "scripts",
)


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def line_count(path: Path) -> int:
    return sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore"))


def is_source_file(path: Path) -> bool:
    rel = relative(path)
    return rel.startswith(
        (
            "ai-pic-backend/app/",
            "ai-pic-backend/tests/",
            "ai-pic-backend/scripts/",
            "ai-pic-frontend/src/",
            "scripts/",
        )
    ) and path.suffix in {".py", ".ts", ".tsx"}


def scan_candidates(mode: str, files: list[str]) -> list[Path]:
    if mode == "audit":
        paths: list[Path] = []
        for root in SOURCE_ROOTS:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_file() and is_source_file(path):
                    paths.append(path)
        return sorted(paths)
    candidates = [REPO_ROOT / item for item in files if (REPO_ROOT / item).is_file()]
    return [path for path in candidates if is_source_file(path)]


def file_limit(path: Path) -> int:
    rel = relative(path)
    if path.suffix == ".py":
        return SERVICE_LIMIT if "/services/" in rel else PYTHON_LIMIT
    if rel.endswith("/page.tsx") and "/src/app/" in rel:
        return PAGE_LIMIT
    return TS_LIMIT


def collect_oversized_files(paths: list[Path], *, mode: str) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for path in paths:
        rel = relative(path)
        limit = file_limit(path)
        count = line_count(path)
        allowed = ALLOWED_OVERSIZE.get(rel)
        baseline_exemption = allowed is not None and count <= allowed
        if count <= limit and not baseline_exemption:
            continue
        if mode == "diff" and baseline_exemption:
            continue
        if count <= limit:
            continue
        violations.append(
            {
                "path": rel,
                "line_count": count,
                "limit": limit,
                "baseline_exemption": baseline_exemption,
                "allowed_limit": allowed,
            }
        )
    return sorted(violations, key=lambda item: (-item["line_count"], item["path"]))


def longest_route_handler(text: str) -> int:
    lines = text.splitlines()
    max_len = 0
    index = 0
    while index < len(lines):
        if not DECORATOR_RE.match(lines[index]):
            index += 1
            continue
        while index < len(lines) and lines[index].lstrip().startswith("@"):
            index += 1
        start = index
        while index < len(lines):
            index += 1
            if index >= len(lines):
                break
            if lines[index].lstrip().startswith("@") or (
                DEF_RE.match(lines[index]) and not lines[index].startswith((" ", "\t"))
            ):
                break
        end = index
        while end > start and not lines[end - 1].strip():
            end -= 1
        max_len = max(max_len, end - start)
    return max_len


def collect_route_handlers(paths: list[Path], *, mode: str) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for path in paths:
        rel = relative(path)
        if not rel.startswith("ai-pic-backend/app/api/v1/endpoints/"):
            continue
        length = longest_route_handler(read_text(path))
        if length > HANDLER_LIMIT:
            allowed = ALLOWED_ROUTE_HANDLERS.get(rel)
            baseline_exemption = allowed is not None and length <= allowed
            if mode == "diff" and baseline_exemption:
                continue
            violations.append(
                {
                    "path": rel,
                    "handler_lines": length,
                    "limit": HANDLER_LIMIT,
                    "baseline_exemption": baseline_exemption,
                    "allowed_limit": allowed,
                }
            )
    return sorted(violations, key=lambda item: (-item["handler_lines"], item["path"]))


def collect_direct_queries(paths: list[Path], *, mode: str) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for path in paths:
        rel = relative(path)
        if not rel.startswith("ai-pic-backend/app/") or "/repositories/" in rel:
            continue
        hits = len(QUERY_RE.findall(read_text(path)))
        if hits:
            allowed = ALLOWED_DIRECT_QUERIES.get(rel)
            baseline_exemption = allowed is not None and hits <= allowed
            if mode == "diff" and baseline_exemption:
                continue
            violations.append(
                {
                    "path": rel,
                    "query_hits": hits,
                    "baseline_exemption": baseline_exemption,
                    "allowed_limit": allowed,
                }
            )
    return sorted(violations, key=lambda item: (-item["query_hits"], item["path"]))


def collect_legacy_references(paths: list[Path]) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for path in paths:
        rel = relative(path)
        if not rel.startswith(("ai-pic-backend/app/", "ai-pic-frontend/src/")):
            continue
        if LEGACY_IMPORT_RE.search(read_text(path)):
            violations.append({"path": rel, "pattern": LEGACY_IMPORT_RE.pattern})
    return sorted(violations, key=lambda item: item["path"])


def summarize(report: dict[str, Any]) -> dict[str, Any]:
    violations = report["violations"]
    docs_errors = report["docs_drift"]["errors"]
    return {
        "oversized_files": len(violations["oversized_files"]),
        "route_handler_violations": len(violations["route_handlers"]),
        "direct_query_files": len(violations["direct_queries"]),
        "legacy_reference_files": len(violations["legacy_references"]),
        "docs_drift_errors": len(docs_errors),
        "checked_files": report["checked_files"],
    }
