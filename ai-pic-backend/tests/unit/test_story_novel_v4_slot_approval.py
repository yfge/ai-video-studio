from app.services.story.story_novel_v4_approval import _mandatory_slots_present


def test_mandatory_arc_slot_must_exist_in_final_revision_world():
    plan = {
        "arc_plans": {
            "arc-1": {
                "instantiated_character_slots": [
                    {"slot_id": "slot-rival", "mandatory": True}
                ],
                "instantiated_scope_slots": [],
            }
        }
    }
    state = {"revision_local_entities": {}}
    assert not _mandatory_slots_present(plan, state)
    state["revision_local_entities"]["entity-rival"] = {
        "attributes": {"slot_id": "slot-rival"}
    }
    assert _mandatory_slots_present(plan, state)
