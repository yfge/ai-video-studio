from types import SimpleNamespace

from app.services.narrative_memory.dramatic_state_service import DramaticStateService


def test_dramatic_state_gate_separates_subtext_and_disclosure():
    state = {
        "must_not_reveal": ["密门在井下"],
        "character_intents": [
            {
                "character_business_id": "char-a",
                "hidden_goal": "逼他交出钥匙",
                "expression_policy": "subtext_only",
            }
        ],
    }
    script = SimpleNamespace(
        dialogues=[{"scene_number": 1, "content": "密门在井下，逼他交出钥匙"}]
    )
    gate = DramaticStateService._quality_gate(state, script, {"scene_number": 1})
    assert gate["passed"] is False
    assert {item["id"] for item in gate["blocking_issues"]} == {
        "must_not_reveal",
        "subtext_spoken_directly",
    }
