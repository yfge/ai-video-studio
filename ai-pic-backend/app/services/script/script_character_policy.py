from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence

from app.core.validators.character_registry import (
    build_alias_to_canonical_map,
    extract_name_aliases,
    normalize_character_name_token,
    normalize_to_registered_or_generic,
    preferred_display_name,
)
from app.models.script import Story, StoryCharacter


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


def enforce_script_character_policy(
    *,
    story: Story,
    scenes: Sequence[Dict[str, Any]],
    dialogues: Sequence[Dict[str, Any]],
) -> ScriptCharacterPolicyResult:
    """Normalize script character fields and detect unknown named characters.

    Policy:
      - Only Story-registered characters may appear (after alias normalization).
      - Allow generic roles: 路人/店员/旁白 (with optional suffix like 路人甲).
      - Missing dialogue speaker is treated as 旁白.
    """
    alias_to_canonical = build_story_alias_map(story)
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
