"""Repair AI-generated prose blocks for dialogue audio.

The script generator sometimes produces long narration paragraphs under the
speaker "旁白" that embed multiple dialogue lines via quotes. If we feed that
directly into TTS, the entire paragraph is spoken with the narrator voice,
which sounds like "旁白描述" instead of character dialogue.

This module extracts quoted utterances and infers speakers from nearby name
mentions (using the Story character registry alias map).
"""

from __future__ import annotations

import re
from typing import Any, Sequence

from app.core.validators.character_registry import (
    normalize_character_name_token,
    normalize_to_registered_or_generic,
)

# Common quote pairs. Keep this strict to avoid capturing mismatched pairs.
_QUOTED_SPAN_RE = re.compile(
    r"“(?P<c1>[^”]{1,2000})”"
    r"|「(?P<c2>[^」]{1,2000})」"
    r"|『(?P<c3>[^』]{1,2000})』"
    r"|‘(?P<c4>[^’]{1,2000})’"
    r'|"(?P<c5>[^"]{1,2000})"'
    r"|'(?P<c6>[^']{1,2000})'"
)

# Hints that a quoted span is UI text / label rather than spoken dialogue.
_NON_SPOKEN_HINTS: tuple[str, ...] = (
    "写着",
    "写上",
    "显示",
    "提示",
    "弹出",
    "出现",
    "字幕",
    "标注",
    "界面",
    "屏幕",
    "窗口",
)

_SPEECH_PUNCT = set("。！？!?…")


def _prev_non_space_char(text: str, idx: int) -> str | None:
    j = idx - 1
    while j >= 0 and text[j].isspace():
        j -= 1
    return text[j] if j >= 0 else None


def _quote_text(match: re.Match[str]) -> str:
    for key in ("c1", "c2", "c3", "c4", "c5", "c6"):
        value = match.group(key)
        if value is not None:
            return value
    return ""


def _looks_like_dialogue_quote(text: str) -> bool:
    value = (text or "").strip()
    if not value:
        return False
    if any(ch in _SPEECH_PUNCT for ch in value):
        return True
    if "，" in value or "," in value:
        # UI strings rarely contain commas; keep a modest length guard.
        return len(value) >= 8
    return len(value) >= 12


def _has_non_spoken_hint(prefix: str) -> bool:
    tail = (prefix or "")[-20:]
    return any(h in tail for h in _NON_SPOKEN_HINTS)


def _infer_speaker_from_prefix(
    prefix: str,
    *,
    alias_to_canonical: dict[str, str],
) -> str | None:
    if not prefix:
        return None
    window = prefix[-80:]

    # Prefer the closest alias match.
    best_canonical = None
    best_idx = -1
    best_len = -1
    for alias, canonical in alias_to_canonical.items():
        if not alias:
            continue
        idx = window.rfind(alias)
        if idx < 0:
            continue
        if idx > best_idx or (idx == best_idx and len(alias) > best_len):
            best_idx = idx
            best_len = len(alias)
            best_canonical = canonical
    if best_canonical:
        return best_canonical

    # Fallback: try parsing the last token-ish segment.
    parts = re.split(r"[:：，,。.!！?？\s]+", window)
    for token in reversed(parts):
        token = normalize_character_name_token(token)
        if not token:
            continue
        normalized = normalize_to_registered_or_generic(
            token, alias_to_canonical=alias_to_canonical
        )
        if normalized:
            return normalized
    return None


def split_prose_dialogue_block(
    text: str,
    *,
    alias_to_canonical: dict[str, str],
    default_speaker: str = "旁白",
) -> list[dict[str, Any]]:
    """Split a prose paragraph into dialogue lines.

    Returns list of {"character": str, "content": str}.
    """
    if not isinstance(text, str):
        return []
    if not alias_to_canonical:
        return []

    results: list[dict[str, Any]] = []
    last_speaker: str | None = None

    for m in _QUOTED_SPAN_RE.finditer(text):
        quote = _quote_text(m).strip()
        if not quote:
            continue

        start = m.start()
        pre = _prev_non_space_char(text, start)
        strong = pre in {":", "："}
        prefix = text[:start]

        if strong:
            speaker = _infer_speaker_from_prefix(
                prefix, alias_to_canonical=alias_to_canonical
            )
        else:
            # Continuation quote: only if we already have a speaker and it doesn't
            # look like UI/screen text.
            if last_speaker is None:
                continue
            if _has_non_spoken_hint(prefix):
                continue
            if not _looks_like_dialogue_quote(quote):
                continue
            speaker = last_speaker

        normalized = normalize_to_registered_or_generic(
            speaker or default_speaker,
            alias_to_canonical=alias_to_canonical,
        )
        if not normalized:
            normalized = default_speaker

        results.append({"character": normalized, "content": quote})
        last_speaker = normalized

    return results


def sanitize_stage_directions_for_audio(
    stage_directions: Sequence[dict[str, Any]],
    *,
    alias_to_canonical: dict[str, str] | None = None,
    max_len: int = 300,
) -> list[dict[str, Any]]:
    """Strip embedded quoted dialogue from stage directions for cleaner beats."""
    if not stage_directions:
        return []

    cleaned: list[dict[str, Any]] = []
    for sd in stage_directions:
        if not isinstance(sd, dict):
            continue
        content = str(sd.get("content") or "").strip()
        if not content:
            continue
        # We remove all quoted spans regardless of alias map; stage directions
        # should primarily describe actions/visuals.
        content2 = _QUOTED_SPAN_RE.sub("", content)
        content2 = re.sub(r"\s+", " ", content2).strip()
        if len(content2) > max_len:
            content2 = content2[: max_len - 3].rstrip() + "..."
        out = dict(sd)
        out["content"] = content2
        cleaned.append(out)
    return cleaned
