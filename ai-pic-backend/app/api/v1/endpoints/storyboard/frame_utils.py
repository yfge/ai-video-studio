"""Storyboard frame utility functions.

Provides frame serialization, augmentation, merging, variety enforcement,
and reference image normalization.
"""

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.models.script import Script


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_uuid(value: Any) -> str:
    if not value:
        return str(uuid4())
    try:
        return str(UUID(str(value)))
    except Exception:
        return str(uuid4())


def _ensure_iso_datetime(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return value.isoformat()
    try:
        return datetime.fromisoformat(str(value)).isoformat()
    except Exception:
        return fallback


def _abs_url(url: str) -> str:
    """Thin wrapper delegating to the canonical scripts_legacy implementation."""
    from app.api.v1.endpoints.scripts_legacy import _abs_url as _legacy_abs_url
    return _legacy_abs_url(url)


# ---------------------------------------------------------------------------
# Serialization & loading
# ---------------------------------------------------------------------------

def _serialize_frame(frame: Dict[str, Any]) -> Dict[str, Any]:
    serialized: Dict[str, Any] = {}
    for key, val in frame.items():
        if isinstance(val, UUID):
            serialized[key] = str(val)
        elif isinstance(val, datetime):
            serialized[key] = val.isoformat()
        else:
            serialized[key] = val
    return serialized


def _load_existing_frames(script: Script) -> List[Dict[str, Any]]:
    storyboard = (
        (script.extra_metadata or {}).get("storyboard")
        if script.extra_metadata
        else None
    )
    frames = storyboard.get("frames") if isinstance(storyboard, dict) else None
    if not isinstance(frames, list):
        return []
    return [deepcopy(frame) for frame in frames if isinstance(frame, dict)]


# ---------------------------------------------------------------------------
# Augmentation
# ---------------------------------------------------------------------------

def _augment_frames(
    frames: List[Dict[str, Any]],
    *,
    scene_map: Dict[int, Dict[str, Any]],
    generation_source: str,
    generation_method: str,
    generation_model: Optional[str],
) -> List[Dict[str, Any]]:
    now_iso = _now_iso()
    augmented: List[Dict[str, Any]] = []
    for raw in frames:
        frame = dict(raw or {})
        frame["frame_id"] = _coerce_uuid(frame.get("frame_id"))
        scene_number = _to_int(frame.get("scene_number"))
        if scene_number is None:
            scene_number = _to_int(frame.get("scene_index"))
        if scene_number is not None:
            frame["scene_number"] = scene_number
            if scene_number in scene_map:
                frame.setdefault("scene_index", scene_number)
            elif scene_map:
                closest = min(scene_map.keys(), key=lambda k: abs(k - scene_number))
                frame.setdefault("scene_index", closest)
        else:
            frame_index = frame.get("scene_index")
            if frame_index is None and scene_map:
                first_key = next(iter(scene_map.keys()), None)
                if first_key is not None:
                    frame["scene_number"] = first_key
                    frame["scene_index"] = first_key
            else:
                frame["scene_index"] = frame_index
        frame["generation_source"] = frame.get("generation_source") or generation_source
        frame["generation_method"] = frame.get("generation_method") or generation_method
        if generation_model:
            frame["generation_model"] = frame.get("generation_model") or generation_model
        frame["generated_at"] = _ensure_iso_datetime(frame.get("generated_at"), now_iso)
        frame["updated_at"] = now_iso
        if not isinstance(frame.get("reference_images"), list):
            frame["reference_images"] = []
        augmented.append(frame)
    return augmented


# ---------------------------------------------------------------------------
# Merging
# ---------------------------------------------------------------------------

def _merge_frames(
    existing_frames: List[Dict[str, Any]],
    new_frames: List[Dict[str, Any]],
    selected_scenes: Optional[List[int]],
) -> List[Dict[str, Any]]:
    has_selection = selected_scenes is not None
    selected_set = (
        {s for s in (selected_scenes or []) if s is not None} if has_selection else None
    )
    merged: List[Dict[str, Any]] = []
    if existing_frames and selected_set:
        for frame in existing_frames:
            scene_number = _to_int(frame.get("scene_number"))
            if scene_number in selected_set:
                continue
            merged.append(deepcopy(frame))
    elif not has_selection:
        merged = []
    else:
        merged = [deepcopy(frame) for frame in existing_frames]
    merged.extend(new_frames)
    merged.sort(
        key=lambda fr: (
            _to_int(fr.get("scene_number")) or 0,
            fr.get("frame_number") or 0,
        )
    )
    for idx, frame in enumerate(merged, start=1):
        frame["frame_number"] = idx
        if frame.get("scene_number") is not None and frame.get("scene_index") is None:
            frame["scene_index"] = _to_int(frame.get("scene_number"))
    return merged


# ---------------------------------------------------------------------------
# Variety enforcement
# ---------------------------------------------------------------------------

def _enforce_storyboard_variety(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    shot_cycle = ["远景", "中景", "近景", "特写"]
    movement_cycle = ["固定", "推", "拉", "摇", "移", "跟", "变焦"]
    composition_cycle = ["三分法", "对称", "前后景", "对角线", "中心对称"]
    seen: Dict[tuple, int] = {}
    for frame in frames:
        desc = (frame.get("description") or "").strip()
        scene_no = _to_int(frame.get("scene_number"))
        key = (scene_no, desc)
        count = seen.get(key, -1) + 1
        seen[key] = count
        if count > 0:
            frame["shot_type"] = shot_cycle[(count + (scene_no or 0)) % len(shot_cycle)]
            frame["camera_movement"] = movement_cycle[
                (count + (scene_no or 0)) % len(movement_cycle)
            ]
            frame["composition"] = composition_cycle[
                (count + (scene_no or 0)) % len(composition_cycle)
            ]
            base_desc = desc or f"场景{scene_no or ''}"
            frame["description"] = (
                f"{base_desc}（变体{count + 1}，强调{frame['camera_movement']}）"
            )
            old_prompt = frame.get("ai_prompt")
            if isinstance(old_prompt, str) and old_prompt.strip():
                frame["ai_prompt"] = f"{frame['description']}\n{old_prompt}"
            else:
                frame["ai_prompt"] = frame["description"]
            frame["duration_seconds"] = max(
                2, min(12, (frame.get("duration_seconds") or 3) + ((count % 3) - 1))
            )
    return frames


# ---------------------------------------------------------------------------
# Reference image filtering
# ---------------------------------------------------------------------------

def _normalize_reference_images(refs: list) -> list:
    """Keep only entries that look like image URLs."""
    allowed_ext = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg")
    normalized: list = []
    for raw in refs:
        if not isinstance(raw, str):
            continue
        ref = raw.strip()
        if not ref:
            continue
        lower = ref.lower()
        base_path = lower.split("?", 1)[0]
        if lower.startswith(
            ("http://", "https://", "data:image/")
        ) or base_path.endswith(allowed_ext):
            normalized.append(_abs_url(ref))
    seen: set = set()
    deduped: list = []
    for u in normalized:
        if u and u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped
