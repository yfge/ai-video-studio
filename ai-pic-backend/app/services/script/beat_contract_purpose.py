from __future__ import annotations

from typing import Any

_VAGUE_PURPOSE_PHRASES = (
    "推进剧情",
    "推动剧情",
    "故事继续",
    "铺垫剧情",
    "制造悬念",
    "留下悬念",
    "制造冲突",
    "推动冲突",
    "升级冲突",
    "出现转折",
    "发生反转",
    "完成转折",
    "承上启下",
    "情绪变化",
    "关系变化",
)


def purpose_issues(scene: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for beat in scene.beats:
        purpose = _compact_text(beat.dramatic_purpose)
        if _visible_len(purpose) < 4 or any(
            phrase in purpose for phrase in _VAGUE_PURPOSE_PHRASES
        ):
            issues.append(
                {
                    "check_id": "beat_dramatic_purpose_specificity",
                    "message": "beat dramatic purpose must name a concrete story turn",
                    "scene_number": scene.scene_number,
                    "beat_order_index": beat.order_index,
                    "evidence": {"dramatic_purpose": beat.dramatic_purpose},
                }
            )
    return issues


def _visible_len(text: str) -> int:
    return len("".join(ch for ch in text if not ch.isspace()))


def _compact_text(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())
