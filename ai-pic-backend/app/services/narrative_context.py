from __future__ import annotations

from typing import Any, Dict, List


def extract_story_characters(story: Dict[str, Any] | None) -> List[Dict[str, Any]]:
    """Return story characters from supported narrative payload shapes."""
    if not isinstance(story, dict):
        return []

    for key in ("characters", "character_profiles", "main_characters"):
        raw_items = story.get(key)
        if not isinstance(raw_items, list) or not raw_items:
            continue

        characters: list[dict[str, Any]] = []
        seen: set[str] = set()
        for raw in raw_items:
            character: dict[str, Any] | None = None
            if isinstance(raw, dict):
                character = dict(raw)
                name = character.get("name") or character.get("character_name")
                if name and not character.get("name"):
                    character["name"] = name
            elif isinstance(raw, str) and raw.strip():
                character = {"name": raw.strip()}

            if not character:
                continue
            name = str(character.get("name") or "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            characters.append(character)

        if characters:
            return characters

    return []
