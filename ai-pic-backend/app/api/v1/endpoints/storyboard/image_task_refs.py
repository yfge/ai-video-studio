"""Reference image loading for storyboard image generation tasks.

Loads environment images, character anchor images, and builds
per-scene reference image mappings from the database.
"""

from collections import defaultdict
from typing import Any, Dict, List

from app.core.logging import get_logger
from app.models.script import Script
from app.models.story_structure import Scene
from app.models.virtual_ip import VirtualIP
from app.repositories.storyboard_image_reference_repository import (
    StoryboardImageReferenceRepository,
)

from .frame_utils import _abs_url
from .image_task_character_refs import (
    filter_frame_character_refs,
    resolve_character_refs,
)

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
    repository = StoryboardImageReferenceRepository(db)

    scenes = repository.list_scenes(script_id)
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
        envs = repository.list_environments(env_ids)
        env_map = {env.id: env for env in envs}
        for sc in scenes:
            if sc.environment_id and sc.environment_id in env_map:
                refs = env_map[sc.environment_id].reference_images or []
                ctx.env_images_by_scene[int(sc.scene_number)] = [
                    _abs_url(u) for u in refs if u
                ]

    # Load character IDs from shots
    if scene_ids:
        shots = repository.list_shots(scene_ids)
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
            get_story_character_virtual_ip_ids,
        )

        episode = repository.get_episode(script.episode_id)
        story_id = int(episode.story_id) if episode and episode.story_id else None
        if story_id:
            all_char_ids.update(get_story_character_virtual_ip_ids(db, story_id))
    except Exception:
        pass

    if all_char_ids:
        _load_character_images(repository, all_char_ids, ctx)
        _build_name_alias_map(ctx)

    return ctx


def _load_character_images(
    repository: StoryboardImageReferenceRepository,
    all_char_ids: set,
    ctx: ImageRefContext,
):
    """Load VirtualIP records and their default/latest images."""
    vips = repository.list_virtual_ips(all_char_ids)
    ctx.vip_map = {v.id: v for v in vips}
    images = repository.list_virtual_ip_images(all_char_ids)
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
    # 1) Frame-level references
    frame_refs = _normalize_reference_images(frame.get("reference_images") or [])

    # 2) User-provided references
    if labeled_references:
        payload_refs = _normalize_reference_images(
            [ref.get("url") for ref in labeled_references if ref.get("url")]
        )
    else:
        payload_refs = _normalize_reference_images(reference_images or [])
    # 3) Character anchor references
    char_anchor_refs, character_notes, selected_character_ids = resolve_character_refs(
        frame,
        scene_no,
        ctx,
        prompt,
    )
    frame_refs = filter_frame_character_refs(
        frame,
        frame_refs,
        selected_character_ids,
        ctx,
    )

    # 4) Environment references
    env_refs = _normalize_reference_images(
        ctx.env_images_by_scene.get(scene_no or -1, []) or []
    )
    # Explicit request references override automatic frame bindings.
    if payload_refs:
        return payload_refs, [{"type": "user"}], char_anchor_refs

    ref_images_raw = [*frame_refs, *char_anchor_refs, *env_refs]
    ref_images = _normalize_reference_images(ref_images_raw)
    reference_notes: List[Dict[str, Any]] = list(character_notes)
    classified = set(char_anchor_refs) | set(env_refs)
    if any(url not in classified for url in frame_refs):
        reference_notes.insert(0, {"type": "frame"})
    if env_refs:
        reference_notes.append({"type": "environment"})
    return ref_images, reference_notes, char_anchor_refs
