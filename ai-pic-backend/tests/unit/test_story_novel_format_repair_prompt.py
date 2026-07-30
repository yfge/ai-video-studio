import json

import pytest
from app.services.story.story_novel_chapter_package_normalization import (
    normalize_missing_contract_fields,
)
from app.services.story.story_novel_v3_generation import _generate_with_format_repair
from app.services.story.story_novel_v3_prompts import chapter_package_prompt


class _GeneratedText(str):
    invocation_evidence = {}


@pytest.mark.asyncio
async def test_format_repair_must_fill_an_empty_required_brief_field():
    prompts = []
    budgets = []

    async def generate(_revision, prompt, **kwargs):
        prompts.append(prompt)
        budgets.append(kwargs["max_tokens"])
        if len(prompts) == 1:
            return _GeneratedText('{"causal_bridge":""}')
        return _GeneratedText('{"causal_bridge":"旱情迫使主角连夜寻找水源"}')

    def parse(text):
        payload = json.loads(text)
        if not payload["causal_bridge"].strip():
            raise ValueError("chapter brief causal_bridge 不能为空")
        return payload

    result, metrics = await _generate_with_format_repair(
        object(),
        "只规划当前章的抗旱行动",
        parse,
        generate,
        stage="chapter_planning.1",
        max_tokens=12_000,
        format_repair_max_tokens=12_000,
    )

    repair_prompt = prompts[1]
    error = "chapter brief causal_bridge 不能为空"
    assert result["causal_bridge"] == "旱情迫使主角连夜寻找水源"
    assert metrics["calls"] == 2
    assert repair_prompt.index(error) < repair_prompt.index("原任务：")
    assert "必须补出符合原任务的非空值" in repair_prompt
    assert "不得原样返回失败响应" in repair_prompt
    assert repair_prompt.count(error) == 2
    assert budgets == [12_000, 12_000]


def test_chapter_package_prompt_separates_predicates_from_typed_effects():
    prompt = chapter_package_prompt({"state_before": {"subjects": {}}})

    assert "operator/value 只属于 preconditions" in prompt
    assert "subject_id/field/from_value/to_value/reason" in prompt
    assert "禁止 add/add_to_set/remove" in prompt
    assert "subject_id/from_location_id/to_location_id/means" in prompt
    assert "character_id/fact_id/source_event_id" in prompt
    assert "不要输出 effect_coverage" in prompt
    assert "effect_review_contracts" not in prompt
    assert "人物 possessions 由服务端随 owner_id 确定性维护" in prompt
    assert "服务端会确定性编译 effect manifest、expected delta" in prompt
    assert "instant/start/progress/complete" in prompt
    assert "activity、reaction、observation" in prompt


def test_legacy_add_to_set_alias_is_normalized_from_exact_current_state():
    contract = {
        "state_transitions": [
            {
                "subject_id": "char-farmer",
                "field": "permissions",
                "operator": "add_to_set",
                "value": "trial-farming-right",
            }
        ]
    }
    state_before = {"subjects": {"char-farmer": {"permissions": []}}}

    result = normalize_missing_contract_fields(
        contract, {"entities": []}, state_before=state_before
    )

    assert result["state_transitions"] == [
        {
            "subject_id": "char-farmer",
            "field": "permissions",
            "from_value": [],
            "to_value": ["trial-farming-right"],
        }
    ]
