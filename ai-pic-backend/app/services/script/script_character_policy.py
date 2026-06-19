from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence

from app.core.validators.character_registry import (
    build_alias_to_canonical_map,
    extract_name_aliases,
    normalize_character_name_token,
    normalize_to_registered_or_generic,
    preferred_display_name,
)
from app.models.script import Story, StoryCharacter

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@dataclass(frozen=True, slots=True)
class ScriptCharacterPolicyResult:
    """Result for script character policy enforcement."""

    unknown_names: List[str]
    canonical_names: List[str]
    normalized_count: int


def _iter_story_registry(story: Story) -> Iterable[tuple[str, Iterable[str]]]:
    """Yield (canonical_name, aliases) for StoryCharacter registry entries."""
    story_characters = getattr(story, "story_characters", None) or []
    for sc in story_characters:
        if not isinstance(sc, StoryCharacter):
            continue
        if getattr(sc, "is_deleted", False):
            continue

        vip = getattr(sc, "virtual_ip", None)
        vip_name = getattr(vip, "name", None) if vip else None
        canonical = getattr(sc, "character_name", None)
        if not canonical:
            canonical = preferred_display_name(vip_name) or vip_name
        canonical = normalize_character_name_token(canonical)
        if not canonical:
            continue

        aliases: list[str] = []
        aliases.extend(extract_name_aliases(canonical))
        if vip_name and vip_name != canonical:
            aliases.extend(extract_name_aliases(vip_name))
        yield canonical, aliases

    for character in getattr(story, "main_characters", None) or []:
        if isinstance(character, dict):
            name = character.get("name") or character.get("character_name")
            raw_aliases = character.get("aliases")
            aliases = raw_aliases if isinstance(raw_aliases, list) else []
        else:
            name = character
            aliases = []
        canonical = normalize_character_name_token(str(name or ""))
        if not canonical:
            continue
        yield canonical, [*extract_name_aliases(canonical), *aliases]


def build_story_alias_map(story: Story) -> dict[str, str]:
    """Build alias -> canonical mapping from StoryCharacter registry."""
    canonical_names: list[str] = []
    extra_aliases: dict[str, list[str]] = {}
    for canonical, aliases in _iter_story_registry(story):
        canonical_names.append(canonical)
        extra_aliases[canonical] = list(aliases)
    return build_alias_to_canonical_map(
        canonical_names=canonical_names, extra_aliases=extra_aliases
    )


def build_episode_alias_map(
    episode_id: int,
    db: "Session",
) -> dict[str, str]:
    """Build alias -> canonical mapping from EpisodeCharacter registry.

    Args:
        episode_id: Episode ID to fetch characters for
        db: Database session

    Returns:
        Dictionary mapping normalized aliases to canonical character names
    """
    from app.repositories.script_lookup_repository import fetch_episode_character_sources

    canonical_names: list[str] = []
    extra_aliases: dict[str, list[str]] = {}

    for ec, vip in fetch_episode_character_sources(db, episode_id):
        # Get display name
        vip_name = getattr(vip, "name", None) if vip else None
        canonical = getattr(ec, "character_name", None)

        if not canonical:
            canonical = preferred_display_name(vip_name) or vip_name

        canonical = normalize_character_name_token(canonical)
        if not canonical:
            continue

        # Build aliases
        aliases: list[str] = []
        aliases.extend(extract_name_aliases(canonical))
        if vip_name and vip_name != canonical:
            aliases.extend(extract_name_aliases(vip_name))

        canonical_names.append(canonical)
        extra_aliases[canonical] = aliases

    return build_alias_to_canonical_map(
        canonical_names=canonical_names, extra_aliases=extra_aliases
    )


def build_combined_alias_map(
    story: Story,
    episode_id: Optional[int] = None,
    db: Optional["Session"] = None,
) -> dict[str, str]:
    """Build combined alias map from Story and Episode characters.

    Episode characters take priority over Story characters when there's a conflict.

    Args:
        story: Story object with character registry
        episode_id: Optional episode ID to include Episode characters
        db: Optional database session (required if episode_id is provided)

    Returns:
        Dictionary mapping normalized aliases to canonical character names
    """
    # Start with Story characters
    alias_map = build_story_alias_map(story)

    # Add Episode characters (overriding Story if conflicts exist)
    if episode_id and db:
        episode_map = build_episode_alias_map(episode_id, db)
        alias_map.update(episode_map)

    return alias_map


def enforce_script_character_policy(
    *,
    story: Story,
    scenes: Sequence[Dict[str, Any]],
    dialogues: Sequence[Dict[str, Any]],
    episode_id: Optional[int] = None,
    db: Optional["Session"] = None,
) -> ScriptCharacterPolicyResult:
    """Normalize script character fields and detect unknown named characters.

    Policy:
      - Only Story-registered and Episode-registered characters may appear.
      - Episode characters take priority over Story characters when names conflict.
      - Allow generic functional roles, such as 路人/店员/客户/团队成员.
      - Missing dialogue speaker is treated as 旁白.

    Args:
        story: Story object with character registry
        scenes: Script scenes to validate
        dialogues: Script dialogues to validate
        episode_id: Optional episode ID to include Episode characters
        db: Optional database session (required if episode_id is provided)

    Returns:
        ScriptCharacterPolicyResult with validation results
    """
    alias_to_canonical = build_combined_alias_map(story, episode_id, db)
    # Backward-compatible: if a story has no registry, do not block generation.
    if not alias_to_canonical:
        for dlg in dialogues:
            if not isinstance(dlg, dict):
                continue
            dlg.setdefault("character", "旁白")
        return ScriptCharacterPolicyResult(
            unknown_names=[],
            canonical_names=[],
            normalized_count=0,
        )

    unknown: set[str] = set()
    normalized_count = 0

    def _dedupe(seq: Iterable[str]) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for item in seq:
            if item in seen:
                continue
            seen.add(item)
            out.append(item)
        return out

    # Scenes.characters
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        chars = scene.get("characters")
        if not isinstance(chars, list):
            continue
        updated: list[str] = []
        for raw in chars:
            token = str(raw) if raw is not None else ""
            normalized = normalize_to_registered_or_generic(
                token, alias_to_canonical=alias_to_canonical
            )
            if normalized is None:
                unknown.add(normalize_character_name_token(token) or token)
                updated.append(normalize_character_name_token(token) or token)
                continue
            if normalize_character_name_token(token) != normalized:
                normalized_count += 1
            updated.append(normalized)
        scene["characters"] = _dedupe([c for c in updated if c])

    # Dialogues.character
    for dlg in dialogues:
        if not isinstance(dlg, dict):
            continue
        who = dlg.get("character") or dlg.get("speaker") or dlg.get("name")
        normalized = normalize_to_registered_or_generic(
            str(who) if who is not None else None,
            alias_to_canonical=alias_to_canonical,
        )
        if normalized is None:
            unknown.add(normalize_character_name_token(str(who)) or str(who))
            continue
        if who is None:
            normalized_count += 1
        elif normalize_character_name_token(str(who)) != normalized:
            normalized_count += 1
        dlg["character"] = normalized

    canonical_names = sorted(set(alias_to_canonical.values()))

    return ScriptCharacterPolicyResult(
        unknown_names=sorted([n for n in unknown if n]),
        canonical_names=canonical_names,
        normalized_count=normalized_count,
    )
