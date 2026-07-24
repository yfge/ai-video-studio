from app.services.story.story_novel_plot_contract import validated_plot_delta
from tests.unit.test_story_novel_longform import _plan_row


def test_authoritative_plot_delta_is_derived_from_typed_state():
    plan = {
        **_plan_row(),
        "key_events": ["交接唯一风钥"],
        "open_threads": ["谁篡改了数据"],
    }
    delta = {
        "opened_thread_ids": ["谁篡改了数据"],
        "resolved_thread_ids": [],
        "state_transitions": [
            {
                "subject_id": "obj-key",
                "field": "owner_id",
                "to_value": "char-a",
            }
        ],
        "knowledge_grants": [],
        "location_transitions": [],
    }

    assert validated_plot_delta(plan, delta) == {
        "key_events": ["交接唯一风钥"],
        "unresolved_threads": ["谁篡改了数据"],
        "resolved_threads": [],
        "character_states": {"obj-key": {"owner_id": "char-a"}},
    }
