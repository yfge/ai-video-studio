"""Render job hashing helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def render_preset_hash(preset: dict[str, Any]) -> str:
    normalized = json.dumps(
        preset, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
