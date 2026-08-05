"""Conservative Canon-entity mention matching for frozen chapter text."""

from __future__ import annotations

import json


def visible_entity_ids(canon: dict, chapter: dict, outline_keys) -> list[str]:
    surface = json.dumps(
        {key: chapter.get(key) for key in outline_keys},
        ensure_ascii=False,
        default=str,
    )
    return [
        str(item["id"])
        for item in canon.get("entities") or []
        if any(
            _name_is_visible(str(name or "").strip(), surface)
            for name in [item.get("name"), *(item.get("aliases") or [])]
        )
    ]


def _name_is_visible(name: str, surface: str) -> bool:
    if not name:
        return False
    if name in surface:
        return True
    # A planned entity may be named with a one-character noun variant in the
    # outline (for example, the same four-character label ending differently).
    # Requiring a three-character leading stem avoids broad suffix matches such
    # as two unrelated markets while keeping the rule genre-neutral.
    stem = name[:-1]
    return len(stem) >= 3 and stem in surface
