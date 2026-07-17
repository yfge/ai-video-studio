from __future__ import annotations

from typing import Any

from app.services.script.beat_contract_auto_repair_common import (
    beat_text,
    compact,
    has_any,
)

_PAYOFF_CUES = (
    "成功",
    "完成",
    "恢复",
    "通过",
    "保住",
    "交付",
    "发布",
    "揭露",
    "证明",
    "确认",
    "锁定",
    "反击",
    "兑现",
)


def ensure_contract_payoff(scenes: list[Any]) -> None:
    beats = [
        beat
        for scene in scenes
        if isinstance(scene, dict)
        for beat in scene.get("beats") or []
        if isinstance(beat, dict)
    ]
    if not beats or any(
        beat.get("beat_type") == "payoff" or beat.get("payoff_tag") for beat in beats
    ):
        return

    candidates = beats[:-1] or beats
    target = next(
        (
            beat
            for beat in reversed(candidates)
            if has_any(beat_text(beat), _PAYOFF_CUES)
        ),
        candidates[-1],
    )
    if target.get("beat_type") not in {"conflict", "reveal"}:
        target["beat_type"] = "payoff"
    if not target.get("payoff_tag"):
        visible = compact(str(target.get("visible_event") or ""))
        target["payoff_tag"] = visible[:24] or "阶段性结果已经兑现"
