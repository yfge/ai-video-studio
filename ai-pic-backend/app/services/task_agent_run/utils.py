from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple


def safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def loads_task_parameters(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def deep_merge_dict(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = deep_merge_dict(existing, value)
        else:
            merged[key] = value
    return merged


def parse_result_id(result_file_path: Optional[str], *, prefix: str) -> Optional[str]:
    if not result_file_path:
        return None
    if not result_file_path.startswith(prefix + ":"):
        return None
    return result_file_path.split(":", 1)[1]


def maybe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def split_provider_model(model: Any) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(model, str):
        return None, None
    raw = model.strip()
    if not raw:
        return None, None
    if ":" in raw:
        provider, model_id = raw.split(":", 1)
        provider = provider.strip() or None
        model_id = model_id.strip() or None
        return provider, model_id
    return None, raw


def load_task_param_str(task, key: str) -> Optional[str]:
    params = loads_task_parameters(getattr(task, "parameters", None))
    value = params.get(key)
    return value if isinstance(value, str) and value.strip() else None

