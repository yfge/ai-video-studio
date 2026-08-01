"""Build and validate one immutable chapter-planner input snapshot."""

from __future__ import annotations

import copy

from .story_novel_context_utils import json_text, value_hash
from .story_novel_incremental_plan import chapter_skeleton
from .story_novel_planner_slot_visibility import (
    authorized_entity_slots,
    visible_arc_context,
)
from .story_novel_snapshot_handles import localize_ids, visible_snapshot_entities
from .story_novel_v3_context import build_v3_planning_context
from .story_novel_v4_snapshot_guard import source_manifest_current

SCHEMA = "story_novel_planner_snapshot.v1"
MAX_INPUT_CHARS = 48_000


def build_planner_snapshot(service, revision, position: int, skeleton: dict) -> dict:
    """Query once, normalize once, and freeze both model and execution inputs."""
    context = build_v3_planning_context(
        service, revision, position, skeleton, persist_memory_snapshots=True
    )
    plan = dict(revision.generation_plan or {})
    bindings = _bindings(context, skeleton)
    model_input = _model_input(revision, position, skeleton, context, bindings)
    if len(json_text(model_input)) > MAX_INPUT_CHARS:
        raise ValueError(f"第 {position} 章规划快照超过 48K 输入预算")
    snapshot = {
        "schema": SCHEMA,
        "position": position,
        "generation_plan_hash": plan.get("plan_hash"),
        "canon_hash": plan.get("canon_hash"),
        "chapter_contract_hash": value_hash(chapter_skeleton(skeleton)),
        "state_before_hash": context["evidence"]["state_before_hash"],
        "source_manifest": _source_manifest(
            context["evidence"], context.get("candidate_universe")
        ),
        "handle_bindings": bindings,
        "model_input": model_input,
        "model_input_hash": value_hash(model_input),
        "execution_context": copy.deepcopy(context),
        "audit_context": {
            "canon": copy.deepcopy(plan.get("canon") or {}),
            "future_guard_index": copy.deepcopy(plan.get("future_guard_index") or {}),
        },
        "truncations": copy.deepcopy(context["evidence"].get("truncations") or []),
    }
    snapshot["snapshot_hash"] = value_hash(snapshot)
    return snapshot


def valid_planner_snapshot(snapshot: dict) -> bool:
    if not isinstance(snapshot, dict) or snapshot.get("schema") != SCHEMA:
        return False
    stored = snapshot.get("snapshot_hash")
    value = copy.deepcopy(snapshot)
    value.pop("snapshot_hash", None)
    return bool(
        stored
        and stored == value_hash(value)
        and snapshot.get("model_input_hash") == value_hash(snapshot.get("model_input"))
        and snapshot.get("state_before_hash")
        == (snapshot.get("execution_context") or {})
        .get("evidence", {})
        .get("state_before_hash")
    )


def planner_snapshot_sources_current(service, revision, snapshot: dict) -> bool:
    """Compare source fingerprints without rebuilding or reprioritizing context."""
    if not valid_planner_snapshot(snapshot):
        return False
    return source_manifest_current(
        service,
        revision,
        int(snapshot["position"]),
        snapshot.get("source_manifest") or {},
    )


def _bindings(context: dict, skeleton: dict) -> dict:
    hard = context["hard_constraints"]
    entities = visible_snapshot_entities(context, hard)
    result = {"events": {}, "entities": {}, "world_events": {}, "memories": {}}
    for index, event_id in enumerate(skeleton.get("required_event_ids") or [], 1):
        result["events"][f"E{index:02d}"] = event_id
    counts: dict[str, int] = {}
    for item in entities:
        kind = str(item.get("kind") or "entity")
        counts[kind] = counts.get(kind, 0) + 1
        prefix = {"character": "C", "location": "S"}.get(kind, "X")
        result["entities"][f"{prefix}{counts[kind]:02d}"] = item["id"]
    evidence = context["brief_input"]["planning_evidence"]
    for key, prefix, target in (
        ("world_events", "WE", "world_events"),
        ("character_memories", "M", "memories"),
    ):
        for index, item in enumerate(evidence.get(key) or [], 1):
            result[target][f"{prefix}{index:02d}"] = item["evidence_id"]
    return result


