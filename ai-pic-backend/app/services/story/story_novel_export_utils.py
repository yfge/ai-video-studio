from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

ZH_SUMMARY_MARKER = "【本章小结】"
ZH_CLIFFHANGER_MARKER = "【本章卡点】"

NOVEL_RESULT_PREFIX = "novel_file:"


@dataclass(frozen=True)
class StoryNovelExportResult:
    relative_path: str
    filename: str
    total_words: int
    chapter_count: int
    content_text: str


def parse_export_result_path(result_file_path: str) -> Optional[str]:
    if not result_file_path:
        return None
    if not result_file_path.startswith(NOVEL_RESULT_PREFIX):
        return None
    value = result_file_path[len(NOVEL_RESULT_PREFIX) :].strip()
    return value or None


def build_export_result_path(relative_path: str) -> str:
    return f"{NOVEL_RESULT_PREFIX}{relative_path}"


def count_words(text: str) -> int:
    return len(re.sub(r"\s+", "", text or ""))


def clip_text(value: Optional[str], limit: int) -> Optional[str]:
    if not value:
        return value
    value = value.strip()
    if len(value) <= limit:
        return value
    head = value[: int(limit * 0.7)]
    tail = value[-int(limit * 0.3) :]
    return f"{head}\n...\n{tail}"


def estimate_chapter_count(target_words: int, chapter_count: Optional[int]) -> int:
    if chapter_count:
        return max(3, min(24, int(chapter_count)))
    rough = int(round(target_words / 1800))
    return max(3, min(24, rough))


def safe_join_under(base_dir: Path, relative_path: str) -> Path:
    base = base_dir.resolve()
    candidate = (base / relative_path).resolve()
    if base == candidate or base in candidate.parents:
        return candidate
    raise HTTPException(status_code=400, detail="Invalid export file path")
