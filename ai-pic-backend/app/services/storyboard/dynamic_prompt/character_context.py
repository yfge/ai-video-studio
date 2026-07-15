"""Per-character appearance context for dynamic storyboard prompts."""

from __future__ import annotations

from typing import Any, Dict, List

APPEARANCE_CHAR_LIMIT = 600


def character_appearance(vip: Any) -> str:
    if vip is None:
        return ""
    value = getattr(vip, "description", None) or getattr(vip, "style_prompt", None)
    if value is None:
        return ""
    text = str(value).replace("\n", " ").strip()
    return text[:APPEARANCE_CHAR_LIMIT] + (
        "…" if len(text) > APPEARANCE_CHAR_LIMIT else ""
    )


def build_frame_characters(
    frame: dict[str, Any],
    scene_characters: List[Dict[str, str]],
    *,
    ref_ctx: Any = None,
) -> List[Dict[str, str]]:
    raw_characters = frame.get("characters")
    if not isinstance(raw_characters, list):
        return list(scene_characters)
    appearances = {
        str(item.get("name") or "").strip(): str(item.get("appearance") or "").strip()
        for item in scene_characters
        if isinstance(item, dict) and str(item.get("name") or "").strip()
    }
    result: List[Dict[str, str]] = []
    for raw_name in raw_characters:
        name = str(raw_name).strip() if raw_name is not None else ""
        if not name:
            continue
        appearance = appearances.get(name, "") or _appearance_from_ref_ctx(
            name,
            ref_ctx,
        )
        result.append({"name": name, "appearance": appearance})
    return result


def _appearance_from_ref_ctx(name: str, ref_ctx: Any) -> str:
    if ref_ctx is None:
        return ""
    character_id = getattr(ref_ctx, "name_to_vip_id", {}).get(name)
    vip = getattr(ref_ctx, "vip_map", {}).get(character_id)
    return character_appearance(vip)
