import copy

import pytest
from app.services.story.story_novel_chapter_brief_contract import (
    BRIEF_SCHEMA,
    compile_chapter_brief_input,
    expected_beat_count,
    validate_chapter_brief,
)
from app.services.story.story_novel_context_utils import value_hash
from app.services.story.story_novel_v3_prompts import chapter_brief_prompt


def _chapter(target_chars=4000):
    return {
        "position": 2,
        "title": "取样",
        "target_chars": target_chars,
        "required_event_ids": ["event-r17"],
        "key_events": ["苏砚封存R-17样本"],
        "state_transitions": [
            {
                "subject_id": "sample-r17",
                "field": "status",
                "from_value": "未封存",
                "to_value": "已封存",
            }
        ],
        "location_transitions": [],
        "knowledge_grants": [],
        "milestones_consumed": [],
        "open_threads": ["thread-r17-source"],
        "payoffs_due": [],
        "execution_contracts": [
            {
                "event_id": "event-r17",
                "action_phase": "complete",
                "time_scope": "unspecified",
                "actor_ids": ["char-su-yan"],
                "effort": "light",
                "timeline_ids": [],
                "knowledge_fact_ids": [],
            }
        ],
    }


def _brief(planning_input):
    count = planning_input["expected_beat_count"]
    total = planning_input["chapter_contract"]["target_chars"]
    quotient, remainder = divmod(total, count)
    beats = []
    for index in range(1, count + 1):
        beats.append(
            {
                "beat_id": f"B{index:02d}",
                "purpose": f"推进当前章第 {index} 个节拍",
                "target_chars": quotient + (1 if index <= remainder else 0),
                "allowed_entity_ids": ["char-su-yan"],
                "bound_event_ids": ["event-r17"] if index == count else [],
                "effect_contract_ids": (
                    [
                        item["contract_id"]
                        for item in planning_input["expected_delta"]["proof_contracts"]
                    ]
                    if index == count
                    else []
                ),
            }
        )
    return {
        "schema": BRIEF_SCHEMA,
        "chapter_contract_hash": planning_input["chapter_contract_hash"],
        "state_before_hash": planning_input["state_before_hash"],
        "input_evidence_hash": planning_input["input_evidence_hash"],
        "execution_contracts": copy.deepcopy(
            planning_input["chapter_contract"].get("execution_contracts") or []
        ),
        "beats": beats,
        "character_motivations": [
            {"character_id": "char-su-yan", "motivation": "追查样本来源"}
        ],
        "emotional_continuity": "承接上一章的戒备",
        "causal_bridge": "样本异常促使苏砚取样",
        "summary": "苏砚封存样本并开始追查来源。",
        "cliffhanger": "样本编号与旧案记录吻合。",
        "setup_thread_ids": list(
            planning_input["chapter_contract"].get("open_threads") or []
        ),
        "payoff_thread_ids": list(
            planning_input["chapter_contract"].get("payoffs_due") or []
        ),
    }


def test_expected_beat_count_is_ceil_bounded_to_four_and_six():
    assert expected_beat_count(100) == 4
    assert expected_beat_count(2000) == 4
    assert expected_beat_count(2500) == 4
    assert expected_beat_count(3000) == 5
    assert expected_beat_count(10000) == 6


def test_brief_prompt_requests_every_required_narrative_field_and_exact_threads():
    prompt = chapter_brief_prompt({"chapter_contract": _chapter()})

    assert '"summary":"当前章摘要"' in prompt
    assert '"cliffhanger":"当前章末钩子"' in prompt
    assert "必须逐字、同序复制当前合同的 open_threads 与 payoffs_due" in prompt
    assert "execution_contracts 必须逐字复制当前章节合同" in prompt
    assert "明确要求连载或商业网文" in prompt
    assert "一般戏剧化、行动略快只属软编辑建议" in prompt


def test_brief_binds_current_contract_state_and_planning_evidence_hashes():
    state = {"subjects": {"char-su-yan": {"knowledge": []}}}
    planning_input = compile_chapter_brief_input(
        _chapter(),
        state,
        world_events=[
            {"id": "evt-previous", "source_hash": "body-a", "summary": "此前取样"}
        ],
        character_memories=[
            {
                "business_id": "mem-su",
                "source_hash": "body-a",
                "content": "苏砚保持戒备",
            }
        ],
        allowed_entity_ids=["char-su-yan", "sample-r17"],
    )

    validated = validate_chapter_brief(_brief(planning_input), planning_input)

    assert validated["brief_hash"]
    assert validated["summary"] == "苏砚封存样本并开始追查来源。"
    assert (
        planning_input["planning_evidence"]["world_events"][0]["evidence_id"]
        == "evt-previous"
    )
    assert (
        planning_input["expected_delta"]["state_before_hash"]
        == planning_input["state_before_hash"]
    )
    assert planning_input["brief_policy_version"].endswith(".v3")
    assert planning_input["input_evidence_hash"] != value_hash(
        planning_input["planning_evidence"]
    )
    assert validate_chapter_brief(validated, planning_input) == validated

    tampered = copy.deepcopy(validated)
    tampered["summary"] = "篡改后的摘要"
    with pytest.raises(ValueError, match="brief hash 不匹配"):
        validate_chapter_brief(tampered, planning_input)


