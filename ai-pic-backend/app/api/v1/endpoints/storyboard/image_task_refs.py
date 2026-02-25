"""Reference image loading for storyboard image generation tasks.

Loads environment images, character anchor images, and builds
per-scene reference image mappings from the database.
"""

from collections import defaultdict
from typing import Any, Dict, List

from app.core.logging import get_logger
from app.models.script import Episode, Script
from app.models.story_structure import Environment, Scene, Shot
from app.models.virtual_ip import VirtualIP, VirtualIPImage

from .frame_utils import _abs_url

logger = get_logger("storyboard_image_refs")


class ImageRefContext:
    """Holds preloaded reference image data for storyboard image generation."""

    def __init__(self):
        self.scene_by_number: Dict[int, Scene] = {}
        self.env_images_by_scene: Dict[int, List[str]] = {}
        self.scene_char_ids: Dict[int, set] = defaultdict(set)
        self.vip_map: Dict[int, VirtualIP] = {}
        self.char_image_map: Dict[int, str] = {}
        self.name_to_vip_id: Dict[str, int] = {}


def load_image_ref_context(db, script: Script, script_id: int) -> ImageRefContext:
    """Load all reference images context from DB for a script.

    Queries scenes, environments, characters (via shots), and virtual IP
    images to build a complete reference context for image generation.
    """
    ctx = ImageRefContext()

    scenes = db.query(Scene).filter(Scene.script_id == script_id).all()
    env_ids: set = set()
    scene_ids: list = []
    for sc in scenes:
        try:
            sn = int(sc.scene_number)
            ctx.scene_by_number[sn] = sc
        except Exception:
            continue
        scene_ids.append(sc.id)
        if sc.environment_id:
            env_ids.add(sc.environment_id)

    # Load environment reference images
    if env_ids:
        envs = db.query(Environment).filter(Environment.id.in_(env_ids)).all()
        env_map = {env.id: env for env in envs}
        for sc in scenes:
            if sc.environment_id and sc.environment_id in env_map:
                refs = env_map[sc.environment_id].reference_images or []
                ctx.env_images_by_scene[int(sc.scene_number)] = [
                    _abs_url(u) for u in refs if u
                ]

    # Load character IDs from shots
    if scene_ids:
        shots = db.query(Shot).filter(Shot.scene_id.in_(scene_ids)).all()
        for shot in shots:
            for cid in shot.character_ids or []:
                try:
                    ctx.scene_char_ids[shot.scene_id].add(int(cid))
                except Exception:
                    continue

    # Build character registry
    all_char_ids = {cid for ids in ctx.scene_char_ids.values() for cid in ids}
    try:
        from app.services.storyboard.storyboard_character_anchors import (
            extract_virtual_ip_name_aliases,
            get_story_character_virtual_ip_ids,
        )
        episode = db.query(Episode).filter(Episode.id == script.episode_id).first()
        story_id = int(episode.story_id) if episode and episode.story_id else None
        if story_id:
            all_char_ids.update(get_story_character_virtual_ip_ids(db, story_id))
    except Exception:
        pass

    if all_char_ids:
        _load_character_images(db, all_char_ids, ctx)
        _build_name_alias_map(ctx)

    return ctx


def _load_character_images(db, all_char_ids: set, ctx: ImageRefContext):
    """Load VirtualIP records and their default/latest images."""
    vips = db.query(VirtualIP).filter(VirtualIP.id.in_(all_char_ids)).all()
    ctx.vip_map = {v.id: v for v in vips}
    images = (
        db.query(VirtualIPImage)
        .filter(VirtualIPImage.virtual_ip_id.in_(all_char_ids))
        .order_by(VirtualIPImage.is_default.desc(), VirtualIPImage.created_at.desc())
        .all()
    )
    for img in images:
        if img.virtual_ip_id in ctx.char_image_map:
            continue
        url = img.oss_url or img.file_path
        if url:
            ctx.char_image_map[img.virtual_ip_id] = _abs_url(url)


