import ast
import json
import re
from typing import Any, Dict

_TRAILING_COMMA_RE = re.compile(r",\s*([}\]])")


def _strip_code_fence(text: str) -> str:
    fence_match = re.search(r"```[a-zA-Z]*\s*(.*?)\s*```", text, flags=re.S)
    if not fence_match:
        return text
    return fence_match.group(1).strip()


def _extract_json_like_substring(text: str) -> str:
    stripped = (text or "").strip()
    if not stripped:
        return ""

    left = stripped.lstrip()
    if left.startswith("{") or left.startswith("["):
        return left

    brace_start = stripped.find("{")
    bracket_start = stripped.find("[")
    start_candidates = [pos for pos in (brace_start, bracket_start) if pos != -1]
    if not start_candidates:
        return stripped

    start = min(start_candidates)
    open_char = stripped[start]
    close_char = "}" if open_char == "{" else "]"
    end = stripped.rfind(close_char)
    if end != -1 and end > start:
        return stripped[start : end + 1]
    return stripped[start:]


def _remove_trailing_commas(text: str) -> str:
    value = text
    while True:
        updated = _TRAILING_COMMA_RE.sub(r"\1", value)
        if updated == value:
            return updated
        value = updated


def _try_parse_json_dict(text: str) -> Dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _try_parse_yaml_dict(text: str) -> Dict[str, Any] | None:
    try:
        import yaml
    except Exception:
        return None

    try:
        parsed = yaml.safe_load(text)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _try_parse_literal_dict(text: str) -> Dict[str, Any] | None:
    try:
        parsed = ast.literal_eval(text)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def extract_json_block(payload: str | None) -> Dict[str, Any] | None:
    """
    尝试从包含 Markdown 代码块或额外文字的字符串中提取 JSON 对象。
    优先处理 ```json ... ``` 包裹的内容，再回退到首尾花括号截取。
    """
    if not payload:
        return None

    text = _extract_json_like_substring(_strip_code_fence(payload.strip()))
    if not text:
        return None

    for candidate in (text, _remove_trailing_commas(text)):
        parsed = _try_parse_json_dict(candidate)
        if parsed is not None:
            return parsed

    for candidate in (text, _remove_trailing_commas(text)):
        parsed = _try_parse_yaml_dict(candidate)
        if parsed is not None:
            return parsed

        parsed = _try_parse_literal_dict(candidate)
        if parsed is not None:
            return parsed

    return None
