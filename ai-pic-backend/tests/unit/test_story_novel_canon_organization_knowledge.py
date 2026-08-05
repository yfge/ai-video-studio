import json

import pytest
from app.services.story.story_novel_ai_prompts import canon_prompt
from app.services.story.story_novel_canon_repair import canon_repair_prompt
from app.services.story.story_novel_canon_service import (
    normalize_canon,
    parse_model_canon,
)


def _raw_canon():
    return {
        "gate_version": 2,
        "timeline": [],
        "entities": [
            {
                "id": "char-a",
                "kind": "character",
                "name": "甲",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "loc-a",
                "kind": "location",
                "name": "甲地",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "org-market",
                "kind": "organization",
                "name": "市场组织",
                "aliases": [],
                "attributes": {},
            },
        ],
        "world_rules": [],
        "milestones": [
            {
                "id": "mile-trust",
                "label": "建立合作信任",
                "planned_position": 1,
                "repeatable": False,
                "outcomes": [
                    {
                        "subject_id": "org-market",
                        "field": "knowledge",
                        "operator": "contains",
                        "value": "fact-supplier-trusted",
                    },
                    {
                        "subject_id": "org-market",
                        "field": "status",
                        "operator": "eq",
                        "value": "supplier-trusted",
                    },
                ],
            }
        ],
        "character_arcs": [],
        "initial_state": {
            "char-a": {"location": "loc-a", "knowledge": []},
            "loc-a": {"status": "active"},
            "org-market": {"status": "supplier-untrusted"},
        },
    }


def test_long_outline_canon_filter_drops_organization_knowledge_without_chapters():
    raw = _raw_canon()
    contract = {
        "story_seed": {
            "structured_outline": {"progression_arcs": []},
            "world_constraints": [],
        }
    }

    canon, error, diagnostics = parse_model_canon(
        json.dumps(raw, ensure_ascii=False), contract
    )

    assert error is None
    assert canon["milestones"][0]["outcomes"] == [
        {
            "subject_id": "org-market",
            "field": "status",
            "operator": "eq",
            "value": "supplier-trusted",
        }
    ]
    assert diagnostics == [
        {
            "id": "mile-trust",
            "section": "milestone",
            "reason": "non_character_knowledge_subject",
            "subject_id": "org-market",
            "fact_id": "fact-supplier-trusted",
        }
    ]
    with pytest.raises(ValueError, match="knowledge outcome 只能授予角色"):
        normalize_canon(raw)


def test_canon_prompts_forbid_organization_knowledge():
    prompt = canon_prompt(planning_contract={})
    repair = canon_repair_prompt(prompt, json.dumps(_raw_canon()), "组织知识无效")

    assert "subject_id 只能是 kind=character" in prompt
    assert "contains 只允许用于 initial_state 中真实为 JSON 数组的字段" in prompt
    assert "status、identity、owner_id、location 等标量字段必须使用 eq" in prompt
    assert "禁止保留 organization knowledge" in repair
