"""Compact contracts and deterministic parsing for long-form V5 planning."""

from __future__ import annotations

import copy

from app.services.narrative_consistency import simulate_causal_graph
from app.utils.json_utils import extract_json_block

from .story_novel_v5_plan import freeze_v5_foundation

BATCHED_COMPILE_THRESHOLD = 32
CAUSAL_BATCH_SIZE = 16


def foundation_contract(revision, plan):
    snapshot = revision.story_snapshot or {}
    story_seed = copy.deepcopy(snapshot.get("story_seed") or {})
    outline = dict(story_seed.get("structured_outline") or {})
    outline.pop("chapters", None)
    outline.pop("thread_payoffs", None)
    story_seed["structured_outline"] = outline
    arcs = list(outline.get("progression_arcs") or [])
    if arcs:
        ranges = [
            {
                key: arc.get(key)
                for key in (
                    "arc_id",
                    "title",
                    "start_position",
                    "end_position",
                    "narrative_goal",
                    "ending_state",
                    "major_entries",
                    "world_scope_changes",
                    "threads",
                )
            }
            for arc in arcs
        ]
    else:
        ranges = [
            {
                "start_position": rows[0]["position"],
                "end_position": rows[-1]["position"],
                "opening_goal": rows[0].get("goal"),
                "ending_state": rows[-1].get("end_state"),
            }
            for rows in causal_ranges(plan.get("chapters") or [])
        ]
    return {
        "story_seed": story_seed,
        "story_seed_version": plan.get("story_seed_version"),
        "outline_hash": plan.get("outline_hash"),
        "story": {
            key: snapshot.get(key)
            for key in (
                "title",
                "genre",
                "theme",
                "target_audience",
                "premise",
                "synopsis",
                "main_conflict",
                "resolution",
            )
        },
        "characters": snapshot.get("characters") or [],
        "chapter_count": len(plan.get("chapters") or []),
        "progression_ranges": ranges,
    }


def causal_contract(plan, rows, schema, before, partial, *, is_final):
    prior_ids = [item["id"] for item in partial.get("events") or []]
    planning_schema = copy.deepcopy(schema)
    planning_schema["predicates"] = [
        item
        for item in planning_schema.get("predicates") or []
        if item.get("persistence") == "causal"
    ]
    snapshot = {
        key: copy.deepcopy(before.get(key))
        for key in ("schema", "entities", "facts", "snapshot_hash")
    }
    snapshot["occurred_event_ids_tail"] = list(before.get("occurred_event_ids") or [])[
        -32:
    ]
    return {
        "consistency_schema": planning_schema,
        "snapshot_before_batch": snapshot,
        "prior_event_ids_tail": prior_ids[-32:],
        "chapter_contracts": rows,
        "batch_range": [rows[0]["position"], rows[-1]["position"]],
        "is_final_batch": is_final,
        "full_chapter_count": int(plan.get("chapter_count") or 0),
    }


def parse_foundation(base, revision, text):
    try:
        payload = extract_json_block(str(text))
        if not isinstance(payload, dict):
            raise ValueError("response does not contain one JSON object")
        schema, initial = freeze_v5_foundation(
            base, payload, revision.story_snapshot or {}
        )
        return {
            "consistency_schema": schema,
            "initial_fact_graph": initial,
        }, []
    except (KeyError, TypeError, ValueError) as exc:
        return None, [{"code": "foundation_validation_failed", "message": str(exc)}]


def parse_causal_batch(text, partial, schema, initial, rows):
    try:
        payload = extract_json_block(str(text))
        if not isinstance(payload, dict):
            raise ValueError("response does not contain one JSON object")
        raw = payload.get("causal_event_graph") or payload
        if not isinstance(raw, dict):
            raise ValueError("causal batch must be an object")
        events = list(raw.get("events") or [])
        obligations = list(raw.get("obligations") or [])
        positions = {int(item["position"]) for item in rows}
        if {int(item.get("chapter_position") or 0) for item in events} != positions:
            raise ValueError("causal batch events do not exactly cover its chapters")
        if {
            int(item.get("chapter_position") or 0) for item in obligations
        } != positions:
            raise ValueError(
                "causal batch obligations do not exactly cover its chapters"
            )
        merged = {
            "schema": "story_novel_causal_event_graph.v1",
            "events": [*(partial.get("events") or []), *events],
            "obligations": [
                *(partial.get("obligations") or []),
                *obligations,
            ],
        }
        simulate_causal_graph(schema, initial, merged)
        return merged, []
    except (KeyError, TypeError, ValueError) as exc:
        return None, [{"code": "causal_batch_validation_failed", "message": str(exc)}]


def causal_ranges(chapters):
    return [
        chapters[index : index + CAUSAL_BATCH_SIZE]
        for index in range(0, len(chapters), CAUSAL_BATCH_SIZE)
    ]
