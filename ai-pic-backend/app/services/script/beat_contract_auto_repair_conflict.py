from __future__ import annotations

import re
from typing import Any

from app.services.script.beat_contract_auto_repair_common import (
    compact,
    has_any,
    visible_len,
)
from app.services.script.beat_contract_conflict import (
    has_concrete_opposition,
    has_concrete_stakes,
)
from app.services.script.beat_contract_specificity import is_specific_text

_VAGUE = (
    "意识到",
    "明白",
    "内心",
    "崩溃",
    "发现关键线索",
    "关键线索",
    "冲突爆发",
    "数据不一致的发现",
    "出现转折",
    "发生反转",
    "信任崩溃",
    "紧张感",
    "潜在危机",
    "制造冲突",
    "制造悬念",
    "留下悬念",
    "推动冲突",
    "升级冲突",
    "推进剧情",
)
_ABSTRACT_OPPOSITION = (
    "幕后黑手",
    "神秘力量",
    "未知势力",
    "神秘人",
    "匿名威胁",
    "崩溃",
)
_THIN_OPPOSITION = {"篡改者", "内部篡改者", "内鬼", "同事", "团队成员"}


def repair_scene_conflict(scene: dict[str, Any]) -> None:
    conflict = scene.setdefault("conflict", {})
    if not isinstance(conflict, dict):
        conflict = {}
        scene["conflict"] = conflict
    beats = [item for item in scene.get("beats") or [] if isinstance(item, dict)]
    protagonist = _preferred_character(beats)
    anchor = _scene_anchor(scene, beats)
    if anchor is None:
        return
    if not str(conflict.get("question") or "").strip():
        conflict["question"] = scene.get("summary") or (
            f"{protagonist}能否解决“{anchor}”带来的问题？"
            if protagonist
            else f"能否解决“{anchor}”带来的问题？"
        )
    stakes = str(conflict.get("stakes") or "")
    if (
        visible_len(stakes) < 6
        or has_any(stakes, _VAGUE)
        or not has_concrete_stakes(stakes)
    ):
        stakes_object = _stakes_object(scene, beats)
        if stakes_object:
            consequence = (
                f"{protagonist}会失去完成目标的机会"
                if protagonist
                else "本场目标将无法完成"
            )
            conflict["stakes"] = (
                f"若本场无法处理“{anchor}”，{stakes_object}将无法交付，"
                f"{consequence}。"
            )
    opposition = str(conflict.get("opposition") or "")
    if (
        visible_len(opposition) < 4
        or compact(opposition) in _THIN_OPPOSITION
        or has_any(opposition, _ABSTRACT_OPPOSITION)
        or not has_concrete_opposition(opposition)
    ):
        source = _opposition_source(opposition)
        evidence = _concrete_opposition_evidence(beats)
        if evidence:
            conflict["opposition"] = (
                f"{source}；{evidence}"
                if source and source not in evidence
                else evidence
            )
    turn = str(conflict.get("turn") or "")
    if visible_len(turn) < 6 or has_any(turn, _VAGUE) or not is_specific_text(turn):
        concrete_turn = _concrete_turn(beats)
        if concrete_turn:
            conflict["turn"] = concrete_turn
        else:
            actor = f"{protagonist}完成" if protagonist else "完成"
            conflict["turn"] = (
                f"{actor}与“{anchor}”直接相关的可见操作后，现场结果发生变化。"
            )


def _preferred_character(beats: list[dict[str, Any]]) -> str | None:
    for beat in beats:
        for line in beat.get("dialogue_lines") or []:
            if not isinstance(line, dict):
                continue
            character = str(line.get("character") or "").strip()
            if character and character not in {"主角", "角色", "旁白"}:
                return character
    return None


def _scene_anchor(
    scene: dict[str, Any],
    beats: list[dict[str, Any]],
) -> str | None:
    values = [
        scene.get("summary"),
        *[beat.get("visible_event") for beat in beats],
        *[
            action.get("content")
            for beat in beats
            for action in beat.get("action_lines") or []
            if isinstance(action, dict)
        ],
        scene.get("slug_line"),
    ]
    for value in values:
        text = compact(str(value or "")).strip("。")
        if visible_len(text) >= 4 and not has_any(text, _VAGUE):
            return text[:24]
    return None


def _stakes_object(
    scene: dict[str, Any],
    beats: list[dict[str, Any]],
) -> str | None:
    text = compact(
        " ".join(
            [
                str(scene.get("summary") or ""),
                str(scene.get("slug_line") or ""),
                *[str(beat.get("visible_event") or "") for beat in beats],
                *[
                    str(action.get("content") or "")
                    for beat in beats
                    for action in beat.get("action_lines") or []
                    if isinstance(action, dict)
                ],
            ]
        )
    )
    for marker in (
        "合同",
        "证据",
        "文件",
        "日志",
        "权限",
        "资产",
        "视频",
        "音频",
        "订单",
        "账单",
        "流程",
        "系统回执",
        "邮件",
        "记录",
        "方案",
        "素材",
    ):
        if marker in text:
            return marker
    return None


def _concrete_turn(beats: list[dict[str, Any]]) -> str | None:
    for beat in reversed(beats):
        values = [
            beat.get("visible_event"),
            *[
                action.get("content")
                for action in reversed(beat.get("action_lines") or [])
                if isinstance(action, dict)
            ],
        ]
        for value in values:
            text = str(value or "").strip()
            if is_specific_text(text):
                return text
    return None


def _opposition_source(value: str) -> str | None:
    source = compact(value).strip("。")
    replacements = {
        "幕后黑手": "对手",
        "神秘力量": "外部对手",
        "未知势力": "外部对手",
        "神秘人": "对手",
        "匿名威胁": "匿名消息背后的对手",
        "崩溃": "",
    }
    for old, new in replacements.items():
        source = source.replace(old, new)
    source = re.split(r"[，,；;。]|但手机|但", source, maxsplit=1)[0]
    return source[:24] if visible_len(source) >= 2 else None


def _concrete_opposition_evidence(
    beats: list[dict[str, Any]],
) -> str | None:
    for beat in beats:
        values = [
            beat.get("visible_event"),
            *[
                action.get("content")
                for action in beat.get("action_lines") or []
                if isinstance(action, dict)
            ],
        ]
        for value in values:
            text = str(value or "").strip()
            if is_specific_text(text) and has_concrete_opposition(text):
                return text
    return None
