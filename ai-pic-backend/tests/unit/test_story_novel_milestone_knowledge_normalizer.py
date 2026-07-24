from app.services.story.story_novel_plan_normalizer import normalize_plan_payload
from app.services.story.story_novel_plan_validator import validate_generation_plan


def _canon():
    return {
        "entities": [
            {
                "id": "char-a",
                "kind": "character",
                "name": "甲",
                "aliases": [],
                "attributes": {},
            }
        ],
        "initial_state": {
            "char-a": {"location": None, "knowledge": [], "permissions": []}
        },
        "milestones": [
            {
                "id": "mile-fact",
                "planned_position": 1,
                "repeatable": False,
                "outcomes": [
                    {
                        "subject_id": "char-a",
                        "field": "knowledge",
                        "operator": "contains",
                        "value": "fact-exact",
                    }
                ],
            }
        ],
    }


def _chapter(grants):
    return {
        "position": 1,
        "key_events": ["角色确认事实"],
        "required_event_ids": ["event-1"],
        "timeline_event_bindings": {},
        "state_transitions": [],
        "knowledge_grants": grants,
        "location_transitions": [],
        "milestones_consumed": ["mile-fact"],
    }


def test_model_milestone_knowledge_uses_exact_canon_fact_id():
    chapter = _chapter(
        [
            {
                "character_id": "char-a",
                "fact_id": "知识-fact-exact",
                "source_event_id": "event-1",
            }
        ]
    )
    try:
        validate_generation_plan(_canon(), [chapter])
    except ValueError as exc:
        assert "里程碑结果未落地" in str(exc)
    else:
        raise AssertionError("raw validator must reject the provider alias")

    normalized = normalize_plan_payload({"chapters": [chapter]}, _canon())["chapters"][
        0
    ]

    assert normalized["knowledge_grants"][0]["fact_id"] == "fact-exact"
    validate_generation_plan(_canon(), [normalized])


def test_ambiguous_milestone_knowledge_alias_remains_invalid():
    chapter = _chapter(
        [
            {
                "character_id": "char-a",
                "fact_id": prefix + "fact-exact",
                "source_event_id": "event-1",
            }
            for prefix in ("知识-", "确认-")
        ]
    )

    normalized = normalize_plan_payload({"chapters": [chapter]}, _canon())["chapters"][
        0
    ]

    assert [item["fact_id"] for item in normalized["knowledge_grants"]] == [
        "知识-fact-exact",
        "确认-fact-exact",
    ]
