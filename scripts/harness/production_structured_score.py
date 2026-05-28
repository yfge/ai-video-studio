"""Structured script scoring for provider-chain quality checks."""

from __future__ import annotations

import re
from typing import Any

from scripts.harness.production_character_score import character_anchor_failed_checks
from scripts.harness.production_duration_score import duration_failed_checks
from scripts.harness.production_script_payload import extract_script_payload

STRUCTURED_SCORE_PASS = 3.5
STRUCTURED_CORE_MIN = 3.0


def structured_script_score(payload: dict[str, Any]) -> dict[str, Any]:
    script = extract_script_payload(payload)
    scenes = script.get("scenes") if isinstance(script.get("scenes"), list) else []
    dialogue_lines = [
        str(line.get("line") or line.get("content") or "")
        for scene in scenes
        for line in [*list(scene.get("dialogue") or []), *beat_dialogue_lines(scene)]
        if isinstance(line, dict)
    ]
    failed_checks = _beat_failed_checks(scenes)
    values = {
        "hook_3s": _score_text(
            " ".join([str(script.get("logline") or ""), _first_plot(scenes)]),
            ["发现", "警报", "失控", "最后", "反转", "不能", "倒计时"],
            base=3.0,
        ),
        "conflict_clarity": _score_text(
            " ".join(str(scene.get("plot") or "") for scene in scenes),
            ["冲突", "阻止", "抢", "危机", "质疑", "失败", "必须", "倒计时"],
            base=3.0,
        ),
        "dialogue_audibility": _dialogue_score(dialogue_lines),
        "filmability": _filmability_score(scenes),
        "ending_twist": _score_text(
            str(scenes[-1].get("plot") if scenes else ""),
            ["反转", "真相", "却", "原来", "最后", "悬念", "门开了"],
            base=3.0,
        ),
    }
    average = round(sum(values.values()) / len(values), 2) if values else 0.0
    core_min = min(values.values()) if values else 0.0
    return {
        "status": "completed",
        "scores": values,
        "average": average,
        "core_min": core_min,
        "failed_checks": sorted(set(failed_checks)),
        "passed": (
            not failed_checks
            and average >= STRUCTURED_SCORE_PASS
            and core_min >= STRUCTURED_CORE_MIN
        ),
        "pass_threshold": STRUCTURED_SCORE_PASS,
        "core_min_threshold": STRUCTURED_CORE_MIN,
    }


def _beat_failed_checks(scenes: list[dict[str, Any]]) -> list[str]:
    failed_checks: list[str] = []
    for index, scene in enumerate(scenes, start=1):
        beats = scene_beats(scene)
        if len(beats) < 3:
            failed_checks.append("scene_min_beats")
        if any(not beat.get("visible_event") for beat in beats):
            failed_checks.append("beat_visible_event")
        if index == 1 and beats and beats[0].get("beat_type") != "hook":
            failed_checks.append("opening_hook_required")
    has_payoff = any(
        beat.get("beat_type") == "payoff" or beat.get("payoff_tag")
        for scene in scenes
        for beat in scene_beats(scene)
    )
    if not has_payoff:
        failed_checks.append("payoff_required")
    final_beats = scene_beats(scenes[-1]) if scenes else []
    if final_beats and (
        final_beats[-1].get("beat_type") != "cliffhanger"
        and not final_beats[-1].get("cliffhanger_tag")
    ):
        failed_checks.append("cliffhanger_required")
    failed_checks.extend(duration_failed_checks(scenes))
    failed_checks.extend(character_anchor_failed_checks(scenes))
    return failed_checks


def scene_beats(scene: dict[str, Any]) -> list[dict[str, Any]]:
    beats = scene.get("beats")
    if not isinstance(beats, list):
        return []
    return [beat for beat in beats if isinstance(beat, dict)]


def beat_dialogue_lines(scene_or_beat: dict[str, Any]) -> list[dict[str, Any]]:
    lines: list[dict[str, Any]] = []
    for beat in scene_beats(scene_or_beat) or [scene_or_beat]:
        dialogue = beat.get("dialogue") or beat.get("dialogue_lines") or []
        if isinstance(dialogue, list):
            lines.extend(line for line in dialogue if isinstance(line, dict))
    return lines


def beat_action_lines(beat: dict[str, Any]) -> list[str]:
    actions = beat.get("action") or beat.get("action_lines") or []
    if not isinstance(actions, list):
        return []
    out: list[str] = []
    for item in actions:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and item.get("content"):
            out.append(str(item["content"]))
    return out


def _score_text(text: str, keywords: list[str], *, base: float) -> float:
    hits = sum(1 for keyword in keywords if keyword in text)
    return min(5.0, round(base + hits * 0.4, 2))


def _dialogue_score(dialogue_lines: list[str]) -> float:
    if not dialogue_lines:
        return 0.0
    visible_lengths = [_visible_chars(line) for line in dialogue_lines]
    max_len = max(visible_lengths)
    avg_len = sum(visible_lengths) / len(visible_lengths)
    if max_len <= 15 and avg_len <= 12:
        return 4.5
    if max_len <= 22 and avg_len <= 18:
        return 3.8
    if max_len <= 30:
        return 3.0
    return 2.5


def _filmability_score(scenes: list[dict[str, Any]]) -> float:
    if not scenes:
        return 0.0
    complete = sum(
        1
        for scene in scenes
        if scene.get("plot")
        and scene.get("video_prompt")
        and (scene.get("dialogue") or scene_beats(scene))
    )
    return round(min(5.0, 3.0 + (complete / len(scenes)) * 1.5), 2)


def _first_plot(scenes: list[dict[str, Any]]) -> str:
    return str(scenes[0].get("plot") if scenes else "")


def _visible_chars(text: str) -> int:
    return len(re.sub(r"[\s，。！？!?：:、,.…\"'“”‘’]", "", text))
