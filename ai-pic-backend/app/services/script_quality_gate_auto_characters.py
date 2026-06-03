from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


async def auto_create_temporary_characters_for_gate(
    *,
    gate: Dict[str, Any],
    content: Dict[str, Any],
    story_model: Any,
    episode_id: Optional[int],
    db: Any,
) -> list[Dict[str, Any]]:
    if not story_model or not episode_id or not db:
        return []

    unknown_names = _unknown_character_policy_names(gate)
    if not unknown_names:
        return []

    candidate_names = _temporary_character_candidate_names(content, unknown_names)
    if not candidate_names:
        return []

    user_id = getattr(story_model, "user_id", None)
    if not user_id:
        from app.repositories.script_lookup_repository import (
            fetch_episode_story_user_id,
        )

        user_id = fetch_episode_story_user_id(db, episode_id)
    if not user_id:
        logger.warning(
            "Could not auto-create temporary script characters without story user",
            extra={"episode_id": episode_id, "unknown_names": unknown_names},
        )
        return []

    from app.services.script.auto_character_creator import (
        auto_create_episode_characters,
    )

    return await auto_create_episode_characters(
        db=db,
        episode_id=episode_id,
        script_content=content,
        unknown_names=candidate_names,
        user_id=int(user_id),
        ai_service=None,
    )


def with_auto_created_characters(
    result: Dict[str, Any],
    auto_created_characters: list[Dict[str, Any]],
) -> Dict[str, Any]:
    updated = dict(result)
    existing = updated.get("auto_created_characters")
    if isinstance(existing, list):
        merged = [*existing]
        seen = {
            item.get("character_name")
            for item in merged
            if isinstance(item, dict) and item.get("character_name")
        }
    else:
        merged = []
        seen = set()
    for item in auto_created_characters:
        name = item.get("character_name") if isinstance(item, dict) else None
        if name and name in seen:
            continue
        if name:
            seen.add(name)
        merged.append(item)
    updated["auto_created_characters"] = merged
    return updated


def _unknown_character_policy_names(gate: Dict[str, Any]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for issue in gate.get("blocking_issues") or []:
        if not isinstance(issue, dict):
            continue
        if issue.get("id") != "script_character_policy":
            continue
        details = issue.get("details")
        if not isinstance(details, dict):
            continue
        for raw in details.get("unknown_names") or []:
            name = str(raw).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            names.append(name)
    return names


def _temporary_character_candidate_names(
    content: Dict[str, Any],
    unknown_names: list[str],
) -> list[str]:
    from app.services.script.temporary_character_extractor import (
        extract_temporary_characters,
    )

    extracted = extract_temporary_characters(
        script_content=content,
        unknown_names=unknown_names,
    )
    names: list[str] = []
    seen: set[str] = set()
    for character in extracted:
        if character.dialogue_count <= 0:
            continue
        name = character.character_name.strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names
