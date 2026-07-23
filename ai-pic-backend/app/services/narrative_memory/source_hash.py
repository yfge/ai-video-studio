"""Stable hashes for narrative source artifacts."""

import hashlib
import json
from typing import Any


def artifact_hash(value: Any) -> str:
    raw = (
        value
        if isinstance(value, str)
        else json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def novel_chapter_source_hash(chapter) -> str:
    return artifact_hash(
        {
            "position": chapter.position,
            "content_hash": chapter.content_hash,
            "title": chapter.title,
        }
    )
