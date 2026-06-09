from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.validators.character_registry import (
    build_alias_to_canonical_map,
    extract_name_aliases,
    normalize_character_name_token,
    preferred_display_name,
)
from app.models.episode_character import EpisodeCharacter
from app.models.script import StoryCharacter
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.repositories.story_character_visual_repository import (
    StoryCharacterVisualRepository,
)
from app.services.script.script_character_policy import build_story_alias_map
from app.services.storyboard.storyboard_character_anchors import (
    fallback_virtual_ip_anchor_url,
)
from sqlalchemy.orm import Session

from .storyboard_audio_context_utils import compact, truncate


def _select_virtual_ip_anchor_url(vip: Optional[VirtualIP]) -> Optional[str]:
    """Pick the best public URL to represent a character identity anchor."""
    if not vip:
        return None

    images = getattr(vip, "images", None)
    if isinstance(images, list) and images:
        candidates: list[VirtualIPImage] = []
        for img in images:
            if not isinstance(img, VirtualIPImage):
                continue
            if getattr(img, "is_deleted", False):
                continue
            url = getattr(img, "oss_url", None)
            if not isinstance(url, str) or not url.strip():
                continue
            candidates.append(img)

        if candidates:
            # Prefer default avatar, then avatar category, then newest.
            def _score(img: VirtualIPImage) -> tuple[int, int, int]:
                is_default = 1 if getattr(img, "is_default", False) else 0
                category = (getattr(img, "category", None) or "").strip().lower()
                is_avatar = 1 if category == "avatar" else 0
                created_at = getattr(img, "created_at", None)
                ts = (
                    int(getattr(created_at, "timestamp", lambda: 0)())
                    if created_at
                    else 0
                )
                return (is_default, is_avatar, ts)

            best = sorted(candidates, key=_score, reverse=True)[0]
            return str(getattr(best, "oss_url")).strip()

    return fallback_virtual_ip_anchor_url(vip)


def _build_character_card_brief(canonical_name: str, vip: VirtualIP) -> str:
    """Short visual anchor string (appearance/clothing) for prompts."""
    desc = str(getattr(vip, "description", "") or "").strip()
    style = str(getattr(vip, "style_prompt", "") or "").strip()

    def _first_clause(text: str, limit: int) -> str:
        t = compact(text)
        for sep in ("。", "；", ";", "\n"):
            if sep in t:
                t = t.split(sep, 1)[0].strip()
        return truncate(t, limit)

    parts = [p for p in (_first_clause(desc, 90), _first_clause(style, 90)) if p]
    if parts:
        return f"{canonical_name}: {'；'.join(parts)}"
    return f"{canonical_name}: 外观与服饰保持一致"


@dataclass(frozen=True, slots=True)
class StoryCharacterVisual:
    canonical_name: str
    virtual_ip_id: int
    card_brief: str
    anchor_url: Optional[str]
    importance: int


def load_story_character_visuals(
    db: Session,
    *,
    story_id: int,
) -> tuple[dict[str, StoryCharacterVisual], dict[str, str]]:
    """Return (canonical_name -> visual), plus alias_to_canonical mapping."""
    story = StoryCharacterVisualRepository(db).get_story_with_character_images(story_id)
    if not story:
        return {}, {}

    alias_to_canonical = build_story_alias_map(story)
    if not alias_to_canonical:
        return {}, {}

    visuals: dict[str, StoryCharacterVisual] = {}
    for sc in getattr(story, "story_characters", []) or []:
        if not isinstance(sc, StoryCharacter):
            continue
        if getattr(sc, "is_deleted", False):
            continue
        vip = getattr(sc, "virtual_ip", None)
        if not isinstance(vip, VirtualIP) or getattr(vip, "is_deleted", False):
            continue

        token = normalize_character_name_token(
            str(getattr(sc, "character_name", None) or getattr(vip, "name", "") or "")
        )
        canonical = alias_to_canonical.get(token)
        if not canonical:
            continue

        visuals[canonical] = StoryCharacterVisual(
            canonical_name=canonical,
            virtual_ip_id=int(getattr(vip, "id")),
            card_brief=_build_character_card_brief(canonical, vip),
            anchor_url=_select_virtual_ip_anchor_url(vip),
            importance=int(getattr(sc, "importance", 1) or 1),
        )

    return visuals, alias_to_canonical


def load_episode_character_visuals(
    db: Session,
    *,
    episode_id: int,
) -> tuple[dict[str, StoryCharacterVisual], dict[str, str]]:
    """Return episode temporary character visuals keyed by canonical display name."""
    rows = StoryCharacterVisualRepository(db).list_episode_characters_with_images(
        episode_id
    )
    canonical_names: list[str] = []
    extra_aliases: dict[str, list[str]] = {}
    visuals: dict[str, StoryCharacterVisual] = {}

    for row in rows:
        if not isinstance(row, EpisodeCharacter):
            continue
        vip = getattr(row, "virtual_ip", None)
        if not isinstance(vip, VirtualIP) or getattr(vip, "is_deleted", False):
            continue
        canonical = normalize_character_name_token(
            str(
                getattr(row, "character_name", None)
                or preferred_display_name(getattr(vip, "name", None))
                or getattr(vip, "name", "")
                or ""
            )
        )
        if not canonical:
            continue
        canonical_names.append(canonical)
        extra_aliases[canonical] = [
            *extract_name_aliases(canonical),
            *extract_name_aliases(getattr(vip, "name", None)),
        ]
        visuals[canonical] = StoryCharacterVisual(
            canonical_name=canonical,
            virtual_ip_id=int(getattr(vip, "id")),
            card_brief=_build_episode_character_card_brief(canonical, row, vip),
            anchor_url=_select_virtual_ip_anchor_url(vip),
            importance=int(getattr(row, "importance", 1) or 1),
        )

    alias_to_canonical = build_alias_to_canonical_map(
        canonical_names=canonical_names,
        extra_aliases=extra_aliases,
    )
    return visuals, alias_to_canonical


def _build_episode_character_card_brief(
    canonical_name: str,
    row: EpisodeCharacter,
    vip: VirtualIP,
) -> str:
    brief = _build_character_card_brief(canonical_name, vip)
    override = str(getattr(row, "appearance_override", "") or "").strip()
    if override:
        return f"{brief}；{truncate(compact(override), 90)}"
    return brief
