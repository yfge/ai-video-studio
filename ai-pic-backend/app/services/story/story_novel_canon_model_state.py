"""Deterministically compile model-only Canon state references."""

from __future__ import annotations

import copy

from .story_novel_location_hierarchy import persistent_location_id
from .story_novel_location_rules import ABSENT_OBJECT_STATUS_LITERALS

_MODEL_ABSENT_OBJECT_STATUSES = {
    *ABSENT_OBJECT_STATUS_LITERALS,
    "not-built",
    "not-issued",
}


def normalize_model_initial_state(payload: dict) -> tuple[dict, list[dict]]:
    """Compile common provider representations without weakening raw validation."""
    normalized = copy.deepcopy(payload)
    diagnostics: list[dict] = []
    for entity in normalized.get("entities") or []:
        attributes = entity.get("attributes") or {}
        if (
            entity.get("kind") == "location"
            and attributes.get("location_scope") == "scene"
            and not attributes.get("parent_location_id")
        ):
            attributes.pop("location_scope", None)
            attributes.pop("parent_location_id", None)
            entity["attributes"] = attributes
            diagnostics.append(
                {
                    "id": entity.get("id"),
                    "section": "entities",
                    "reason": "orphan_scene_promoted_to_persistent",
                }
            )
    entities = {
        item.get("id"): item
        for item in normalized.get("entities") or []
        if item.get("id")
    }
    for subject_id, state in (normalized.get("initial_state") or {}).items():
        if not isinstance(state, dict):
            continue
        kind = (entities.get(subject_id) or {}).get("kind")
        status = state.get("status")
        if kind == "object" and status in _MODEL_ABSENT_OBJECT_STATUSES:
            changed = status != "absent" or state.get("location") is not None
            changed = changed or state.get("owner_id") is not None
            state["status"] = "absent"
            state["location"] = None
            state["owner_id"] = None
            if changed:
                diagnostics.append(
                    {
                        "id": subject_id,
                        "section": "initial_state",
                        "reason": "absent_object_state_normalized",
                    }
                )
            continue
        location_id = state.get("location")
        owner_id = state.get("owner_id")
        owner_kind = (entities.get(owner_id) or {}).get("kind")
        if (
            kind == "object"
            and location_id == owner_id
            and owner_kind
            in {
                "character",
                "organization",
            }
        ):
            state["location"] = None
            diagnostics.append(
                {
                    "id": subject_id,
                    "section": "initial_state",
                    "reason": "owner_reference_removed_from_location",
                    "owner_id": owner_id,
                }
            )
            continue
        target = entities.get(location_id) or {}
        if target.get("kind") != "location":
            continue
        durable_id = persistent_location_id(normalized, location_id)
        if durable_id != location_id:
            state["location"] = durable_id
            diagnostics.append(
                {
                    "id": subject_id,
                    "section": "initial_state",
                    "reason": "scene_location_mapped_to_persistent_parent",
                    "source_location_id": location_id,
                    "location_id": durable_id,
                }
            )
    return normalized, diagnostics
