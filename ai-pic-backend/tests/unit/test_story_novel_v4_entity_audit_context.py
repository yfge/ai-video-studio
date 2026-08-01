from app.services.story.story_novel_audit_contract_context import audit_contract_context


def test_entity_proof_context_carries_authorized_narrative_function():
    expected = {
        "knowledge_grants": [],
        "entity_introductions": [
            {
                "id": "revision-entity-1",
                "kind": "character",
                "name": "闻鹿",
                "aliases": [],
                "source_event_id": "event-1-1",
                "attributes": {
                    "narrative_function": "承担当前区域的引路与竞争作用",
                    "profile": "熟悉当前区域路线",
                },
                "initial_state": {"relationships": {"char-main": "谨慎合作"}},
            }
        ],
    }
    context = audit_contract_context(
        {
            "required_event_ids": ["event-1-1"],
            "key_events": ["闻鹿引导主角越过封锁"],
        },
        {"beats": []},
        expected,
        {"entities": []},
    )

    semantic = context["entity_introduction_semantics"][0]
    assert semantic["contract_id"] == "entity:revision-entity-1"
    assert semantic["narrative_function"] == "承担当前区域的引路与竞争作用"
    assert semantic["initial_relationships"] == {"char-main": "谨慎合作"}
