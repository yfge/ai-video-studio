#!/usr/bin/env python3
"""Enforce lightweight repository contracts for harness-first development."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_LIMIT = 300
SERVICE_LIMIT = 250
TS_LIMIT = 250
PAGE_LIMIT = 200
HANDLER_LIMIT = 50

ALLOWED_OVERSIZE = {
    "ai-pic-backend/app/api/v1/endpoints/scripts_legacy.py": 2101,
    "ai-pic-backend/app/services/dialogue_audio_service.py": 1720,
    "ai-pic-backend/app/services/ai_service_manager.py": 1510,
    "ai-pic-backend/app/services/script_agent.py": 1479,
    "ai-pic-backend/app/services/voice_catalog.py": 1171,
    "ai-pic-frontend/src/app/episodes/[id]/storyboard/page.tsx": 3466,
    "ai-pic-frontend/src/components/shared/modals/UserDetailsModal.tsx": 643,
    "ai-pic-frontend/src/app/admin/users/page.tsx": 571,
}
LEGACY_IMPORT_RE = re.compile(
    r"(scripts_legacy|dialogue_audio_service|ai_service_manager)"
)
QUERY_RE = re.compile(r"\b(?:db|session|self\.db|self\.session)\.query\(")
DECORATOR_RE = re.compile(r"^\s*@router\.(get|post|put|patch|delete)")
DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "files", nargs="*", help="Optional changed files for diff-sensitive rules"
    )
    return parser.parse_args()


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"[check_repo_contracts] {error}", file=sys.stderr)
    return 1 if errors else 0


def relative(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def line_count(path: Path) -> int:
    return sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore"))


def check_file_sizes(paths: list[Path], errors: list[str]) -> None:
    for path in paths:
        rel = relative(path)
        if "__pycache__" in rel or rel.endswith(".d.ts"):
            continue
        count = line_count(path)
        limit = PYTHON_LIMIT if path.suffix == ".py" else TS_LIMIT
        if "/services/" in rel and path.suffix == ".py":
            limit = SERVICE_LIMIT
        if (
            "/src/app/" in rel
            and path.suffix in {".ts", ".tsx"}
            and rel.endswith("/page.tsx")
        ):
            limit = PAGE_LIMIT
        allowed = ALLOWED_OVERSIZE.get(rel)
        if allowed is not None and count <= allowed:
            continue
        if count > limit:
            errors.append(f"{rel} has {count} lines (limit {limit})")


def check_changed_files(changed_files: list[Path], errors: list[str]) -> None:
    default_scenarios = read_text(REPO_ROOT / "scripts" / "harness" / "scenarios.py")
    for path in changed_files:
        rel = relative(path)
        if not rel.startswith(("ai-pic-backend/app/", "ai-pic-frontend/src/")):
            continue
        text = read_text(path)
        if rel.startswith("ai-pic-backend/app/") and LEGACY_IMPORT_RE.search(text):
            errors.append(f"{rel} introduces or keeps legacy choke-point imports")
        if rel.startswith("ai-pic-frontend/src/") and LEGACY_IMPORT_RE.search(text):
            errors.append(f"{rel} references backend legacy choke-point names")
        if (
            rel.startswith("ai-pic-backend/app/")
            and "/repositories/" not in rel
            and QUERY_RE.search(text)
        ):
            errors.append(f"{rel} uses direct SQLAlchemy queries outside repositories")
        if rel.startswith("ai-pic-backend/app/api/v1/endpoints/"):
            max_handler = longest_route_handler(text)
            if max_handler > HANDLER_LIMIT:
                errors.append(
                    f"{rel} has a route handler with {max_handler} lines (limit {HANDLER_LIMIT})"
                )
            if "login_smoke" not in default_scenarios:
                errors.append(
                    "scripts/harness/scenarios.py must define default browser scenarios"
                )
        if (
            rel.startswith("ai-pic-frontend/src/app/")
            and "episode_timeline_smoke" not in default_scenarios
        ):
            errors.append(
                "scripts/harness/scenarios.py must define episode_timeline_smoke"
            )


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


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


def main() -> int:
    args = parse_args()
    changed_files = [
        REPO_ROOT / item for item in args.files if (REPO_ROOT / item).is_file()
    ]
    errors: list[str] = []
    if changed_files:
        size_candidates = [
            path
            for path in changed_files
            if relative(path).startswith(
                ("ai-pic-backend/app/", "ai-pic-frontend/src/", "scripts/")
            )
        ]
        check_file_sizes(size_candidates, errors)
        check_changed_files(changed_files, errors)
    else:
        print(
            "[check_repo_contracts] no changed-file diff rules were provided; skipping diff-sensitive checks"
        )
    return fail(errors)


if __name__ == "__main__":
    raise SystemExit(main())
