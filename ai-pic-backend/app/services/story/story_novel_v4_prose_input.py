"""Build a topic-neutral prose packet from one frozen planner snapshot."""

from __future__ import annotations

import copy


def build_v4_prose_input(
    snapshot: dict, intent: dict, contract: dict, brief: dict
) -> dict:
    source = snapshot["model_input"]
    entities = source.get("visible_characters_and_world") or []
    characters = [item for item in entities if item.get("kind") == "character"]
    world = [item for item in entities if item.get("kind") != "character"]
    motivations = {
        item["character_handle"]: item["motivation"]
        for item in intent.get("character_motivations") or []
    }
    safe_beats = [
        {
            "beat_id": item["beat_id"],
            "purpose": item["purpose"],
            "target_chars": item["target_chars"],
            "bound_event_ids": copy.deepcopy(item["event_handles"]),
            "effect_contract_ids": [],
        }
        for item in intent["beats"]
    ]
    event_rows = copy.deepcopy(source["current_chapter"]["events"])
    return {
        "schema": "story_novel_prose_packet.v2",
        "chapter_intent": {
            "beats": copy.deepcopy(intent["beats"]),
            "effect_intents": copy.deepcopy(intent.get("effect_intents") or []),
            "emotional_continuity": intent["emotional_continuity"],
            "causal_bridge": intent["causal_bridge"],
            "cliffhanger": intent["cliffhanger"],
        },
        "current_chapter": copy.deepcopy(source["current_chapter"]),
        "events": copy.deepcopy(source["current_chapter"]["events"]),
        "visible_characters": [
            {
                **copy.deepcopy(item),
                "motivation": motivations.get(item["entity_handle"]),
            }
            for item in characters
        ],
        "visible_world": copy.deepcopy(world),
        "authorized_new_entities": [
            {
                **{
                    key: copy.deepcopy(item.get(key))
                    for key in (
                        "proposal_handle",
                        "slot_id",
                        "kind",
                        "name",
                        "aliases",
                        "narrative_function",
                        "transient",
                        "profile",
                        "relationship_intents",
                        "capabilities",
                        "resources",
                        "knowledge_boundary",
                        "arc_direction",
                        "attributes",
                    )
                },
                "motivation": motivations.get(item["proposal_handle"]),
            }
            for item in intent.get("entity_proposals") or []
        ],
        "previous_chapter_tail": source.get("previous_chapter_tail") or "",
        "chapter_length": {
            key: int(contract[key])
            for key in ("min_chars", "target_chars", "max_chars")
        },
        "writing_style": copy.deepcopy(source.get("story_invariants") or {}),
        "prompt_evidence": {
            "planner_snapshot_hash": snapshot["snapshot_hash"],
            "raw_world_event_count": 0,
            "raw_character_memory_count": 0,
            "future_chapter_count": 0,
            "database_id_count": 0,
        },
        "expected_block_ids": [item["beat_id"] for item in brief["beats"]],
        "chapter_brief": {
            "beats": safe_beats,
            "emotional_continuity": intent["emotional_continuity"],
            "causal_bridge": intent["causal_bridge"],
        },
        "current_chapter_context": {
            "events": [
                {
                    "event_id": item["event_handle"],
                    "event": item["description"],
                    "execution": {"action_phase": "current_chapter"},
                    "scene_participants": [],
                }
                for item in event_rows
            ],
            "characters": copy.deepcopy(characters),
            "scene_participants": [],
        },
        "visible_canon": {
            "characters": copy.deepcopy(characters),
            "world": copy.deepcopy(world),
        },
        "repair_contract": {
            "scope": "current_blocks_only",
        },
    }