def test_brief_rejects_contract_mutation_and_future_event_reference():
    planning_input = compile_chapter_brief_input(
        _chapter(),
        {"subjects": {}},
        allowed_entity_ids=["char-su-yan"],
    )
    mutated = _brief(planning_input)
    mutated["state_transitions"] = []
    with pytest.raises(ValueError, match="越界字段"):
        validate_chapter_brief(mutated, planning_input)

    future = _brief(planning_input)
    future["beats"][0]["bound_event_ids"] = ["event-chapter-19"]
    with pytest.raises(ValueError, match="当前章节合同外"):
        validate_chapter_brief(future, planning_input)


def test_brief_rejects_stale_evidence_binding_and_invalid_effect_contract():
    planning_input = compile_chapter_brief_input(
        _chapter(),
        {"subjects": {}},
        world_events=[{"id": "evt-1", "source_hash": "body-a"}],
        allowed_entity_ids=["char-su-yan"],
    )
    stale = _brief(planning_input)
    stale["input_evidence_hash"] = "stale"
    with pytest.raises(ValueError, match="input_evidence_hash 不匹配"):
        validate_chapter_brief(stale, planning_input)

    invalid = _brief(planning_input)
    invalid["beats"][0]["effect_contract_ids"] = ["state:99"]
    with pytest.raises(ValueError, match="当前章节合同外"):
        validate_chapter_brief(invalid, planning_input)

    changed_execution = _brief(planning_input)
    changed_execution["execution_contracts"][0]["action_phase"] = "start"
    with pytest.raises(ValueError, match="execution_contracts 必须逐字复制"):
        validate_chapter_brief(changed_execution, planning_input)

    missing_summary = _brief(planning_input)
    missing_summary["summary"] = ""
    with pytest.raises(ValueError, match="summary 不能为空"):
        validate_chapter_brief(missing_summary, planning_input)

    changed = copy.deepcopy(planning_input)
    changed["planning_evidence"]["world_events"][0]["source_hash"] = "body-b"
    assert changed["planning_evidence"] != planning_input["planning_evidence"]


def test_brief_reports_exact_missing_expected_delta_contract_ids():
    planning_input = compile_chapter_brief_input(
        _chapter(), {"subjects": {}}, allowed_entity_ids=["char-su-yan"]
    )
    incomplete = _brief(planning_input)
    incomplete["beats"][-1]["effect_contract_ids"].remove("state:1")

    with pytest.raises(ValueError, match=r"缺少 ID: \['state:1'\]"):
        validate_chapter_brief(incomplete, planning_input)


def test_model_brief_normalizes_only_exact_contract_id_prefix():
    planning_input = compile_chapter_brief_input(
        _chapter(), {"subjects": {}}, allowed_entity_ids=["char-su-yan"]
    )
    aliased = _brief(planning_input)
    aliased["beats"][-1]["effect_contract_ids"] = [
        f"contract_id:{value}" for value in aliased["beats"][-1]["effect_contract_ids"]
    ]

    validated = validate_chapter_brief(
        aliased, planning_input, normalize_model_aliases=True
    )

    assert "state:1" in validated["beats"][-1]["effect_contract_ids"]
    with pytest.raises(ValueError, match="合同外 ID"):
        validate_chapter_brief(aliased, planning_input)


@pytest.mark.parametrize(
    ("brief_key", "contract_key"),
    [("setup_thread_ids", "open_threads"), ("payoff_thread_ids", "payoffs_due")],
)
def test_brief_rejects_reordered_thread_contract_ids(brief_key, contract_key):
    chapter = _chapter()
    chapter["open_threads"] = ["thread-a", "thread-b"]
    chapter["payoffs_due"] = ["thread-c", "thread-d"]
    planning_input = compile_chapter_brief_input(
        chapter, {"subjects": {}}, allowed_entity_ids=["char-su-yan"]
    )
    brief = _brief(planning_input)
    brief[brief_key] = list(reversed(chapter[contract_key]))

    with pytest.raises(ValueError, match="必须完整覆盖当前章节合同"):
        validate_chapter_brief(brief, planning_input)
