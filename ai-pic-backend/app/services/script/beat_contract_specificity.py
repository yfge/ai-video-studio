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
    "意识到",
    "明白",
    "想到",
    "感到",
    "感觉到",
    "内心",
    "心里",
    "情绪",
    "崩溃",
    "命运",
    "关系变化",
    "心理变化",
    "产生变化",
)

_GENERIC_CHARACTER_NAMES = {
    "角色",
    "角色A",
    "角色B",
    "人物",
    "某人",
    "主角",
    "男主",
    "女主",
    "男主角",
    "女主角",
    "旁白",
    "叙述者",
    "narrator",
    "speaker",
}


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


def character_specificity_issues(scene: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    character_beats: dict[str, set[int]] = {}
    has_dialogue = False

    for beat in scene.beats:
        for line in beat.dialogue_lines:
            has_dialogue = True
            character = _compact_text(line.character)
            if not is_specific_character_name(character):
                issues.append(
                    {
                        "check_id": "dialogue_character_specificity",
                        "message": "dialogue character must be a stable named role",
                        "scene_number": scene.scene_number,
                        "beat_order_index": beat.order_index,
                        "evidence": {"character": line.character},
                    }
                )
                continue
            character_beats.setdefault(character, set()).add(beat.order_index)

    has_recurring_character = any(
        len(beat_indexes) >= 2 for beat_indexes in character_beats.values()
    )
    if has_dialogue and len(scene.beats) > 1 and not has_recurring_character:
        issues.append(
            {
                "check_id": "scene_protagonist_presence",
                "message": "scene must keep one named character active across beats",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {"characters": sorted(character_beats)},
            }
        )

    return issues


def protagonist_screen_presence_issues(scene: Any) -> list[dict[str, Any]]:
    recurring_characters = _recurring_dialogue_characters(scene)
    if not recurring_characters:
        return []

    screen_text = _scene_screen_text(scene)
    if any(character in screen_text for character in recurring_characters):
        return []

    return [
        {
            "check_id": "scene_protagonist_screen_presence",
            "message": "scene must show the recurring named protagonist in screen action",
            "scene_number": scene.scene_number,
            "beat_order_index": None,
            "evidence": {"characters": recurring_characters},
        }
    ]


def is_specific_character_name(character: str | None) -> bool:
    normalized = _compact_text(character or "")
    if _visible_len(normalized) < 2:
        return False
    return normalized not in _GENERIC_CHARACTER_NAMES


def _visible_len(text: str) -> int:
    return len("".join(ch for ch in text if not ch.isspace()))


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())


def _recurring_dialogue_characters(scene: Any) -> list[str]:
    character_beats: dict[str, set[int]] = {}
    for beat in scene.beats:
        for line in beat.dialogue_lines:
            character = _compact_text(line.character)
            if is_specific_character_name(character):
                character_beats.setdefault(character, set()).add(beat.order_index)
    return sorted(
        character
        for character, beat_indexes in character_beats.items()
        if len(beat_indexes) >= 2
    )


def _scene_screen_text(scene: Any) -> str:
    parts: list[str] = []
    for beat in scene.beats:
        parts.append(beat.visible_event)
        parts.extend(action.content for action in beat.action_lines)
    return _compact_text("".join(parts))
