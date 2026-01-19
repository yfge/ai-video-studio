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

    # Prefer the first balanced JSON object/array in the text, rather than
    # slicing to the *last* closing brace which can be polluted by extra
    # reminders like `只输出严格JSON：{"frames":[...]}` appended by models.
    start = None
    for idx, ch in enumerate(stripped):
        if ch in "{[":
            start = idx
            break

    if start is None:
        return stripped

    stack: list[str] = []
    in_string = False
    escape = False
    for idx in range(start, len(stripped)):
        ch = stripped[idx]

        if in_string:
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue

        if ch in "{[":
            stack.append(ch)
            continue

        if ch in "}]":
            if not stack:
                continue
            open_ch = stack[-1]
            if (open_ch == "{" and ch == "}") or (open_ch == "[" and ch == "]"):
                stack.pop()
                if not stack:
                    return stripped[start : idx + 1]
            continue

    # Fallback: return from first brace/bracket onward (best effort).
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
