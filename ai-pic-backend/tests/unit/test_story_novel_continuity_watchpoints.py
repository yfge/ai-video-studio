import copy

import pytest
from app.services.story import story_novel_chapter_package_context as package_context
from app.services.story import story_novel_priority_evidence as priority_evidence
from app.services.story.story_novel_brief_policy import BRIEF_POLICY_VERSION
from app.services.story.story_novel_chapter_brief_contract import (
    compile_chapter_brief_input,
    validate_chapter_brief,
)
from app.services.story.story_novel_continuity_watchpoints import (
    watchpoint_evidence_ids,
)
from app.services.story.story_novel_v3_prompts import (
    audit_contract_context,
    chapter_audit_prompt,
    chapter_package_prompt,
    prose_blocks_prompt,
)


def test_watchpoints_are_source_bound_and_survive_into_prose_and_audit():
    source = _brief_input()
    brief = _brief(source)

    validated = validate_chapter_brief(brief, source)
    audit_context = audit_contract_context(
        source["chapter_contract"], validated, source["expected_delta"], _canon()
    )
    prose_prompt = prose_blocks_prompt(
        {
            "chapter_brief": validated,
            "current_chapter_context": {},
            "visible_canon": {},
        }
    )

    assert validated["continuity_watchpoints"] == brief["continuity_watchpoints"]
    assert audit_context["continuity_watchpoints"] == brief["continuity_watchpoints"]
    assert "借用已经到期" in prose_prompt
    assert "先前事件的完整原文" not in prose_prompt


def test_watchpoints_reject_unbound_evidence_and_state_subjects():
    source = _brief_input()
    invalid_evidence = _brief(source)
    invalid_evidence["continuity_watchpoints"][0]["source_evidence_ids"] = [
        "evt-future"
    ]
    with pytest.raises(ValueError, match="越界 evidence"):
        validate_chapter_brief(invalid_evidence, source)

    invalid_subject = _brief(source)
    invalid_subject["continuity_watchpoints"][0]["source_evidence_ids"] = []
    invalid_subject["continuity_watchpoints"][0]["source_subject_ids"] = ["obj-unknown"]
    with pytest.raises(ValueError, match="越界 subject"):
        validate_chapter_brief(invalid_subject, source)


def test_watchpoints_are_optional_soft_guards_not_growth_kpis():
    source = _brief_input()
    brief = _brief(source)
    brief["continuity_watchpoints"] = []

    validated = validate_chapter_brief(brief, source)
    package_prompt = chapter_package_prompt(
        {
            "prior_world_events": [],
            "prior_character_memories": [],
            "state_before": {"subjects": {}},
            "current_progression_arc": {
                "growth": {
                    "cognition": None,
                    "capability": None,
                    "resources": None,
                    "activity_and_time_scale": None,
                }
            },
        }
    )
    audit_prompt = chapter_audit_prompt(
        {"current_contract_context": {"continuity_watchpoints": []}}
    )

    assert validated["continuity_watchpoints"] == []
    assert "不得在本章逐项兑现" in package_prompt
    assert "没有相关约束时输出 []" in package_prompt
    assert "不得要求正文\n复述 watchpoint" in audit_prompt


def test_package_rebuild_prioritizes_the_exact_prompt_watchpoint_sources(monkeypatch):
    captured = {}

    def build(*_args, **kwargs):
        captured.update(kwargs)
        return {"brief_input": {}}

    monkeypatch.setattr(package_context, "build_v3_planning_context", build)
    brief = {
        "continuity_watchpoints": [
            {
                "source_evidence_ids": ["memory-long", "event-bound"],
            },
            {"source_evidence_ids": ["memory-long"]},
        ]
    }

    package_context.build_final_package_context(None, None, 5, {}, brief)

    assert watchpoint_evidence_ids(brief) == ["memory-long", "event-bound"]
    assert captured["priority_evidence_ids"] == ["memory-long", "event-bound"]
    assert captured["persist_memory_snapshots"] is False


def test_priority_evidence_survives_when_optional_context_is_truncated(monkeypatch):
    monkeypatch.setattr(priority_evidence, "CONTEXT_CHAR_BUDGET", 320)
    pack, truncations = {}, []
    memory = {"business_id": "memory-long", "content": "记" * 80}
    optional = {"business_id": "event-optional", "summary": "事" * 400}

    priority_evidence.add_priority_evidence(
        pack, [], [memory], {"memory-long"}, truncations
    )
    priority_evidence.append_unpinned_evidence(
        pack, "world_events", [optional], {"memory-long"}, truncations
    )

    assert pack["character_memories"] == [memory]
    assert pack["world_events"] == []
    assert truncations[-1] == {
        "section": "world_events",
        "original_items": 1,
        "kept_items": 0,
    }


def _brief_input() -> dict:
    chapter = {
        "position": 6,
        "title": "再用旧工具",
        "target_chars": 2500,
        "required_event_ids": ["event-6-1"],
        "key_events": ["主角完成当前尝试"],
        "state_transitions": [],
        "location_transitions": [],
        "knowledge_grants": [],
        "milestones_consumed": [],
        "open_threads": [],
        "payoffs_due": [],
        "execution_contracts": [
            {
                "event_id": "event-6-1",
                "action_phase": "complete",
                "time_scope": "unspecified",
                "actor_ids": ["char-main"],
                "effort": "light",
                "timeline_ids": [],
                "knowledge_fact_ids": [],
            }
        ],
    }
    return compile_chapter_brief_input(
        chapter,
        {"subjects": {"char-main": {"status": "active"}}},
        world_events=[
            {
                "id": "evt-borrow-returned",
                "source_hash": "body-2",
                "summary": "工具只借半日并已归还",
                "source_quote": "先前事件的完整原文",
            }
        ],
        allowed_entity_ids=["char-main"],
        brief_policy_version=BRIEF_POLICY_VERSION,
    )


def _brief(source: dict) -> dict:
    count = source["expected_beat_count"]
    total = source["chapter_contract"]["target_chars"]
    base, extra = divmod(total, count)
    effect_ids = [
        item["contract_id"] for item in source["expected_delta"]["proof_contracts"]
    ]
    result = {
        "schema": "story_novel_chapter_brief.v1",
        "chapter_contract_hash": source["chapter_contract_hash"],
        "state_before_hash": source["state_before_hash"],
        "input_evidence_hash": source["input_evidence_hash"],
        "execution_contracts": copy.deepcopy(
            source["chapter_contract"]["execution_contracts"]
        ),
        "beats": [
            {
                "beat_id": f"B{index:02d}",
                "purpose": "推进当前选择",
                "target_chars": base + int(index <= extra),
                "allowed_entity_ids": ["char-main"],
                "bound_event_ids": ["event-6-1"] if index == count else [],
                "effect_contract_ids": effect_ids if index == count else [],
            }
            for index in range(1, count + 1)
        ],
        "character_motivations": [],
        "emotional_continuity": "承接上一章的谨慎",
        "causal_bridge": "既有约束影响当前选择",
        "summary": "主角在限制下完成尝试。",
        "cliffhanger": "新的选择出现。",
        "continuity_watchpoints": [
            {
                "watchpoint_id": "W01",
                "kind": "resource",
                "constraint": "工具的临时借用已经到期，不能无来源继续使用。",
                "source_evidence_ids": ["evt-borrow-returned"],
                "source_subject_ids": [],
            }
        ],
        "setup_thread_ids": [],
        "payoff_thread_ids": [],
    }
    return result


def _canon() -> dict:
    return {"entities": [{"id": "char-main", "kind": "character", "name": "主角"}]}
