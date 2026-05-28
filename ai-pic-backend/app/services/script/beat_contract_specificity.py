from __future__ import annotations

from typing import Any

_VAGUE_PHRASES = (
    "剧情继续",
    "推进剧情",
    "故事继续",
    "角色开始行动",
    "开始行动",
    "重大危机",
    "巨大危机",
    "神秘力量",
    "获得胜利",
    "取得胜利",
    "赢得胜利",
    "留下悬念",
    "留下巨大悬念",
    "巨大悬念",
    "制造悬念",
    "关键线索",
    "出现转折",
    "发生反转",
    "推动冲突",
    "升级冲突",
    "必须推进剧情信息",
    "本场必须推进",
    "阻碍尚未结构化",
)


def has_specific_scene_conflict(scene: Any) -> bool:
    return is_specific_text(scene.conflict.stakes) and is_specific_text(
        scene.conflict.opposition
    )


def has_specific_payoff(beat: Any) -> bool:
    return is_specific_text(
        " ".join(
            [
                beat.visible_event,
                beat.payoff_tag or "",
                *[action.content for action in beat.action_lines],
            ]
        )
    )


def has_specific_cliffhanger(beat: Any) -> bool:
    return is_specific_text(
        " ".join(
            [
                beat.visible_event,
                beat.cliffhanger_tag or "",
                *[action.content for action in beat.action_lines],
            ]
        )
    )


def is_payoff_beat(beat: Any) -> bool:
    return beat.beat_type == "payoff" or bool(beat.payoff_tag)


def is_cliffhanger_beat(beat: Any) -> bool:
    return beat.beat_type == "cliffhanger" or bool(beat.cliffhanger_tag)


def is_specific_text(text: str | None) -> bool:
    normalized = _compact_text(text or "")
    if _visible_len(normalized) < 4:
        return False
    return not any(phrase in normalized for phrase in _VAGUE_PHRASES)


def _visible_len(text: str) -> int:
    return len("".join(ch for ch in text if not ch.isspace()))


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