def _build_name_alias_map(ctx: ImageRefContext):
    """Build name-to-VirtualIP-ID mapping including aliases."""
    try:
        from app.services.storyboard.storyboard_character_anchors import (
            extract_virtual_ip_name_aliases,
        )
    except ImportError:
        return

    for vid, vip in ctx.vip_map.items():
        name = getattr(vip, "name", None)
        try:
            aliases = extract_virtual_ip_name_aliases(name)
        except Exception:
            aliases = [name] if isinstance(name, str) else []
        for alias in aliases:
            if isinstance(alias, str) and alias.strip():
                ctx.name_to_vip_id.setdefault(alias.strip(), int(vid))


def build_frame_references(
    frame: Dict[str, Any],
    idx: int,
    ctx: ImageRefContext,
    *,
    prompt: str,
    reference_images: list | None,
    labeled_references: list | None,
) -> tuple:
    """Build the complete reference image list and notes for a single frame.

    Returns:
        (ref_images, reference_notes, char_anchor_refs) tuple.
    """
    from .frame_utils import _normalize_reference_images, _to_int

    scene_no = _to_int(frame.get("scene_number"))
    reference_notes: List[Dict[str, Any]] = []

    # 1) Frame-level references
    frame_refs = _normalize_reference_images(frame.get("reference_images") or [])
    if frame_refs:
        reference_notes.append({"type": "frame"})

    # 2) User-provided references
    if labeled_references:
        payload_refs = _normalize_reference_images(
            [ref.get("url") for ref in labeled_references if ref.get("url")]
        )
    else:
        payload_refs = _normalize_reference_images(reference_images or [])
    if payload_refs:
        reference_notes.append({"type": "user"})

    # 3) Character anchor references
    char_anchor_refs = _resolve_character_refs(
        frame, scene_no, ctx, prompt, reference_notes,
    )

    # 4) Environment references
    env_refs = _normalize_reference_images(
        ctx.env_images_by_scene.get(scene_no or -1, []) or []
    )
    if env_refs:
        reference_notes.append({"type": "environment"})

    # Combine: user refs first, then frame/char/env
    ref_images_raw: List[str] = []
    if payload_refs:
        ref_images_raw.extend(payload_refs)
    else:
        ref_images_raw.extend(frame_refs)
        ref_images_raw.extend(char_anchor_refs)
        ref_images_raw.extend(env_refs)

    ref_images = _normalize_reference_images(ref_images_raw)
    return ref_images, reference_notes, char_anchor_refs


def _resolve_character_refs(frame, scene_no, ctx, prompt, reference_notes):
    """Resolve character anchor images for a frame."""
    from .frame_utils import _abs_url

    char_anchor_refs: List[str] = []
    candidate_char_ids: list = []
    source: str | None = None

    if scene_no and scene_no in ctx.scene_by_number:
        sc_obj = ctx.scene_by_number.get(scene_no)
        if sc_obj:
            bound_ids = ctx.scene_char_ids.get(sc_obj.id) or set()
            if bound_ids:
                candidate_char_ids = [int(cid) for cid in bound_ids]
                source = "shot"

    if not candidate_char_ids and ctx.name_to_vip_id:
        try:
            from app.services.storyboard.storyboard_character_anchors import (
                infer_character_ids_from_text,
            )
            candidate_char_ids = infer_character_ids_from_text(
                prompt, ctx.name_to_vip_id, max_matches=4,
            )
            if candidate_char_ids:
                source = "prompt"
        except Exception:
            pass

    for cid in candidate_char_ids[:4]:
        vip = ctx.vip_map.get(cid)
        name = getattr(vip, "name", None) if vip else None
        if not isinstance(name, str) or not name.strip():
            name = f"角色{cid}"
        img_url = ctx.char_image_map.get(cid)
        if not img_url:
            try:
                from app.services.storyboard.storyboard_character_anchors import (
                    fallback_virtual_ip_anchor_url,
                )
                img_url = fallback_virtual_ip_anchor_url(vip)
            except Exception:
                img_url = None
        if img_url:
            note: Dict[str, Any] = {"type": "character", "name": name}
            if source:
                note["source"] = source
            reference_notes.append(note)
            char_anchor_refs.append(_abs_url(img_url))

    return char_anchor_refs
