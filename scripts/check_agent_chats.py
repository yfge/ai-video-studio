#!/usr/bin/env python3
"""Pre-commit hook to enforce agent_chats logging discipline."""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

try:
    import yaml  # type: ignore
except ImportError as exc:  # pragma: no cover - handled by pre-commit deps
    raise SystemExit("pyyaml is required for agent_chats validation") from exc

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_CHAT_ROOT = REPO_ROOT / "agent_chats"

# Regex for files like agent_chats/2025/10/23/2025-10-23T07-30-03Z-topic.md
FILENAME_PATTERN = re.compile(
    r"^agent_chats/\d{4}/\d{2}/\d{2}/\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z-[a-z0-9-]+\.md$"
)
ISO_DATETIME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)

REQUIRED_FRONTMATTER_KEYS = {
    "id",
    "date",
    "participants",
    "models",
    "tags",
    "summary",
    "related_paths",
}

REQUIRED_SECTIONS = [
    "## User Prompt",
    "## Goals",
    "## Changes",
    "## Validation",
    "## Next Steps",
    "## Linked Commits",
]

CODE_PREFIXES = (
    "ai-pic-backend/",
    "ai-pic-frontend/",
    "scripts/",
    "docker/",
    "infrastructure/",
)
CODE_FILES = {
    "AGENTS.md",
    "task.md",
}


def run_git(*args: str) -> Sequence[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(result.returncode)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


@dataclass
class AgentChatValidationError(Exception):
    message: str
    path: Path | None = None

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.path is not None:
            return f"{self.message}: {self.path}"
        return self.message


def ensure_agent_directory_present() -> None:
    if not AGENT_CHAT_ROOT.exists():
        raise AgentChatValidationError(
            "agent_chats directory is missing in repository root", AGENT_CHAT_ROOT
        )


def ensure_no_unstaged_agent_changes() -> None:
    unstaged = run_git("diff", "--name-only", "agent_chats")
    unstaged = [path for path in unstaged if not path.endswith(".gitkeep")]
    if unstaged:
        pretty = "\n  - ".join(["" , *unstaged])
        raise AgentChatValidationError(
            f"Unstaged changes detected under agent_chats:{pretty}"
        )


def get_staged_files() -> Sequence[str]:
    staged = run_git("diff", "--cached", "--name-only")
    return staged


def separate_files(paths: Iterable[str]) -> tuple[list[str], list[str]]:
    chat_files: list[str] = []
    code_files: list[str] = []
    for path in paths:
        if path.startswith("agent_chats/"):
            if not path.endswith(".md"):
                raise AgentChatValidationError(
                    "Only Markdown files are allowed under agent_chats", Path(path)
                )
            chat_files.append(path)
            continue
        if path.startswith(CODE_PREFIXES) or path in CODE_FILES:
            code_files.append(path)
    return chat_files, code_files


def assert_chat_files_present_if_needed(chat_files: list[str], code_files: list[str]) -> None:
    if code_files and not chat_files:
        pretty = "\n  - ".join(["" , *code_files])
        raise AgentChatValidationError(
            "Code changes require a matching agent_chats log entry."
            f" Staged code files:{pretty}"
        )


def parse_frontmatter(text: str, path: Path) -> tuple[dict, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise AgentChatValidationError("Missing YAML frontmatter", path)
    try:
        end_index = lines[1:].index("---") + 1
    except ValueError as exc:
        raise AgentChatValidationError("Frontmatter must end with '---'", path) from exc
    fm_lines = lines[1:end_index]
    fm_text = "\n".join(fm_lines)
    try:
        data = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        raise AgentChatValidationError("Invalid YAML frontmatter", path) from exc
    body = "\n".join(lines[end_index + 1 :]).strip()
    return data, body


def validate_frontmatter(data: dict, path: Path) -> None:
    missing = REQUIRED_FRONTMATTER_KEYS - set(data)
    if missing:
        raise AgentChatValidationError(
            f"Frontmatter missing keys: {', '.join(sorted(missing))}", path
        )

    identifier = data.get("id")
    if not isinstance(identifier, str) or not identifier:
        raise AgentChatValidationError("frontmatter.id must be a non-empty string", path)

    date_value = data.get("date")
    if not isinstance(date_value, str) or not ISO_DATETIME_RE.match(date_value):
        raise AgentChatValidationError(
            "frontmatter.date must be UTC ISO timestamp (e.g. 2025-01-01T08:30:00Z)",
            path,
        )

    for list_key in ("participants", "models", "tags", "related_paths"):
        value = data.get(list_key)
        if not isinstance(value, list) or not value:
            raise AgentChatValidationError(
                f"frontmatter.{list_key} must be a non-empty list", path
            )
        if not all(isinstance(item, str) and item for item in value):
            raise AgentChatValidationError(
                f"frontmatter.{list_key} must contain non-empty strings", path
            )

    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise AgentChatValidationError("frontmatter.summary must be a string", path)


def validate_sections(body: str, path: Path) -> None:
    for section in REQUIRED_SECTIONS:
        if section not in body:
            raise AgentChatValidationError(
                f"Missing required section heading '{section}'", path
            )


def validate_filename(path: Path) -> None:
    if not FILENAME_PATTERN.match(path.as_posix()):
        raise AgentChatValidationError(
            "File name must follow agent_chats/YYYY/MM/DD/YYYY-MM-DDTHH-MM-SSZ-topic.md",
            path,
        )


def validate_agent_file(rel_path: str) -> None:
    path = REPO_ROOT / rel_path
    validate_filename(path.relative_to(REPO_ROOT))
    text = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text, path)
    validate_frontmatter(frontmatter, path)
    validate_sections(body, path)


def main() -> int:
    try:
        ensure_agent_directory_present()
        ensure_no_unstaged_agent_changes()
        staged = get_staged_files()
        chat_files, code_files = separate_files(staged)
        assert_chat_files_present_if_needed(chat_files, code_files)
        for rel_path in chat_files:
            validate_agent_file(rel_path)
    except AgentChatValidationError as exc:
        print(f"[agent_chats] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
