"""Reference image resolution for scene grid sheet generation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def resolve_reference_images(
    scene_number: int,
    ref_ctx: Any,
    *,
    character_refs: List[dict],
    environment_refs: List[str],
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Combine user-selected and auto-resolved character/environment refs.

    Explicit selections win; auto resolution falls back to scene bindings in
    the ImageRefContext (shot characters + environment images).
    """
    refs: List[str] = []
    refs_used: List[Dict[str, Any]] = []

    if character_refs:
        _collect_user_character_refs(character_refs, ref_ctx, refs, refs_used)
    else:
        _collect_scene_character_refs(scene_number, ref_ctx, refs, refs_used)

    if environment_refs:
        for url in environment_refs:
            if isinstance(url, str) and url.strip():
                refs.append(url.strip())
                refs_used.append(
                    {"type": "environment", "source": "user", "url": url.strip()}
                )
    else:
        for url in ref_ctx.env_images_by_scene.get(scene_number, [])[:2]:
            refs.append(url)
            refs_used.append({"type": "environment", "source": "scene", "url": url})

    deduped: List[str] = []
    for url in refs:
        if url not in deduped:
            deduped.append(url)
    return deduped, refs_used


def _collect_user_character_refs(
    character_refs: List[dict],
    ref_ctx: Any,
    refs: List[str],
    refs_used: List[Dict[str, Any]],
) -> None:
    for item in character_refs:
        if not isinstance(item, dict):
            continue
        url = (item.get("url") or "").strip()
        vip_id = _to_int(item.get("virtual_ip_id"))
        name = item.get("name")
        if not url and vip_id is not None:
            url = ref_ctx.char_image_map.get(vip_id) or _fallback_anchor(ref_ctx, vip_id) or ""
            vip = ref_ctx.vip_map.get(vip_id)
            name = name or (getattr(vip, "name", None) if vip else None)
        if url:
            refs.append(url)
            refs_used.append(
                {"type": "character", "name": name, "source": "user", "url": url}
            )


def _collect_scene_character_refs(
    scene_number: int,
    ref_ctx: Any,
    refs: List[str],
    refs_used: List[Dict[str, Any]],
) -> None:
    scene_obj = ref_ctx.scene_by_number.get(scene_number)
    bound_ids = (
        sorted(ref_ctx.scene_char_ids.get(scene_obj.id) or set())
        if scene_obj is not None
        else []
    )
    for vip_id in bound_ids[:4]:
        url = ref_ctx.char_image_map.get(vip_id) or _fallback_anchor(ref_ctx, vip_id)
        if url:
            vip = ref_ctx.vip_map.get(vip_id)
            refs.append(url)
            refs_used.append(
                {
                    "type": "character",
                    "name": getattr(vip, "name", None) if vip else None,
                    "source": "scene",
                    "url": url,
                }
            )


def _fallback_anchor(ref_ctx: Any, vip_id: int) -> Optional[str]:
    try:
        from app.services.storyboard.storyboard_character_anchors import (
            fallback_virtual_ip_anchor_url,
        )

        return fallback_virtual_ip_anchor_url(ref_ctx.vip_map.get(vip_id))
    except Exception:
        return None


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
