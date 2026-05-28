from __future__ import annotations

from typing import Any

from app.services.script.beat_contract_specificity import (
    is_cliffhanger_beat,
    is_specific_text,
)

_RESOLVED_ENDING_PHRASES = (
    "任务完成",
    "全部熄灭",
    "全部恢复",
    "恢复正常",
    "危机解除",
    "真相大白",
    "圆满结束",
    "安全离开",
    "成功拿回",
    "拿回全部",
    "奖金全拿回",
    "全部奖金",
)

_UNRESOLVED_THREAT_CUES = (
    "谁",
    "还",
    "却",
    "突然",
    "倒计时",
    "删除",
    "消失",
    "黑影",
    "陌生",
    "未知",
    "新",
    "门开",
    "未解",
)


def cliffhanger_issues(beat: Any, scene_number: int) -> list[dict[str, Any]]:
    if not is_cliffhanger_beat(beat):
        return []

    issues: list[dict[str, Any]] = []
    if not _has_specific_cliffhanger(beat):
        issues.append(
            {
                "check_id": "cliffhanger_specificity",
                "message": "cliffhanger beat must leave a concrete unresolved threat",
                "scene_number": scene_number,
                "beat_order_index": beat.order_index,
                "evidence": {
                    "visible_event": beat.visible_event,
                    "cliffhanger_tag": beat.cliffhanger_tag,
                },
            }
        )
    if _looks_resolved_without_threat(beat):
        issues.append(
            {
                "check_id": "cliffhanger_unresolved_threat",
                "message": "cliffhanger beat must not fully resolve the story",
                "scene_number": scene_number,
                "beat_order_index": beat.order_index,
                "evidence": {
                    "visible_event": beat.visible_event,
                    "cliffhanger_tag": beat.cliffhanger_tag,
                },
            }
        )
    return issues


def _looks_resolved_without_threat(beat: Any) -> bool:
    text = _compact_text(
        " ".join(
            [
                beat.visible_event,
                beat.cliffhanger_tag or "",
                *[action.content for action in beat.action_lines],
                *[line.content for line in beat.dialogue_lines],
            ]
        )
    )
    has_resolution = any(phrase in text for phrase in _RESOLVED_ENDING_PHRASES)
    has_unresolved_cue = any(phrase in text for phrase in _UNRESOLVED_THREAT_CUES)
    return has_resolution and not has_unresolved_cue


def _has_specific_cliffhanger(beat: Any) -> bool:
    return is_specific_text(
        " ".join(
            [
                beat.visible_event,
                beat.cliffhanger_tag or "",
                *[action.content for action in beat.action_lines],
            ]
        )
    )


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
