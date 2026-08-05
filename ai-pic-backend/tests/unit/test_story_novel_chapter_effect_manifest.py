from app.services.story.story_novel_chapter_effect_manifest import (
    compile_effect_manifest,
    effect_manifest_checkpoint_valid,
)


def test_service_compiles_typed_effect_manifest_without_model_coverage():
    contract = {
        "state_transitions": [
            {"subject_id": "char-a", "field": "status", "to_value": "ready"}
        ],
        "location_transitions": [
            {"subject_id": "char-a", "to_location_id": "loc-field"}
        ],
        "knowledge_grants": [
            {
                "character_id": "char-a",
                "fact_id": "fact-current",
                "source_event_id": "event-1-1",
            }
        ],
        "milestones_consumed": ["mile-1"],
    }
    canon = {
        "milestones": [
            {
                "id": "mile-1",
                "outcomes": [
                    {
                        "subject_id": "obj-contract",
                        "field": "owner_id",
                        "operator": "eq",
                        "value": "char-a",
                    }
                ],
            }
        ]
    }

    manifest = compile_effect_manifest(contract, canon)
    chapter = {**contract, "effect_manifest": manifest}

    assert [item["effect_ref"] for item in manifest["items"]] == [
        "state:1",
        "location:1",
        "knowledge:1",
        "milestone:mile-1:obj-contract:owner_id",
    ]
    assert manifest["items"][2]["source_event_id"] == "event-1-1"
    assert effect_manifest_checkpoint_valid(chapter)


def test_effect_manifest_checkpoint_rejects_tamper_and_missing_effect():
    contract = {
        "state_transitions": [
            {"subject_id": "char-a", "field": "status", "to_value": "ready"}
        ],
        "location_transitions": [],
        "knowledge_grants": [],
        "milestones_consumed": [],
    }
    manifest = compile_effect_manifest(contract, {"milestones": []})
    chapter = {**contract, "effect_manifest": manifest}

    manifest["items"] = []

    assert not effect_manifest_checkpoint_valid(chapter)
