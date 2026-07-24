import json

from app.services.story.story_novel_canon_service import parse_model_canon
from tests.unit.test_story_novel_longform import _canon


def test_model_world_rules_are_replaced_by_static_seed_constraints():
    raw = _canon()
    raw["world_rules"] = [
        {"id": "leak", "statement": "第48章才揭露幕后身份", "exceptions": []}
    ]
    contract = {
        "story_seed": {
            "world_constraints": [
                "任何角色都不能瞬移",
                "第48章才揭露幕后身份",
            ],
            "structured_outline": {"chapters": []},
        }
    }

    canon, error, _diagnostics = parse_model_canon(
        json.dumps(raw, ensure_ascii=False),
        contract,
    )

    assert error is None
    assert canon["world_rules"] == [
        {
            "id": "rule-source-1",
            "statement": "任何角色都不能瞬移",
            "exceptions": [],
        }
    ]
    assert "幕后身份" not in json.dumps(canon, ensure_ascii=False)
