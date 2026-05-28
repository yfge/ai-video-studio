"""Payload helpers for provider chain regression."""

from __future__ import annotations

import json
import re
from typing import Any

TEXT_MODEL = "deepseek-v4-flash"
IMAGE_MODEL = "openai:chatgpt-img-2"
VIDEO_MODEL = "seedance-2.0-i2v"
SEEDANCE_CANONICAL = "doubao-seedance-2-0-260128"


def scene_durations(mode: str) -> list[int]:
    return [4] if mode == "smoke" else [15, 15]


def build_script_prompt(mode: str, premise: str | None = None) -> str:
    durations = scene_durations(mode)
    premise_text = (
        f" Story premise to follow: {premise.strip()}. "
        if isinstance(premise, str) and premise.strip()
        else " "
    )
    return (
        "Return only valid JSON. Write a compact Chinese short-drama script for a "
        "non-real 3D cartoon robot character. No live-action human, no celebrity, "
        "no photorealistic face."
        f"{premise_text}"
        "The JSON schema is: "
        '{"title":str,"logline":str,"characters":[{"name":str,"role":str,'
        '"appearance_prompt":str,"consistency_anchor":str}],'
        '"scenes":[{"scene_id":str,"duration_seconds":int,"plot":str,'
        '"dialogue":[{"speaker":str,"line":str}],'
        '"beats":[{"order_index":int,"beat_type":str,"dramatic_purpose":str,'
        '"visible_event":str,"action":[str],"dialogue":[{"speaker":str,"line":str}],'
        '"duration_seconds":number,"hook_tag":str,"payoff_tag":str,'
        '"cliffhanger_tag":str}],"image_prompt":str,'
        '"video_prompt":str}]}. '
        f"Create exactly {len(durations)} scene(s) with durations {durations}. "
        "Use one stable protagonist across every scene; keep the protagonist's "
        "consistency_anchor as a visual descriptor, not just a name. Supporting "
        "characters, if any, must stay secondary and must not replace the protagonist. "
        "Do not use generic speaker names like 主角, 角色, 男主, 女主, or 旁白; "
        "reuse the same named protagonist in scene dialogue and beat dialogue. "
        "Every scene must include 3 to 5 beats. The first beat of scene 1 must "
        "be hook. At least one beat across the script must be payoff. The final "
        "beat must be cliffhanger. "
        "Every dialogue line must be <= 15 visible Chinese/English characters. "
        "Scene 1 must open with an immediate conflict or countdown hook. The final "
        "scene must end on an unresolved reversal or question, not a full resolution. "
        "Every scene must have plot, one or two short dialogue lines, and a Seedance-ready "
        "video prompt that includes the same character anchor and the dialogue source."
    )


def extract_structured_script(content: str, expected_scene_count: int) -> dict[str, Any]:
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fence:
        text = fence.group(1)
    elif not text.startswith("{"):
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            text = match.group(0)

    data = json.loads(text)
    scenes = data.get("scenes")
    characters = data.get("characters")
    if not isinstance(characters, list) or not characters:
        raise ValueError("script_missing_characters")
    if not isinstance(scenes, list) or len(scenes) != expected_scene_count:
        raise ValueError("script_scene_count_mismatch")

    for index, scene in enumerate(scenes, start=1):
        dialogue = scene.get("dialogue")
        if not scene.get("plot") or not scene.get("video_prompt"):
            raise ValueError(f"script_scene_{index}_missing_plot_or_video_prompt")
        if not isinstance(dialogue, list) or not dialogue:
            raise ValueError(f"script_scene_{index}_missing_dialogue")
        for line in dialogue:
            if (
                not isinstance(line, dict)
                or not line.get("speaker")
                or not line.get("line")
            ):
                raise ValueError(f"script_scene_{index}_invalid_dialogue")
        beats = scene.get("beats")
        if not isinstance(beats, list) or len(beats) < 3:
            raise ValueError(f"script_scene_{index}_missing_beats")
        for beat_index, beat in enumerate(beats, start=1):
            if not isinstance(beat, dict) or not beat.get("visible_event"):
                raise ValueError(f"script_scene_{index}_beat_{beat_index}_invalid")
    return data


def character_image_prompt(script: dict[str, Any]) -> str:
    character = script["characters"][0]
    return (
        f"{character.get('appearance_prompt', '')}. "
        f"{character.get('consistency_anchor', '')}. "
        "High quality 3D cartoon character reference sheet, expressive LED eyes, "
        "cinematic lighting, clean silhouette, non-real robot, no photorealistic human."
    )


def video_prompt(scene: dict[str, Any], character: dict[str, Any]) -> str:
    dialogue = " / ".join(f"{d['speaker']}: {d['line']}" for d in scene["dialogue"])
    return (
        f"{scene.get('video_prompt')}. "
        f"Character anchor: {character.get('consistency_anchor')}. "
        f"Plot: {scene.get('plot')}. Dialogue source: {dialogue}. "
        "3D cartoon style, non-real robot character, clear acting, readable story beat."
    )
