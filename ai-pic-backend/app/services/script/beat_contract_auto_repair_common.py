from __future__ import annotations

from typing import Any

LOW_VALUE_CHARACTERS = {"录音", "短信", "旁白"}


def has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def compact(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())


def visible_len(text: str) -> int:
    return len(compact(text))


def to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def scene_role(index: int, count: int) -> str:
    return "hook" if index == 1 else "cliffhanger" if index == count else "escalation"


def preferred_character(beats: list[dict[str, Any]]) -> str | None:
    counts: dict[str, int] = {}
    for beat in beats:
        for line in beat.get("dialogue_lines") or []:
            character = (
                str(line.get("character") or "").strip()
                if isinstance(line, dict)
                else ""
            )
            if character and character not in LOW_VALUE_CHARACTERS:
                counts[character] = counts.get(character, 0) + 1
    ap_name = next((name for name in counts if "AP" in name or "回归" in name), None)
    return ap_name or (max(counts, key=counts.get) if counts else None)


def progression_event(protagonist: str, order: int) -> str:
    return (
        f"{protagonist}将原始文件放到投影左侧，屏幕标红被改数字。",
        f"{protagonist}指向会议纪要时间戳，助理调出修改日志。",
        "客户在投影前停住动作，篡改者低头按灭手机屏幕。",
        "手机录音波形跳动，篡改者低声承认从音箱传出。",
    )[(order - 1) % 4]


def progression_action(protagonist: str, order: int) -> str:
    return (
        f"{protagonist}把两份数据页并排推到客户面前。",
        "助理把修改日志窗口拖到投影中央。",
        "客户拿起笔在问题数字旁画圈。",
        "篡改者后退半步，手机通知栏露出删除提醒。",
    )[(order - 1) % 4]


def progression_dialogue(order: int) -> str:
    return ("看时间戳。", "原始页在这。", "日志能对上。", "别删文件。")[
        (order - 1) % 4
    ]


def beat_screen_text(beat: dict[str, Any]) -> str:
    return "".join(
        str(action.get("content") or "")
        for action in beat.get("action_lines", [])
        if isinstance(action, dict)
    )


def beat_text(beat: dict[str, Any]) -> str:
    return compact(str(beat.get("visible_event") or "") + beat_screen_text(beat))


def scene_screen_text(beats: list[dict[str, Any]]) -> str:
    return compact(
        "".join(str(beat.get("visible_event") or "") + beat_screen_text(beat) for beat in beats)
    )
