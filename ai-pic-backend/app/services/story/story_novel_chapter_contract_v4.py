"""Compile a v4 executable contract and brief from semantic intent."""

from __future__ import annotations

import copy

from .story_novel_chapter_effect_manifest import compile_effect_manifest
from .story_novel_context_utils import value_hash
from .story_novel_effect_compiler import compile_intent_effects, effect_model_input
from .story_novel_expected_delta import compile_expected_delta
from .story_novel_incremental_plan import chapter_skeleton
from .story_novel_world_expansion import (
    normalize_package_expansion,
    state_with_pending_expansion,
)


def compile_intent_contract(
    skeleton: dict, intent: dict, snapshot: dict, canon: dict
) -> tuple[dict, dict, dict]:
    bindings = snapshot["handle_bindings"]
    event_ids = bindings["events"]
    entity_ids = bindings["entities"]
    entity_refs = {
        **entity_ids,
        **{
            item["proposal_handle"]: item["proposal_handle"]
            for item in intent.get("entity_proposals") or []
        },
    }
    contract = {
        **chapter_skeleton(skeleton),
        "preconditions": copy.deepcopy(skeleton.get("preconditions") or []),
        "entity_introductions": _raw_introductions(intent, event_ids, entity_ids),
    }
    raw_brief = _brief(intent, event_ids, entity_refs, int(skeleton["target_chars"]))
    state_before = snapshot["execution_context"]["state_before"]
    contract, raw_brief = normalize_package_expansion(
        contract, raw_brief, canon, state_before
    )
    proposal_ids = {
        proposal["proposal_handle"]: introduction["id"]
        for proposal, introduction in zip(
            [
                item
                for item in intent.get("entity_proposals") or []
                if not item["transient"]
            ],
            contract["entity_introductions"],
            strict=True,
        )
    }
    effect_context = {
        "entities": {**entity_ids, **proposal_ids},
        "state_before": state_with_pending_expansion(
            state_before, contract["entity_introductions"]
        ),
        "model_input": effect_model_input(snapshot, intent),
    }
    effects, effect_event_bindings, effect_semantics = compile_intent_effects(
        skeleton, intent, snapshot, canon, effect_context
    )
    contract.update(
        {
            **effects,
            "effect_event_bindings": effect_event_bindings,
            "effect_semantics": effect_semantics,
            "execution_contracts": _execution_contracts(
                intent, event_ids, {**entity_ids, **proposal_ids}
            ),
            "contract_status": "compiled",
            "contract_schema": "story_novel_chapter_contract.v2",
        }
    )
    contract["state_compiler"] = {
        "version": 1,
        "source_effect_hash": value_hash(
            {
                key: contract.get(key) or []
                for key in (
                    "state_transitions",
                    "knowledge_grants",
                    "location_transitions",
                    "milestones_consumed",
                )
            }
        ),
    }
    for execution in contract["execution_contracts"]:
        event_id = execution["event_id"]
        execution["timeline_ids"] = [
            timeline_id
            for timeline_id, bound_event in (
                contract.get("timeline_event_bindings") or {}
            ).items()
            if bound_event == event_id
        ]
        execution["knowledge_fact_ids"] = [
            item["fact_id"]
            for item in contract.get("knowledge_grants") or []
            if item.get("source_event_id") == event_id
        ]
    contract["effect_manifest"] = compile_effect_manifest(contract, canon)
    expected_delta = compile_expected_delta(contract, state_before)
    brief = _bind_effects(raw_brief, expected_delta, effect_event_bindings)
    brief.update(
        schema="story_novel_chapter_brief.v1",
        planner_snapshot_hash=snapshot["snapshot_hash"],
        intent_hash=intent["intent_hash"],
        chapter_contract_hash=value_hash(contract),
        state_before_hash=snapshot["state_before_hash"],
        input_evidence_hash=value_hash(snapshot["source_manifest"]),
        execution_contracts=copy.deepcopy(contract["execution_contracts"]),
        setup_thread_ids=copy.deepcopy(contract.get("open_threads") or []),
        payoff_thread_ids=copy.deepcopy(contract.get("payoffs_due") or []),
    )
    brief["brief_hash"] = value_hash(brief)
    return contract, brief, expected_delta


