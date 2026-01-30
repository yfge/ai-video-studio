"""Script dialogue quality validators.

These helpers are used by script-generation agents to detect common LLM failure
modes (assistant meta-notes, repetitive filler lines, etc.) and trigger REACT
regeneration before persisting results.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Sequence

_PUNCTUATION = set(
    " \t\r\n" "，。！？!?….,、;；:：" "\"“”‘’'`" "()（）[]【】{}<>《》" "—-~～"
)


def _normalize_text(text: str) -> str:
    return "".join(ch for ch in text.strip().lower() if ch not in _PUNCTUATION)


def looks_like_writer_note(text: str) -> bool:
    """Heuristic: detect assistant/writer meta-notes accidentally output as dialogue."""
    s = (text or "").strip()
    if not s:
        return False

    if s.startswith(("提示：", "注：", "备注：", "建议：")):
        return True

    locators = ("这里", "此处", "这一段", "这段", "这一幕", "本段", "本场", "此时")
    verbs = (
        "可以",
        "建议",
        "应该",
        "需要",
        "用来",
        "用于",
        "突出",
        "加强",
        "体现",
        "表现",
        "铺垫",
    )
    targets = ("冲突", "情绪", "张力", "节奏", "氛围", "转折", "反转", "矛盾")

    has_locator = any(k in s for k in locators)
    has_meta_signal = any(k in s for k in verbs) or any(k in s for k in targets)
    if has_locator and has_meta_signal:
        return True

    return False


def find_reused_short_dialogues(
    dialogues: Sequence[dict],
    *,
    max_chars: int = 40,
    min_repeats: int = 2,
) -> set[str]:
    """Return normalized dialogue contents that are suspiciously repeated."""
    normalized: list[str] = []
    for d in dialogues:
        if not isinstance(d, dict):
            continue
        content = d.get("content")
        if not isinstance(content, str):
            continue
        raw = content.strip()
        if not raw or len(raw) > max_chars:
            continue
        normalized.append(_normalize_text(raw))

    counts = Counter([n for n in normalized if n])
    return {k for k, v in counts.items() if v >= min_repeats}


@dataclass(frozen=True, slots=True)
class SceneDialogueIssue:
    code: str
    message: str


def validate_scene_dialogues(
    scene_dialogues: Sequence[dict],
    *,
    min_lines: int = 2,
    repeated_short_norms: set[str] | None = None,
) -> list[SceneDialogueIssue]:
    """Validate a single scene's dialogues and return issues (empty means ok)."""
    issues: list[SceneDialogueIssue] = []

    if len([d for d in scene_dialogues if isinstance(d, dict)]) < min_lines:
        issues.append(
            SceneDialogueIssue(
                code="too_few_lines",
                message=f"对白条数不足（至少 {min_lines} 句）",
            )
        )

    for d in scene_dialogues:
        if not isinstance(d, dict):
            continue
        content = d.get("content")
        if not isinstance(content, str):
            continue
        if looks_like_writer_note(content):
            issues.append(
                SceneDialogueIssue(
                    code="writer_note",
                    message="检测到疑似编剧/助手元语言（如“这里可以…”），需改写为戏内台词",
                )
            )
            break

    if repeated_short_norms:
        for d in scene_dialogues:
            if not isinstance(d, dict):
                continue
            content = d.get("content")
            if not isinstance(content, str):
                continue
            if _normalize_text(content) in repeated_short_norms:
                issues.append(
                    SceneDialogueIssue(
                        code="reused_filler",
                        message="检测到跨场景重复的模板台词（请替换为与本场景相关的具体台词）",
                    )
                )
                break

    return issues
