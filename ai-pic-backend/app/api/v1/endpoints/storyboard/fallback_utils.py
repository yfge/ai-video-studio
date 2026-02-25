"""Fallback text composition utilities for storyboard generation.

Provides helper functions to compose fallback descriptions and prompts
when AI generation fails or is unavailable.
"""

import re
from typing import Any, Dict, List, Optional

from app.models.script import Script

from .frame_utils import _to_int


def _trim_local(value: Any, limit: int = 120) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def _collect_dialogues_for_scene(
    script_obj: Script, scene_number: Optional[int], limit: int = 2
) -> List[str]:
    results: List[str] = []
    for item in script_obj.dialogues or []:
        if isinstance(item, dict):
            sn = _to_int(item.get("scene_number"))
            content = item.get("content") or item.get("text")
        else:
            sn = None
            content = str(item)
        if scene_number is not None and sn != scene_number:
            continue
        if not content:
            continue
        results.append(_trim_local(content, 80))
        if len(results) >= limit:
            break
    return results


def _collect_stage_for_scene(
    script_obj: Script, scene_number: Optional[int], limit: int = 2
) -> List[str]:
    results: List[str] = []
    for item in script_obj.stage_directions or []:
        if isinstance(item, dict):
            sn = _to_int(item.get("scene_number"))
            content = item.get("content") or item.get("direction")
        else:
            sn = None
            content = str(item)
        if scene_number is not None and sn != scene_number:
            continue
        if not content:
            continue
        results.append(_trim_local(content, 80))
        if len(results) >= limit:
            break
    return results


def _compose_fallback_text(
    scene_payload: Any,
    scene_number: Optional[int],
    *,
    script_obj: Script,
    base_text: str,
    shot: str,
    movement: str,
    composition: str,
) -> tuple:
    """Build a fallback description + ai_prompt pair from scene metadata."""
    details: List[str] = []
    if isinstance(scene_payload, dict):
        location = scene_payload.get("location") or scene_payload.get("place")
        time_info = scene_payload.get("time") or scene_payload.get("period")
        characters = scene_payload.get("characters") or scene_payload.get("cast")
        notes = scene_payload.get("notes")
        if location:
            details.append(f"地点:{_trim_local(location, 50)}")
        if time_info:
            details.append(f"时间:{_trim_local(time_info, 40)}")
        if characters:
            if isinstance(characters, list):
                details.append(
                    f"角色:{_trim_local(', '.join(map(str, characters)), 80)}"
                )
            else:
                details.append(f"角色:{_trim_local(characters, 80)}")
        if notes:
            details.append(f"备注:{_trim_local(notes, 80)}")
    dialogues = _collect_dialogues_for_scene(script_obj, scene_number)
    if dialogues:
        details.append("对白:" + " / ".join(dialogues))
    stage = _collect_stage_for_scene(script_obj, scene_number)
    if stage:
        details.append("舞台:" + " / ".join(stage))
    details.append("内容:" + _trim_local(base_text, 140))

    description = (
        "；".join(details)[:200] if details else _trim_local(base_text, 200)
    )
    return description, description


def generate_fallback_frames(
    script, scenes_filtered, scene_order, frames_per_scene, max_frames,
) -> List[Dict[str, Any]]:
    """Generate simple fallback storyboard frames from script structure."""
    shot_cycle = ["远景", "中景", "近景", "特写"]
    movement_cycle = ["固定", "推", "拉", "摇", "移", "跟", "变焦"]
    composition_cycle = ["三分法", "对称", "前后景", "对角线", "中心对称"]
    frames_fallback: List[Dict[str, Any]] = []
    frame_no = 1
    if scenes_filtered:
        for sidx, sc in enumerate(scenes_filtered, start=1):
            real_sn = scene_order[sidx - 1] if (sidx - 1) < len(scene_order) else sidx
            if max_frames and len(frames_fallback) >= max_frames:
                break
            desc = sc.get("description") if isinstance(sc, dict) else (str(sc) if sc else "")
            segments = [s for s in re.split(r"[。.!?！？]", desc or "") if s.strip()]
            for i in range(max(1, frames_per_scene)):
                if max_frames and len(frames_fallback) >= max_frames:
                    break
                text = segments[i] if i < len(segments) else (desc or f"场景 {sidx}")
                v = frame_no - 1
                shot = shot_cycle[v % len(shot_cycle)]
                movement = movement_cycle[v % len(movement_cycle)]
                comp = composition_cycle[v % len(composition_cycle)]
                description, ai_prompt = _compose_fallback_text(
                    sc if isinstance(sc, dict) else None, real_sn,
                    script_obj=script, base_text=text,
                    shot=shot, movement=movement, composition=comp,
                )
                frames_fallback.append({
                    "frame_number": frame_no, "scene_number": real_sn,
                    "shot_type": shot, "camera_movement": movement,
                    "composition": comp, "description": description,
                    "duration_seconds": max(2, min(12, 3 + (v % 3) - 1)),
                    "ai_prompt": ai_prompt, "reference_images": [],
                })
                frame_no += 1
    else:
        paragraphs = (script.content or "").split("\n\n")
        for para in paragraphs:
            if max_frames and len(frames_fallback) >= max_frames:
                break
            text = para.strip().replace("\n", " ")[:200]
            if not text:
                continue
            v = frame_no - 1
            shot = shot_cycle[v % len(shot_cycle)]
            movement = movement_cycle[v % len(movement_cycle)]
            comp = composition_cycle[v % len(composition_cycle)]
            description, ai_prompt = _compose_fallback_text(
                None, None, script_obj=script, base_text=text,
                shot=shot, movement=movement, composition=comp,
            )
            frames_fallback.append({
                "frame_number": frame_no, "scene_number": None,
                "shot_type": shot, "camera_movement": movement,
                "composition": comp, "description": description,
                "duration_seconds": max(2, min(12, 3 + (v % 3) - 1)),
                "ai_prompt": ai_prompt, "reference_images": [],
            })
            frame_no += 1
    return frames_fallback
