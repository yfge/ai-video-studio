from __future__ import annotations

import re
from typing import Any

from app.services.script.beat_contract_auto_repair_common import (
    beat_text,
    compact,
    has_any,
    preferred_character,
    to_float,
    visible_len,
)
from app.services.script.beat_contract_cliffhanger import (
    is_concrete_unresolved_cliffhanger_text,
)
from app.services.script.beat_contract_hook import (
    opening_hook_screen_text_has_substance,
)

_VAGUE_VISUAL = ("气氛", "氛围", "紧张感", "压迫感")
_VAGUE = (
    "意识到",
    "明白",
    "内心",
    "崩溃",
    "发现关键线索",
    "关键线索",
    "出现转折",
    "发生反转",
    "制造冲突",
    "制造悬念",
    "留下悬念",
    "推动冲突",
    "升级冲突",
    "推进剧情",
)


def repair_beats(scene: dict[str, Any], beats: list[dict[str, Any]]) -> None:
    protagonist = preferred_character(beats)
    for beat in beats:
        visible = str(beat.get("visible_event") or "")
        if has_any(visible, _VAGUE_VISUAL):
            beat["visible_event"] = _repair_vague_visual(visible, protagonist)
        if (
            protagonist
            and (beat.get("beat_type") == "payoff" or beat.get("payoff_tag"))
            and has_any(visible, ("信任", "崩溃", "承认"))
        ):
            payoff_object = _concrete_object(
                visible
                + "".join(
                    str(item.get("content") or "")
                    for item in beat.get("action_lines") or []
                    if isinstance(item, dict)
                )
            )
            beat["visible_event"] = (
                f"{protagonist}把{payoff_object}结果页推到镜头前，状态栏变为“已确认”。"
            )
            beat["action_lines"] = [
                {
                    "content": f"{protagonist}指向{payoff_object}结果页上的确认标记。",
                    "timing": "mid",
                    "type": "action",
                }
            ]
            beat["payoff_tag"] = f"{payoff_object}结果已确认"
        purpose = str(beat.get("dramatic_purpose") or "")
        if not purpose or has_any(purpose, _VAGUE):
            beat["dramatic_purpose"] = (
                f"{beat['visible_event']}让当前人物选择和局面进入下一步。"
            )
        for action in beat.get("action_lines") or []:
            if isinstance(action, dict) and has_any(
                str(action.get("content") or ""), _VAGUE_VISUAL
            ):
                action["content"] = _repair_vague_visual(
                    str(action.get("content") or ""),
                    protagonist,
                )
    _ensure_escalation_beat(beats)


def harden_opening_hook(
    beat: dict[str, Any] | None,
    scene: dict[str, Any] | None = None,
) -> None:
    if not isinstance(beat, dict):
        return
    beat["beat_type"] = "hook"
    if opening_hook_screen_text_has_substance(beat_text(beat)):
        return
    beats = scene.get("beats") if isinstance(scene, dict) else None
    if not isinstance(beats, list):
        return
    current = str(beat.get("visible_event") or "").strip()
    for later_beat in beats[1:]:
        if not isinstance(later_beat, dict):
            continue
        evidence = str(later_beat.get("visible_event") or "").strip()
        if not evidence:
            continue
        if not opening_hook_screen_text_has_substance(f"{beat_text(beat)} {evidence}"):
            continue
        beat["visible_event"] = (
            f"{current.rstrip('。')}；{evidence}" if current else evidence
        )
        return


def harden_final_cliffhanger(
    beat: dict[str, Any] | None,
    scene: dict[str, Any] | None = None,
) -> None:
    if not isinstance(beat, dict):
        return
    beat["beat_type"] = "cliffhanger"
    text = " ".join(
        [
            str(beat.get("visible_event") or ""),
            str(beat.get("cliffhanger_tag") or ""),
            *[
                str(action.get("content") or "")
                for action in beat.get("action_lines") or []
                if isinstance(action, dict)
            ],
            *[
                str(line.get("content") or "")
                for line in beat.get("dialogue_lines") or []
                if isinstance(line, dict)
            ],
        ]
    )
    if is_concrete_unresolved_cliffhanger_text(text):
        return
    conflict = scene.get("conflict") if isinstance(scene, dict) else None
    opposition = (
        str(conflict.get("opposition") or "").strip()
        if isinstance(conflict, dict)
        else ""
    )
    protagonist = preferred_character([beat])
    unresolved = compact(opposition)[:28] or "当前阻力"
    existing = str(beat.get("visible_event") or "").strip()
    beat["visible_event"] = (
        f"{existing.rstrip('。')}；{unresolved}仍未解除。"
        if existing
        else (
            f"{protagonist}停下动作，{unresolved}仍未解除。"
            if protagonist
            else f"{unresolved}仍未解除。"
        )
    )
    beat["cliffhanger_tag"] = f"{unresolved}仍未解决"
    if protagonist:
        beat.setdefault("action_lines", []).append(
            {
                "content": f"{protagonist}转向阻力来源，镜头停在尚未解决的状态上。",
                "timing": "outro",
                "type": "action",
            }
        )


def align_scene_durations(
    scene: dict[str, Any], beats: list[dict[str, Any]], opening: bool
) -> None:
    estimated = to_float(scene.get("estimated_duration_seconds")) or 0
    if estimated <= 0 or not beats:
        return
    first = min(3.0, max(1.0, estimated / len(beats))) if opening else 0.0
    if first:
        beats[0]["duration_seconds"] = round(first, 2)
    rest = beats[1:] if first else beats
    remaining = max(1.0, estimated - first)
    base = round(remaining / len(rest), 2)
    for index, beat in enumerate(rest):
        beat["duration_seconds"] = (
            base if index < len(rest) - 1 else round(remaining - (base * index), 2)
        )


def _repair_vague_visual(text: str, protagonist: str | None) -> str:
    clauses = [
        item.strip()
        for item in re.split(r"[，,；;。]", text)
        if item.strip() and not has_any(item, _VAGUE_VISUAL)
    ]
    concrete = "，".join(clauses)
    if visible_len(concrete) >= 4:
        return concrete.rstrip("。") + "。"
    if not protagonist:
        return text
    target = _concrete_object(text)
    return f"{protagonist}把{target}移到镜头前，状态变化清楚可见。"


def _concrete_object(text: str) -> str:
    choices = (
        ("合同", "合同"),
        ("奖金", "奖金记录"),
        ("日志", "日志"),
        ("文件", "文件"),
        ("数据", "数据"),
        ("权限", "权限"),
        ("素材", "素材"),
        ("方案", "方案"),
        ("客户", "客户确认页"),
        ("倒计时", "倒计时页面"),
        ("手机", "手机页面"),
        ("电话", "电话页面"),
    )
    return next((label for marker, label in choices if marker in text), "当前结果")


def _ensure_escalation_beat(beats: list[dict[str, Any]]) -> None:
    if any(beat.get("beat_type") in {"conflict", "reveal"} for beat in beats):
        return
    candidates = [
        beat for beat in beats if beat.get("beat_type") not in {"hook", "cliffhanger"}
    ]
    if candidates:
        candidates[0]["beat_type"] = "reveal"
