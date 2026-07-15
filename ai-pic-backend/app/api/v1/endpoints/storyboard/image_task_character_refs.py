"""Character-specific reference selection for storyboard image tasks."""

from __future__ import annotations

from typing import Any


def resolve_character_refs(
    frame: dict[str, Any],
    scene_no: int | None,
    ctx,
    prompt: str,
) -> tuple[list[str], list[dict[str, Any]], list[int]]:
    """Resolve anchors, prioritizing the frame's explicit cast contract."""

    candidate_ids, source = _candidate_character_ids(frame, scene_no, ctx, prompt)
    refs: list[str] = []
    notes: list[dict[str, Any]] = []
    for character_id in candidate_ids[:4]:
        vip = ctx.vip_map.get(character_id)
        name = getattr(vip, "name", None) if vip else None
        if not isinstance(name, str) or not name.strip():
            name = f"角色{character_id}"
        url = _anchor_url(ctx, character_id, vip)
        if not url:
            continue
        note: dict[str, Any] = {"type": "character", "name": name}
        if source:
            note["source"] = source
        notes.append(note)
        refs.append(url)
    return refs, notes, candidate_ids


def filter_frame_character_refs(
    frame: dict[str, Any],
    refs: list[str],
    selected_ids: list[int],
    ctx,
) -> list[str]:
    """Remove known anchors for characters excluded by an explicit frame cast."""

    if not isinstance(frame.get("characters"), list):
        return refs
    all_character_urls = {
        url
        for character_id, vip in ctx.vip_map.items()
        if (url := _anchor_url(ctx, int(character_id), vip))
    }
    selected_urls = {
        url
        for character_id in selected_ids
        if (url := _anchor_url(ctx, character_id, ctx.vip_map.get(character_id)))
    }
    return [
        url for url in refs if url not in all_character_urls or url in selected_urls
    ]


def _candidate_character_ids(
    frame, scene_no, ctx, prompt
) -> tuple[list[int], str | None]:
    explicit = frame.get("characters")
    if isinstance(explicit, list):
        ids = _ids_from_explicit_names(explicit, ctx)
        return ids, "frame" if ids else None

    if scene_no and scene_no in ctx.scene_by_number:
        scene = ctx.scene_by_number.get(scene_no)
        bound = ctx.scene_char_ids.get(getattr(scene, "id", None)) or set()
        if bound:
            return [int(character_id) for character_id in sorted(bound)], "shot"

    return _ids_from_prompt(prompt, ctx), "prompt"


def _ids_from_explicit_names(names: list[Any], ctx) -> list[int]:
    matched: list[int] = []
    for raw_name in names:
        name = str(raw_name).strip() if raw_name is not None else ""
        character_id = ctx.name_to_vip_id.get(name) if name else None
        if character_id is not None and int(character_id) not in matched:
            matched.append(int(character_id))
    return matched


def _ids_from_prompt(prompt: str, ctx) -> list[int]:
    if not ctx.name_to_vip_id:
        return []
    try:
        from app.services.storyboard.storyboard_character_anchors import (
            infer_character_ids_from_text,
        )

        return infer_character_ids_from_text(
            prompt,
            ctx.name_to_vip_id,
            max_matches=4,
        )
    except Exception:
        return []


def _anchor_url(ctx, character_id: int, vip) -> str | None:
    from .frame_utils import _abs_url

    url = ctx.char_image_map.get(character_id)
    if not url:
        try:
            from app.services.storyboard.storyboard_character_anchors import (
                fallback_virtual_ip_anchor_url,
            )

            url = fallback_virtual_ip_anchor_url(vip)
        except Exception:
            url = None
    return _abs_url(url) if url else None
