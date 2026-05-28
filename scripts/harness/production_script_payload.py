"""Shared script payload extraction for provider-chain quality checks."""

from __future__ import annotations

import json
import re
from typing import Any


def extract_script_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw = ((payload.get("key_artifacts") or {}).get("script") or {}).get("raw_content")
    if not isinstance(raw, str) or not raw.strip():
        return {}
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fence:
        text = fence.group(1)
    elif not text.startswith("{"):
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            text = match.group(0)
    data = json.loads(text)
    return data if isinstance(data, dict) else {}
