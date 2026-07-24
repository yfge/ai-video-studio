import copy

import pytest
from app.services.story.story_novel_canon_service import validate_generation_plan
from tests.unit.test_story_novel_longform import _canon, _plan_row


def test_plan_rejects_knowledge_grant_to_non_character():
    canon = _canon()
    plan = copy.deepcopy(_plan_row(1))
    plan["knowledge_grants"] = [
        {
            "character_id": "object-key",
            "fact_id": "fact-secret",
            "source_event_id": "event-1",
        }
    ]
    canon["entities"].append(
        {
            "id": "object-key",
            "kind": "object",
            "name": "钥匙",
            "aliases": [],
            "attributes": {},
        }
    )
    canon["initial_state"]["object-key"] = {"status": "在库"}

    with pytest.raises(ValueError, match="知识只能授予角色"):
        validate_generation_plan(canon, [plan])
