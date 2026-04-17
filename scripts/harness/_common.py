#!/usr/bin/env python3
"""Shared helpers for harness scripts."""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_ROOT = REPO_ROOT / "artifacts" / "runs"
LOG_FILE = REPO_ROOT / "logs" / "ai-video-studio.jsonl"


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_run_id(prefix: str = "harness") -> str:
    stamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{stamp}"


def slugify(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-") or "workspace"


def ensure_run_dir(run_id: str) -> Path:
    run_dir = ARTIFACTS_ROOT / run_id
    (run_dir / "screenshots").mkdir(parents=True, exist_ok=True)
    return run_dir


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def resolve_run_dir(run_id: str | None) -> Path:
    if run_id:
        return ensure_run_dir(run_id)
    candidates = sorted(ARTIFACTS_ROOT.glob("*/manifest.json"))
    if not candidates:
        raise FileNotFoundError("No harness runs found under artifacts/runs")
    return candidates[-1].parent


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd or REPO_ROOT,
        env=env or os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(
            f"Command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    return completed


def update_summary(run_dir: Path, **fields: Any) -> dict[str, Any]:
    summary_path = run_dir / "summary.json"
    summary = read_json(summary_path, default={}) or {}
    summary.update(fields)
    write_json(summary_path, summary)
    return summary


def find_jsonl_log() -> Path:
    return LOG_FILE
