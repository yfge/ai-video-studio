from __future__ import annotations

from typing import Dict, List, Optional

from app.core.validators.character_registry import extract_name_aliases
from app.models.script import StoryCharacter
from app.models.virtual_ip import VirtualIP
from sqlalchemy.orm import Session


def extract_virtual_ip_name_aliases(name: str | None) -> List[str]:
    """Backward compatible wrapper for alias extraction."""
    return extract_name_aliases(name)


def get_story_character_virtual_ip_ids(db: Session, story_id: int) -> List[int]:
    """Return ordered virtual_ip_ids registered for a story (deduped)."""
    rows = (
        db.query(StoryCharacter.virtual_ip_id)
        .filter(
            StoryCharacter.story_id == story_id,
            StoryCharacter.is_deleted.is_(False),
        )
        .order_by(StoryCharacter.importance.desc(), StoryCharacter.id.asc())
        .all()
    )

    seen: set[int] = set()
    ordered: List[int] = []
    for (vip_id,) in rows:
        try:
            value = int(vip_id)
        except (TypeError, ValueError):
            continue
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def infer_character_ids_from_text(
    text: str,
    name_to_id: Dict[str, int],
    *,
    max_matches: int | None = None,
) -> List[int]:
    """Infer character IDs by matching known names in text (longest names first)."""
    if not isinstance(text, str) or not text.strip():
        return []

    candidates: list[tuple[str, int]] = []
    for name, cid in (name_to_id or {}).items():
        if not isinstance(name, str):
            continue
        clean = name.strip()
        if not clean:
            continue
        candidates.append((clean, int(cid)))

    # Prefer longer names, and avoid substring overlaps by blanking matched spans.
    candidates.sort(key=lambda item: len(item[0]), reverse=True)

    remaining = text
    matched: list[int] = []
    for name, cid in candidates:
        if name not in remaining:
            continue
        matched.append(cid)
        remaining = remaining.replace(name, " " * len(name))
        if max_matches is not None and len(matched) >= max_matches:
            break

    # Dedup while keeping order.
    deduped: list[int] = []
    seen_ids: set[int] = set()
    for cid in matched:
        if cid in seen_ids:
            continue
        seen_ids.add(cid)
        deduped.append(cid)
    return deduped


def fallback_virtual_ip_anchor_url(vip: Optional[VirtualIP]) -> Optional[str]:
    """Best-effort anchor URL for a character when VirtualIPImage is missing."""
    if not vip:
        return None

    url = getattr(vip, "default_avatar_url", None)
    if isinstance(url, str) and url.strip():
        return url.strip()

    refs = getattr(vip, "style_reference_images", None)
    if isinstance(refs, list):
        for item in refs:
            if isinstance(item, str) and item.strip():
                return item.strip()

    return None
