"""Opening-hook substance checks for provider-chain script scoring."""

from __future__ import annotations

from typing import Any

_HOOK_MARKERS = (
    "异常",
    "警报",
    "报警",
    "警告",
    "倒计时",
    "清零",
    "归零",
    "删除",
    "丢失",
    "失去",
    "拒绝",
    "锁定",
    "冻结",
    "错误",
    "失败",
    "危机",
    "威胁",
    "黑影",
    "证据",
    "编号",
    "真相",
    "反转",
    "最后",
    "必须",
    "谁",
    "不能",
    "阻止",
    "抢",
    "改",
    "改了",
)


def opening_hook_failed_checks(scenes: list[dict[str, Any]]) -> list[str]:
    if not scenes:
        return []

    beats = scenes[0].get("beats") if isinstance(scenes[0].get("beats"), list) else []
    first_beat = beats[0] if beats and isinstance(beats[0], dict) else None
    if not first_beat or first_beat.get("beat_type") != "hook":
        return []

    screen_text = _opening_screen_text(first_beat)
    if any(marker in screen_text for marker in _HOOK_MARKERS):
        return []
    return ["opening_hook_substance"]


def _opening_screen_text(beat: dict[str, Any]) -> str:
    parts = [str(beat.get("visible_event") or "")]
    actions = beat.get("action") or beat.get("action_lines") or []
    if isinstance(actions, list):
        for item in actions:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("content") or ""))
    dialogue = beat.get("dialogue") or beat.get("dialogue_lines") or []
    if isinstance(dialogue, list):
        for line in dialogue:
            if isinstance(line, dict):
                parts.append(str(line.get("line") or line.get("content") or ""))
    return _compact_text("".join(parts))


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
