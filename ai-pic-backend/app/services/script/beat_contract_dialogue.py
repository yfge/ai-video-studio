from __future__ import annotations

from typing import Any

_FILLER_DIALOGUE = {
    "嗯",
    "嗯嗯",
    "啊",
    "哦",
    "好",
    "好的",
    "好吧",
    "行",
    "可以",
    "知道了",
    "我知道了",
    "明白了",
    "是的",
    "不是",
    "没事",
    "怎么办",
    "怎么会这样",
}


def dialogue_issues(scene: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    dialogue_texts: list[str] = []
    for beat in scene.beats:
        for line in beat.dialogue_lines:
            content = _compact_text(line.content)
            dialogue_texts.append(content)
            if content in _FILLER_DIALOGUE:
                issues.append(
                    {
                        "check_id": "dialogue_substance",
                        "message": "dialogue must carry story information",
                        "scene_number": scene.scene_number,
                        "beat_order_index": beat.order_index,
                        "evidence": {"content": line.content},
                    }
                )

    if len(dialogue_texts) > 1 and len(set(dialogue_texts)) < len(dialogue_texts):
        issues.append(
            {
                "check_id": "dialogue_progression_repetition",
                "message": "scene dialogue must progress across beats",
                "scene_number": scene.scene_number,
                "beat_order_index": None,
                "evidence": {"dialogue_count": len(dialogue_texts)},
            }
        )
    return issues


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
