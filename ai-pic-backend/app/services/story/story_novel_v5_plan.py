"""Freeze and verify a topic-neutral Story Novel v5 generation plan."""

from __future__ import annotations

import copy

from app.services.narrative_consistency import (
    freeze_fact_graph,
    freeze_schema,
    simulate_causal_graph,
)

from .story_novel_context_utils import value_hash
from .story_novel_plan_hash import generation_plan_hash
from .story_novel_plan_versions import V5_SCHEMA
from .story_novel_v5_prompts import V5_TEMPLATES, prompt_policy


def freeze_v5_plan(
    base: dict, payload: dict, snapshot: dict, attempts: list[dict]
) -> dict:
    schema, initial = freeze_v5_foundation(base, payload, snapshot)
    causal = copy.deepcopy(_required(payload, "causal_event_graph"))
    _require_chapter_coverage(base, causal)
    simulation = simulate_causal_graph(schema, initial, causal)
    causal_hash = simulation["causal_graph_hash"]
    causal["graph_hash"] = causal_hash
    chapters = _chapter_contracts(base["chapters"], causal)
    result = {
        **base,
        "status": "ready",
        "phase": "ready",
        "chapters": chapters,
        "consistency_schema": schema,
        "consistency_schema_hash": schema["schema_hash"],
        "initial_fact_graph": initial,
        "initial_snapshot_hash": initial["snapshot_hash"],
        "causal_event_graph": causal,
        "causal_graph_hash": causal_hash,
        "schema_compile_status": "frozen",
        "schema_compile_diagnostics": [],
        "schema_compile_attempts": attempts,
        "simulation": {
            "status": "passed",
            "snapshots": simulation["snapshots"],
            "final_snapshot_hash": simulation["final_graph"]["snapshot_hash"],
        },
        "canon_view": canon_view(schema, initial),
    }
    result.setdefault("prompt_templates", prompt_policy())
    for key in (
        "schema_compile_candidate",
        "causal_compile_next_batch",
        "causal_compile_completed_ranges",
        "causal_compile_partial_graph",
    ):
        result.pop(key, None)
    result["plan_hash"] = generation_plan_hash(result)
    return result


def freeze_v5_foundation(
    base: dict, payload: dict, snapshot: dict
) -> tuple[dict, dict]:
    raw_schema = copy.deepcopy(_required(payload, "consistency_schema"))
    raw_schema["source_manifest"] = _source_manifest(base, snapshot)
    schema = freeze_schema(raw_schema)
    graph_value = _bind_initial_evidence(
        copy.deepcopy(_required(payload, "initial_fact_graph")), base, snapshot
    )
    initial = freeze_fact_graph(schema, graph_value)
    return schema, initial


def valid_v5_plan(plan: dict, snapshot: dict | None = None) -> bool:
    if plan.get("schema") != V5_SCHEMA or plan.get("schema_compile_status") != "frozen":
        return False
    try:
        schema = freeze_schema(plan["consistency_schema"])
        initial = freeze_fact_graph(schema, plan["initial_fact_graph"])
        _require_chapter_coverage(plan, plan["causal_event_graph"])
        simulated = simulate_causal_graph(schema, initial, plan["causal_event_graph"])
    except (KeyError, TypeError, ValueError):
        return False
    return bool(
        schema["schema_hash"] == plan.get("consistency_schema_hash")
        and initial["snapshot_hash"] == plan.get("initial_snapshot_hash")
        and simulated["causal_graph_hash"] == plan.get("causal_graph_hash")
        and _valid_source_manifest(plan, schema, snapshot)
        and _valid_prompt_policy(plan.get("prompt_templates") or {})
        and plan.get("plan_hash") == generation_plan_hash(plan)
    )


def canon_view(schema: dict, graph: dict) -> dict:
    types = {item["id"]: item["label"] for item in schema["entity_types"]}
    predicates = {item["id"]: item["label"] for item in schema["predicates"]}
    return {
        "counts": {
            "entity_types": len(types),
            "predicates": len(predicates),
            "event_types": len(schema["event_types"]),
            "constraints": len(schema["constraints"]),
            "perspectives": len(schema["perspectives"]),
        },
        "entities": [
            {**item, "type_label": types[item["type_id"]]} for item in graph["entities"]
        ],
        "facts": [
            {
                "subject_id": item["subject_id"],
                "predicate_id": item["predicate_id"],
                "predicate_label": predicates[item["predicate_id"]],
                "value": item["value"],
                "scope": item["scope"],
                "perspective_state": item.get("perspective_state"),
            }
            for item in graph["facts"]
        ],
    }


def _source_manifest(base, snapshot):
    return {
        "source_artifact_type": "story_seed",
        "source_artifact_id": snapshot.get("business_id"),
        "story_seed_version": base.get("story_seed_version"),
        "source_hash": base.get("outline_hash"),
    }


def _valid_source_manifest(plan, schema, snapshot):
    manifest = schema.get("source_manifest") or {}
    expected_id = (snapshot or {}).get("business_id")
    return bool(
        manifest.get("source_artifact_type") == "story_seed"
        and str(manifest.get("source_artifact_id") or "").strip()
        and (expected_id is None or manifest.get("source_artifact_id") == expected_id)
        and int(manifest.get("story_seed_version") or 0)
        == int(plan.get("story_seed_version") or 0)
        and manifest.get("source_hash") == plan.get("outline_hash")
    )


def _bind_initial_evidence(graph, base, snapshot):
    manifest = _source_manifest(base, snapshot)
    graph["evidence"] = [
        {
            **item,
            "source_artifact_type": manifest["source_artifact_type"],
            "source_artifact_id": manifest["source_artifact_id"],
            "source_version": manifest["story_seed_version"],
            "source_hash": manifest["source_hash"],
        }
        for item in graph.get("evidence") or []
    ]
    return graph


def _require_chapter_coverage(base, causal):
    positions = {int(item["position"]) for item in base.get("chapters") or []}
    event_positions = {
        int(item.get("chapter_position") or 0) for item in causal.get("events") or []
    }
    if event_positions != positions:
        raise ValueError(
            f"causal events must cover exactly every chapter: {sorted(event_positions)}"
        )
    obligation_positions = {
        int(item.get("chapter_position") or 0)
        for item in causal.get("obligations") or []
    }
    if obligation_positions != positions:
        raise ValueError("narrative obligations must cover exactly every chapter")


def _chapter_contracts(chapters, causal):
    events = causal.get("events") or []
    obligations = causal.get("obligations") or []
    return [
        {
            **row,
            "required_event_ids": [
                item["id"]
                for item in events
                if item["chapter_position"] == row["position"]
            ],
            "obligation_ids": [
                item["id"]
                for item in obligations
                if item["chapter_position"] == row["position"]
            ],
            "contract_status": "ready",
        }
        for row in chapters
    ]


def _valid_prompt_policy(policy):
    templates = policy.get("templates") or {}
    return bool(
        policy.get("schema") == "story_novel_prompt_policy.v15"
        and set(templates) == set(V5_TEMPLATES)
        and policy.get("hash") == value_hash(templates)
    )


def _required(payload, key):
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"v5 compile response missing {key}")
    return value
