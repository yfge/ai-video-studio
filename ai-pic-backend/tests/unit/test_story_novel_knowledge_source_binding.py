from app.services.story.story_novel_plan_normalizer import normalize_plan_payload


def _payload(event_ids):
    return {
        "chapters": [
            {
                "knowledge_grants": [
                    {"character_id": "char-a", "fact_id": "fact-current"}
                ],
                "execution_contracts": [
                    {
                        "event_id": event_id,
                        "knowledge_fact_ids": ["fact-current"],
                    }
                    for event_id in event_ids
                ],
            }
        ]
    }


def test_binds_missing_knowledge_source_from_unique_execution_contract():
    chapter = normalize_plan_payload(_payload(["event-1-2"]))["chapters"][0]

    assert chapter["knowledge_grants"] == [
        {
            "character_id": "char-a",
            "fact_id": "fact-current",
            "source_event_id": "event-1-2",
        }
    ]


def test_keeps_ambiguous_missing_source_for_strict_schema_rejection():
    chapter = normalize_plan_payload(_payload(["event-1-1", "event-1-2"]))["chapters"][
        0
    ]

    assert "source_event_id" not in chapter["knowledge_grants"][0]


def test_preserves_provider_source_event_id():
    payload = _payload(["event-1-2"])
    payload["chapters"][0]["knowledge_grants"][0]["source_event_id"] = "event-1-1"

    chapter = normalize_plan_payload(payload)["chapters"][0]

    assert chapter["knowledge_grants"][0]["source_event_id"] == "event-1-1"
