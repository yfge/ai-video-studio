from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.services.script.beat_contract_normalizer import (
    flatten_contract_to_script_payload,
    normalize_script_beat_contract,
)
from app.services.script.beat_contract_auto_repair_anchors import (
    apply_workplace_anchors,
    needs_workplace_anchors,
)
from app.services.script.beat_contract_auto_repair_common import (
    progression_action,
    progression_dialogue,
    progression_event,
    scene_role,
)
from app.services.script.beat_contract_auto_repair_conflict import (
    repair_scene_conflict,
)
from app.services.script.beat_contract_auto_repair_polish import (
    align_scene_durations,
    dedupe_progression,
    harden_final_cliffhanger,
    harden_opening_hook,
    repair_beats,
    shorten_dialogue_lines,
)


def auto_repair_script_beat_contract(
    content: dict[str, Any],
    *,
    format_type: str = "screenplay",
    language: str = "zh-CN",
    episode_number: int | None = None,
    template_style: str | None = "commercial_vertical_drama",
    target_chars_per_episode: int | None = 1300,
    title: str | None = None,
) -> dict[str, Any]:
    raw_contract = _extract_contract(content)
    if not isinstance(raw_contract, dict):
        return content

    repaired = deepcopy(raw_contract)
    scenes = repaired.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        return content

    needs_anchors = needs_workplace_anchors(scenes)
    for scene_index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            continue
        beats = _ensure_scene(scene, scene_index, len(scenes))
        if needs_anchors:
            apply_workplace_anchors(scene, beats, scene_index, len(scenes))
        repair_scene_conflict(scene)
        harden_opening_hook(beats[0] if scene_index == 0 else None)
        harden_final_cliffhanger(beats[-1] if scene_index == len(scenes) - 1 else None)
        repair_beats(scene, beats)
        align_scene_durations(scene, beats, scene_index == 0)
        dedupe_progression(beats)
        shorten_dialogue_lines(beats)

    try:
        contract = normalize_script_beat_contract(repaired)
        flattened = flatten_contract_to_script_payload(
            contract,
            format_type=format_type,
            language=language,
            episode_number=episode_number,
            template_style=template_style,
            target_chars_per_episode=target_chars_per_episode,
            title=title,
        )
    except Exception:
        return content

    metadata = {**dict(content.get("metadata") or {}), **flattened["metadata"]}
    return {
        **content,
        **flattened,
        "metadata": metadata,
        "structured_script_contract": contract.model_dump(mode="json"),
    }


def _extract_contract(content: dict[str, Any]) -> dict[str, Any] | None:
    metadata = content.get("metadata") if isinstance(content.get("metadata"), dict) else {}
    top_level = (
        {
            key: value
            for key, value in content.items()
            if key not in {"metadata", "structured_script_contract"}
        }
        if isinstance(content.get("scenes"), list)
        else None
    )
    candidates = [
        content.get("structured_script_contract"),
        top_level,
        metadata.get("structured_script_contract"),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and _can_normalize(candidate):
            return candidate
    for candidate in candidates:
        coerced = _coerce_malformed_contract(candidate)
        if coerced and _can_normalize(coerced):
            return coerced
    return None


def _coerce_malformed_contract(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict) or not isinstance(payload.get("scenes"), list):
        return None
    candidate = deepcopy(payload)
    candidate.setdefault("contract_version", "script-beat-v1")
    candidate.setdefault("title", "AP短剧")
    candidate.setdefault("logline", "AP用证据核实被篡改的数据。")
    for index, scene in enumerate(candidate["scenes"], start=1):
        if not isinstance(scene, dict):
            continue
        scene.setdefault("scene_number", index)
        scene.setdefault("slug_line", "内. 会议室 - 日")
        scene.setdefault("location", "会议室")
        scene.setdefault("time_of_day", "日")
        scene.setdefault("estimated_duration_seconds", 15)
        scene.setdefault("dramatic_role", scene_role(index, len(candidate["scenes"])))
        scene["conflict"] = {
            **dict(scene.get("conflict") or {}),
            "question": (scene.get("summary") or "AP如何锁定篡改证据？"),
            "stakes": "若不澄清，300万项目合同当场作废，客户终止签字验收。",
            "opposition": "客户质疑、被篡改文件和手机匿名短信阻止AP核实。",
            "turn": "AP把投影数字、原始文件和团队反应对齐，锁定篡改来源。",
        }
        _ensure_scene(scene, index - 1, len(candidate["scenes"]))
    return candidate


def _ensure_scene(scene: dict[str, Any], index: int, count: int) -> list[dict[str, Any]]:
    scene.setdefault("scene_number", index + 1)
    scene.setdefault("slug_line", "内. 会议室 - 日")
    scene.setdefault("location", "会议室")
    scene.setdefault("time_of_day", "日")
    scene.setdefault("estimated_duration_seconds", 15)
    scene.setdefault("dramatic_role", scene_role(index + 1, count))
    beats = scene.setdefault("beats", [])
    if not isinstance(beats, list):
        beats = []
        scene["beats"] = beats
    while len(beats) < 3:
        beats.append({"order_index": len(beats) + 1})
    for order, beat in enumerate(beats, start=1):
        if not isinstance(beat, dict):
            beat = {"order_index": order}
            beats[order - 1] = beat
        beat["order_index"] = order
        beat.setdefault("beat_type", "conflict" if order < 3 else "reveal")
        beat.setdefault("dramatic_purpose", "AP用屏幕证据推进核实。")
        beat.setdefault("visible_event", progression_event("AP", order))
        beat.setdefault(
            "action_lines",
            [{"content": progression_action("AP", order), "timing": "mid", "type": "action"}],
        )
        beat.setdefault(
            "dialogue_lines",
            [{"character": "AP", "content": progression_dialogue(order)}],
        )
        beat.setdefault("duration_seconds", 5)
    return [beat for beat in beats if isinstance(beat, dict)]


def _can_normalize(payload: dict[str, Any]) -> bool:
    try:
        normalize_script_beat_contract(payload)
        return True
    except Exception:
        return False


def _has_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _beat_text(beat: dict[str, Any]) -> str:
    return _compact(str(beat.get("visible_event") or "") + _beat_screen_text(beat))


def _beat_screen_text(beat: dict[str, Any]) -> str:
    return "".join(str(action.get("content") or "") for action in beat.get("action_lines", []) if isinstance(action, dict))


def _scene_screen_text(beats: list[dict[str, Any]]) -> str:
    return _compact("".join(str(beat.get("visible_event") or "") + _beat_screen_text(beat) for beat in beats))


def _compact(text: str) -> str:
    return "".join(ch for ch in text if not ch.isspace())


def _visible_len(text: str) -> int:
    return len(_compact(text))


def _to_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
