from __future__ import annotations

from typing import Any

_HOOK_MARKERS = (
    "异常",
    "警报",
    "报警",
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


def opening_hook_issues(scene: Any) -> list[dict[str, Any]]:
    if scene.scene_number != 1 or not scene.beats:
        return []

    beat = scene.beats[0]
    if beat.beat_type != "hook":
        return []

    screen_text = _opening_screen_text(beat)
    if any(marker in screen_text for marker in _HOOK_MARKERS):
        return []

    return [
        {
            "check_id": "opening_hook_substance",
            "message": "opening hook must show an immediate threat or reversal",
            "scene_number": scene.scene_number,
            "beat_order_index": beat.order_index,
            "evidence": {"screen_text": screen_text},
        }
    ]


def _opening_screen_text(beat: Any) -> str:
    parts = [
        beat.visible_event,
        *[action.content for action in beat.action_lines],
        *[line.content for line in beat.dialogue_lines],
    ]
    return _compact_text("".join(parts))


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