def _execution_contracts(intent, events, entities) -> list[dict]:
    actors: dict[str, list[str]] = {key: [] for key in events}
    for beat in intent["beats"]:
        resolved = [entities.get(item, item) for item in beat["character_handles"]]
        for handle in beat["event_handles"]:
            actors[handle].extend(resolved)
    return [
        {
            "event_id": event_id,
            "action_phase": "instant",
            "time_scope": "unspecified",
            "actor_ids": list(dict.fromkeys(actors[handle])),
            "effort": "unspecified",
            "timeline_ids": [],
            "knowledge_fact_ids": [],
        }
        for handle, event_id in events.items()
    ]


def _raw_introductions(intent, events, entities) -> list[dict]:
    return [
        {
            "ref": item["proposal_handle"],
            "kind": item["kind"],
            "name": item["name"],
            "aliases": item["aliases"],
            "attributes": {
                **_replace_handles(item["attributes"], entities),
                "narrative_function": item["narrative_function"],
                "slot_id": item["slot_id"],
                "profile": item["profile"],
                "arc_direction": item["arc_direction"],
                "knowledge_boundary": item["knowledge_boundary"],
            },
            "initial_state": _initial_state(item, entities),
            "source_event_id": events[item["source_event_handle"]],
            "persistence": "revision",
            "reason": item["narrative_function"],
        }
        for item in intent["entity_proposals"]
        if not item["transient"]
    ]


def _replace_handles(value, entities: dict[str, str]):
    if isinstance(value, str):
        return entities.get(value, value)
    if isinstance(value, list):
        return [_replace_handles(item, entities) for item in value]
    if isinstance(value, dict):
        return {key: _replace_handles(item, entities) for key, item in value.items()}
    return value


def _initial_state(item: dict, entities: dict[str, str]) -> dict:
    if item["kind"] == "character":
        return {
            "knowledge": [],
            "possessions": list(item["resources"]),
            "capabilities": list(item["capabilities"]),
            "relationships": {
                entities.get(row["target_handle"], row["target_handle"]): row[
                    "relationship"
                ]
                for row in item["relationship_intents"]
            },
        }
    return {}


def _brief(intent, events, entities, target: int) -> dict:
    beats = []
    for item in intent["beats"]:
        beats.append(
            {
                "beat_id": item["beat_id"],
                "purpose": item["purpose"],
                "target_chars": item["target_chars"],
                "allowed_entity_ids": list(entities.values()),
                "bound_event_ids": [events[value] for value in item["event_handles"]],
                "effect_contract_ids": [],
            }
        )
    if sum(item["target_chars"] for item in beats) != target:
        raise ValueError("intent beat 字符预算与章节合同不一致")
    return {
        "beats": beats,
        "character_motivations": [
            {
                "character_id": entities[item["character_handle"]],
                "motivation": item["motivation"],
            }
            for item in intent["character_motivations"]
        ],
        "emotional_continuity": intent["emotional_continuity"],
        "causal_bridge": intent["causal_bridge"],
        "summary": intent["summary"],
        "cliffhanger": intent["cliffhanger"],
        "continuity_watchpoints": [],
    }


def _bind_effects(brief: dict, delta: dict, bindings: dict[str, str]) -> dict:
    beats = brief["beats"]
    for proof in delta["proof_contracts"]:
        event_id = _effect_event(proof, bindings)
        target = next(
            (item for item in beats if event_id in item["bound_event_ids"]),
            beats[-1],
        )
        target["effect_contract_ids"].append(proof["contract_id"])
    return brief


def _effect_event(proof: dict, bindings: dict[str, str]) -> str | None:
    if proof["kind"] == "event":
        return proof["value"]
    value = proof.get("value") or {}
    if proof["kind"] in {"knowledge_grant", "entity_introduction"}:
        return value.get("source_event_id")
    return bindings.get(proof["contract_id"])
