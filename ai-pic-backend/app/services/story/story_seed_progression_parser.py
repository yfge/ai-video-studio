"""Parse model progression plans through call-local character handles."""

from __future__ import annotations

import copy
from typing import Any

from app.schemas.story_seed import StorySeedProgressionPlan
from app.utils.json_utils import extract_json_block

from .story_seed_structure_policy import structure_ranges


def localize_story_seed(seed: dict) -> tuple[dict, dict[str, str]]:
    """Replace persistent protagonist IDs with short call-local handles."""
    localized = copy.deepcopy(seed)
    handle_to_source: dict[str, str] = {}
    for index, protagonist in enumerate(localized.get("protagonists") or [], 1):
        source_id = str(protagonist.get("virtual_ip_business_id") or "").strip()
        if not source_id:
            continue
        handle = f"SC{index:03d}"
        handle_to_source[handle] = source_id
        protagonist["virtual_ip_business_id"] = handle
    return localized, handle_to_source


def localize_progression(plan: dict, handle_to_source: dict[str, str]) -> dict:
    """Return a prompt-safe plan using the same call-local handles."""
    source_to_handle = {value: key for key, value in handle_to_source.items()}
    return _replace_exact(copy.deepcopy(plan), source_to_handle)


def parse_progression(text, expected_positions, handle_to_source=None):
    try:
        payload = extract_json_block(text) or {}
        raw = payload.get("progression_plan") or payload
        if handle_to_source:
            raw = _restore_model_handles(raw, handle_to_source)
        plan = StorySeedProgressionPlan.model_validate(raw)
        expected = [
            (f"arc-{index:03d}", rows[0], rows[-1])
            for index, rows in enumerate(structure_ranges(expected_positions), 1)
        ]
        actual = [
            (item.arc_id, item.start_position, item.end_position)
            for item in plan.progression_arcs
        ]
        if (
            plan.requested_chapter_count != len(expected_positions)
            or actual != expected
        ):
            raise ValueError(f"分卷覆盖不匹配: expected={expected}, actual={actual}")
        return plan, None
    except (KeyError, TypeError, ValueError) as exc:
        return None, str(exc)


def _restore_model_handles(raw: Any, handle_to_source: dict[str, str]) -> Any:
    value = copy.deepcopy(raw)
    if not isinstance(value, dict):
        return value
    for route in value.get("core_character_routes") or []:
        if not isinstance(route, dict):
            continue
        targets = route.get("relationship_targets")
        if isinstance(targets, list):
            route["relationship_targets"] = [
                _canonical_handle(item, handle_to_source) for item in targets
            ]
    return _replace_exact(value, handle_to_source)


def _canonical_handle(value: Any, handle_to_source: dict[str, str]) -> Any:
    if isinstance(value, dict):
        value = value.get("character_ref")
    if not isinstance(value, str):
        return value
    matches = [handle for handle in handle_to_source if value.startswith(handle)]
    if len(matches) == 1:
        return matches[0]
    return value


def _replace_exact(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        return replacements.get(value, value)
    if isinstance(value, list):
        return [_replace_exact(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_exact(item, replacements) for key, item in value.items()}
    return value