def _model_input(revision, position, skeleton, context, bindings) -> dict:
    hard = context["hard_constraints"]
    entities = {item["id"]: item for item in visible_snapshot_entities(context, hard)}
    reverse_entities = {value: key for key, value in bindings["entities"].items()}
    evidence = context["brief_input"]["planning_evidence"]
    return {
        "schema": "story_novel_chapter_planner_input.v1",
        "position": position,
        "current_chapter": _semantic_skeleton(skeleton, bindings),
        "current_arc": visible_arc_context(
            revision.generation_plan or {}, position, reverse_entities
        ),
        "authorized_entity_slots": authorized_entity_slots(
            revision.generation_plan or {},
            position,
            reverse_entities,
            entities.values(),
        ),
        "scope_taxonomy": copy.deepcopy(
            ((revision.generation_plan or {}).get("scope_graph") or {}).get("taxonomy")
            or []
        ),
        "story_invariants": copy.deepcopy(hard.get("story_invariants") or {}),
        "visible_characters_and_world": [
            _visible_entity(
                handle, entities[entity_id], context, entity_id, reverse_entities
            )
            for handle, entity_id in bindings["entities"].items()
        ],
        "planning_evidence": [
            _safe_evidence(item, handle)
            for key, target in (
                ("world_events", "world_events"),
                ("character_memories", "memories"),
            )
            for handle, source_id in bindings[target].items()
            for item in evidence.get(key) or []
            if item.get("evidence_id") == source_id
        ],
        "recent_chapters": copy.deepcopy(
            context["brief_input"].get("recent_chapters") or []
        )[-4:],
        "previous_chapter_tail": context["brief_input"].get("previous_chapter_tail")
        or "",
        "allowed_entity_handles": sorted(reverse_entities.values()),
        "expected_beat_count": context["brief_input"]["expected_beat_count"],
    }


def _semantic_skeleton(skeleton: dict, bindings: dict) -> dict:
    events = list(skeleton.get("key_events") or [])
    event_handles = list(bindings["events"])
    return {
        key: copy.deepcopy(skeleton.get(key))
        for key in (
            "position",
            "title",
            "goal",
            "character_focus",
            "open_threads",
            "end_state",
            "min_chars",
            "target_chars",
            "max_chars",
        )
    } | {
        "events": [
            {"event_handle": handle, "description": text}
            for handle, text in zip(event_handles, events, strict=True)
        ]
    }


def _visible_entity(handle, entity, context, entity_id, reverse_entities) -> dict:
    state = (context.get("state_before") or {}).get("subjects", {}).get(entity_id, {})
    return {
        "entity_handle": handle,
        "kind": entity.get("kind"),
        "name": entity.get("name"),
        "aliases": copy.deepcopy(entity.get("aliases") or []),
        "attributes": localize_ids(entity.get("attributes") or {}, reverse_entities),
        "current_state": localize_ids(state, reverse_entities),
    }


def _safe_evidence(item: dict, handle: str) -> dict:
    allowed = (
        "event_type",
        "title",
        "summary",
        "description",
        "content",
        "memory_type",
        "importance",
        "emotional_valence",
        "source_chapter_position",
    )
    return {
        "evidence_handle": handle,
        **{
            key: copy.deepcopy(item.get(key))
            for key in allowed
            if item.get(key) is not None
        },
    }


def _source_manifest(evidence: dict, candidate_universe=None) -> dict:
    return {
        "chapter_ids": copy.deepcopy(evidence.get("chapter_ids") or []),
        "chapter_hashes": copy.deepcopy(evidence.get("chapter_hashes") or []),
        "event_ids": copy.deepcopy(evidence.get("event_ids") or []),
        "event_hashes": copy.deepcopy(evidence.get("event_hashes") or []),
        "memory_ids": copy.deepcopy(evidence.get("memory_ids") or []),
        "memory_hashes": copy.deepcopy(evidence.get("memory_hashes") or []),
        "candidate_universe": copy.deepcopy(candidate_universe or {}),
    }
