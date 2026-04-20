#!/usr/bin/env python3
"""Check repository documentation drift for the harness foundation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_ROOT_DOCS = [
    "ARCHITECTURE.md",
    "FRONTEND.md",
    "RELIABILITY.md",
    "SECURITY.md",
    "QUALITY_SCORE.md",
]
REQUIRED_DOC_INDEX_ENTRIES = [
    "docs/generated/db-schema.md",
    "docs/exec-plans/active/",
    "docs/exec-plans/completed/",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def ensure_mirrors(errors: list[str]) -> None:
    agents = REPO_ROOT / "AGENTS.md"
    for mirror_name in ("CLAUDE.md", "GEMINI.md"):
        mirror = REPO_ROOT / mirror_name
        if not mirror.exists():
            errors.append(f"Missing mirror file: {mirror_name}")
            continue
        if mirror.is_symlink():
            if mirror.resolve() != agents.resolve():
                errors.append(f"{mirror_name} must resolve to AGENTS.md")
            continue
        if read_text(mirror) != read_text(agents):
            errors.append(f"{mirror_name} must match AGENTS.md exactly")


def ensure_required_docs(errors: list[str]) -> None:
    for rel_path in REQUIRED_ROOT_DOCS:
        path = REPO_ROOT / rel_path
        if not path.exists():
            errors.append(f"Missing required root doc: {rel_path}")
    generated = REPO_ROOT / "docs" / "generated" / "db-schema.md"
    if not generated.exists():
        errors.append("Missing generated schema summary: docs/generated/db-schema.md")
    for rel_dir in ("docs/exec-plans/active", "docs/exec-plans/completed"):
        path = REPO_ROOT / rel_dir
        if not path.exists():
            errors.append(f"Missing required plan directory: {rel_dir}")


def ensure_docs_index(errors: list[str]) -> None:
    index_text = read_text(REPO_ROOT / "docs" / "README.md")
    for entry in REQUIRED_DOC_INDEX_ENTRIES:
        if entry not in index_text:
            errors.append(f"docs/README.md must index {entry}")

    docs_root = REPO_ROOT / "docs"
    indexed = {
        line.split("`")[1] for line in index_text.splitlines() if line.count("`") >= 2
    }
    missing = []
    for path in docs_root.rglob("*.md"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel == "docs/README.md":
            continue
        if (
            "/api/" in rel
            or "/agent_graphs/" in rel
            or "/exec-plans/" in rel
            or "/generated/" in rel
        ):
            continue
        if rel not in indexed:
            missing.append(rel)
    if missing:
        errors.append(
            "docs/README.md is missing index entries for: "
            + ", ".join(sorted(missing)[:10])
        )


def ensure_frontend_test_truth(errors: list[str]) -> None:
    agents_text = read_text(REPO_ROOT / "AGENTS.md")
    package = json.loads(read_text(REPO_ROOT / "ai-pic-frontend" / "package.json"))
    test_files = list((REPO_ROOT / "ai-pic-frontend" / "tests").glob("**/*.*"))
    has_frontend_tests = bool(package.get("scripts", {}).get("test")) and bool(
        test_files
    )
    stale_claims = ["0 frontend tests", "Frontend Testing (TODO - Not Implemented)"]
    if has_frontend_tests and any(claim in agents_text for claim in stale_claims):
        errors.append("AGENTS.md still claims frontend tests are not implemented")


def ensure_harness_commands_documented(errors: list[str]) -> None:
    readme_text = read_text(REPO_ROOT / "README.md")
    docker_text = read_text(REPO_ROOT / "docker" / "README.md")
    required = [
        "scripts/harness/bootstrap_worktree.sh",
        "python scripts/harness/doctor.py",
        "python scripts/harness/browser_flow.py",
        "python scripts/harness/run_golden_path.py",
    ]
    for command in required:
        if command not in readme_text and command not in docker_text:
            errors.append(f"Harness command is undocumented: {command}")


def collect_doc_errors() -> list[str]:
    errors: list[str] = []
    ensure_mirrors(errors)
    ensure_required_docs(errors)
    ensure_docs_index(errors)
    ensure_frontend_test_truth(errors)
    ensure_harness_commands_documented(errors)
    return errors


def main() -> int:
    errors = collect_doc_errors()
    if errors:
        for error in errors:
            print(f"[check_repo_docs] {error}", file=sys.stderr)
        return 1
    print("[check_repo_docs] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
