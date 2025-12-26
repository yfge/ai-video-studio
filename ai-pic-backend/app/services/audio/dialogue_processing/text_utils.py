"""Text utilities for dialogue processing."""

from __future__ import annotations

import re

from app.core.logging import get_logger

logger = get_logger()


_ONLY_PUNCT_OR_SPACE = re.compile(
    r"^[\s\.\,\!\?\-\—\_\~\·\…\，\。\！\？\、\：\；\"\"\(\)\（\）]+$"
)

_LEADING_INLINE_ACTION_RE = re.compile(
    r"^\s*[\(\（\[\【](?P<action>[^)\）\]\】]{1,200})[\)\）\]\】]\s*"
)
_TRAILING_INLINE_ACTION_RE = re.compile(
    r"\s*[\(\（\[\【](?P<action>[^)\）\]\】]{1,200})[\)\）\]\】]\s*$"
)
_SPEECH_ATTR_RE = re.compile(
    r"^\s*(?P<attr>.{1,80}?)(?P<sep>[:：]|\s+|“|\"|‘|'|「|『)(?P<text>.+)$"
)
_TRIVIAL_SPEECH_ATTR_RE = re.compile(
    r"^(?:我|你|他|她|它|我们|你们|他们|她们|大家|众人|所有人)(?:们)?(?:说|说道|问|问道|答|答道)$"
)

_SPEECH_ATTR_SUFFIXES: tuple[str, ...] = tuple(
    sorted(
        {
            "低声说",
            "轻声说",
            "小声说",
            "大声说",
            "笑着说",
            "冷冷地说",
            "嘀咕道",
            "呢喃道",
            "咆哮道",
            "吼道",
            "喊道",
            "说道",
            "问道",
            "答道",
            "说",
            "问",
            "答",
        },
        key=len,
        reverse=True,
    )
)


def norm_name(name: str) -> str:
    """Normalize character name for comparison."""

    return "".join((name or "").strip().lower().split())


def looks_like_silence(text: str) -> bool:
    """Check if text represents silence or pause."""

    cleaned = (text or "").strip()
    if not cleaned:
        return True
    if _ONLY_PUNCT_OR_SPACE.match(cleaned):
        return True
    lowered = cleaned.lower()
    if lowered in {"...", "……", "…", "（沉默）", "(silence)", "[silence]"}:
        return True
    return False


def sanitize_dialogue_content(
    content: str,
    *,
    action: str | None = None,
) -> tuple[str, str | None]:
    """
    Remove inline stage directions from dialogue text.

    Examples:
    - "（叹气）你好" -> text="你好", action+="叹气"
    - "叹了一口气，站起来说：你好" -> text="你好", action+="叹了一口气，站起来说"
    """

    text = str(content or "").strip()
    actions: list[str] = []

    if isinstance(action, str) and action.strip():
        actions.append(action.strip())

    while True:
        m = _LEADING_INLINE_ACTION_RE.match(text)
        if not m:
            break
        inline = m.group("action").strip()
        if inline:
            actions.append(inline)
        text = text[m.end() :].strip()

    while True:
        m = _TRAILING_INLINE_ACTION_RE.search(text)
        if not m:
            break
        inline = m.group("action").strip()
        if inline:
            actions.append(inline)
        text = text[: m.start()].strip()

    m = _SPEECH_ATTR_RE.match(text)
    if m:
        attr = (m.group("attr") or "").strip()
        attr_no_space = "".join(attr.split())
        suffix_ok = any(attr_no_space.endswith(suf) for suf in _SPEECH_ATTR_SUFFIXES)
        if (
            suffix_ok
            and attr_no_space
            and not _TRIVIAL_SPEECH_ATTR_RE.match(attr_no_space)
        ):
            actions.append(attr)
            text = m.group("text").strip()

    combined_action = "；".join(actions) if actions else None
    return text, combined_action

