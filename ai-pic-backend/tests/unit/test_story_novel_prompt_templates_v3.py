import json
from types import SimpleNamespace

import pytest
from app.prompts.manager import prompt_manager
from app.services.story import story_novel_task_generation
from app.services.story.story_novel_ai_prompts import (
    SYSTEM_PROMPT,
    canon_prompt,
    structured_outline_prompt,
    structured_outline_repair_prompt,
)
from app.services.story.story_novel_continuity_contract import continuity_prompt
from app.services.story.story_novel_export_ai import TruncatedNovelOutput
from app.services.story.story_novel_invocation_evidence import GeneratedNovelText
from app.services.story.story_novel_plan_repair import plan_repair_prompt
from app.services.story.story_novel_planning_prompt import planning_prompt
from app.services.story.story_novel_prompt_renderer import (
    V3_PROMPT_TEMPLATES,
    prompt_template_evidence,
    v3_prompt_template_policy,
    valid_v3_prompt_template_policy,
)
from app.services.story.story_novel_thread_schedule import thread_schedule_prompt
from app.services.story.story_novel_thread_schedule_repair import (
    thread_schedule_repair_prompt,
)
from app.services.story.story_novel_v3_prompts import (
    chapter_audit_prompt,
    chapter_brief_prompt,
    format_repair_prompt,
    local_block_repair_prompt,
    prose_blocks_continuation_prompt,
    prose_blocks_prompt,
)


def test_v3_prompt_builders_render_through_versioned_prompt_manager_templates():
    prompts = [
        SYSTEM_PROMPT,
        structured_outline_prompt(
            story_seed={"outline": "四十八章长篇"}, expected_positions=[1, 2]
        ),
        structured_outline_repair_prompt("原任务", "无效输出", "缺少章节"),
        canon_prompt(planning_contract={"story_seed": {"title": "示例故事"}}),
        planning_prompt(planning_contract={}, canon={}, thread_payoffs=[]),
        plan_repair_prompt("原任务", "无效输出", "缺少章节", [1]),
        thread_schedule_prompt([]),
        continuity_prompt("窗口", {"chapters": []}, issue_limit=3),
        chapter_brief_prompt({"chapter_contract": {"position": 1}}),
        prose_blocks_prompt({"chapter_brief": {"beats": []}}),
        prose_blocks_continuation_prompt({}, [], ["B02"]),
        chapter_audit_prompt({"sentence_index": []}),
        local_block_repair_prompt({"failed_block_ids": ["B02"]}),
        format_repair_prompt("任务", "{", "invalid json"),
    ]

    for prompt in prompts:
        audit = prompt_template_evidence(prompt)
        assert audit["template"] in V3_PROMPT_TEMPLATES
        assert audit["version"] in {
            "1.0",
            "1.1",
            "1.2",
            "1.3",
            "1.4",
            "1.5",
            "1.6",
            "1.7",
            "1.8",
        }
        assert len(audit["sources_hash"]) == 64
        assert len(audit["rendered_hash"]) == 64


def test_proof_audit_prompt_allows_non_stateful_web_fiction_elaboration():
    prompt = chapter_audit_prompt({"sentence_index": []})

    assert "会改变 state_before 的计划外硬变化" in prompt
    assert "不得把不改变 expected_delta" in prompt
    assert "普通生活经验" in prompt
    assert "过往经历、日常能力" in prompt
    assert "未来事件的客观结果" in prompt
    assert "合理的自然时间流逝本身不是状态变化" in prompt
    assert "必须放入 future_hits" in prompt
    assert "同一项硬冲突若在全文多处出现" in prompt
    assert "sentence_ids 中列出全部相关句子" in prompt


def test_system_prompt_uses_stage_role_without_editorializing_prose():
    assert "叙事创作助手" in SYSTEM_PROMPT
    assert "规划、正文、审计或局部修订职责" in SYSTEM_PROMPT
    assert "不写成编辑报告" in SYSTEM_PROMPT
    assert "严谨的中文长篇叙事编辑" not in SYSTEM_PROMPT


def test_prose_and_repair_prompts_use_elastic_blocks_without_new_canon():
    prose = prose_blocks_prompt({"chapter_brief": {"beats": []}})
    repair = local_block_repair_prompt({"failed_block_ids": ["B01"]})

    assert "不是逐块硬门禁" in prose
    assert "每块必须完成不同的行动" in prose
    assert "current_chapter_context.events" in prose
    assert "events[].execution.actor_ids" in prose
    assert "scene_participants" in prose
    assert "typed_execution_boundary 是穷尽的当前章硬合同" in prose
    assert "action_phase=start 只能开始" in prose
    assert "不得自行补写可跨章延续的身世" in prose
    assert "length_action=compress" in repair
    assert "实际删去至少 required_removed_chars" in repair
    assert "先检查输入中的 rewrite_mode" in repair
    assert "expand_previous_replacements" in repair
    assert "compress_previous_replacements" in repair
    assert "compress_current_blocks" in repair
    assert "repair_previous_replacements" in repair
    assert "不得原样返回未通过预算的正文块" in repair
    assert "不得为补长度或修证据新增" in repair


def test_v3_prompt_policy_freezes_all_template_versions_and_hashes():
    policy = v3_prompt_template_policy()

    assert policy["schema"] == "story_novel_prompt_policy.v2"
    assert set(policy["templates"]) == set(V3_PROMPT_TEMPLATES)
    assert len(policy["hash"]) == 64
    assert {item["version"] for item in policy["templates"].values()} <= {
        "1.0",
        "1.1",
        "1.2",
        "1.3",
        "1.4",
        "1.5",
        "1.6",
        "1.7",
        "1.8",
    }
    assert policy["templates"]["story_novel_prose_blocks_v3"]["version"] == "1.7"


def test_v3_templates_are_discoverable_by_the_existing_prompt_api_manager():
    names = {item["name"] for item in prompt_manager.list_templates("story")}

    assert set(V3_PROMPT_TEMPLATES) <= names


def test_v1_prompt_policy_is_validated_from_its_frozen_snapshot():
    policy = v3_prompt_template_policy(version=1)

    assert valid_v3_prompt_template_policy(policy)
    policy["templates"]["story_novel_plan_v3"]["sources_hash"] = "changed"
    assert not valid_v3_prompt_template_policy(policy)


def test_batched_planning_prompt_keeps_template_evidence_and_prefix_in_hash():
    first = planning_prompt(
        planning_contract={},
        canon={},
        thread_payoffs=[],
        batch_positions=[1, 2],
        prefix_context={"validated_through_position": 0},
    )
    second = planning_prompt(
        planning_contract={},
        canon={},
        thread_payoffs=[],
        batch_positions=[3, 4],
        prefix_context={"validated_through_position": 2},
    )

    assert "精确 positions=[1,2]" in first
    assert prompt_template_evidence(first)["template"] == "story_novel_plan_v3"
    assert (
        prompt_template_evidence(first)["rendered_hash"]
        != prompt_template_evidence(second)["rendered_hash"]
    )


def test_thread_schedule_repair_uses_versioned_template():
    contract = [
        {
            "position": 1,
            "title": "启程",
            "goal": "调查异常",
            "open_threads": ["thread-rain"],
            "key_events": ["发现异常线索"],
            "end_state": "等待新消息",
        },
        {
            "position": 2,
            "title": "追踪",
            "goal": "找到答案",
            "open_threads": [],
            "key_events": ["找到线索来源"],
            "end_state": "问题得到回答",
        },
    ]
    prompt = thread_schedule_repair_prompt("调度无效", ["thread-rain"], contract, [])

    assert prompt_template_evidence(prompt)["template"] == (
        "story_novel_thread_schedule_repair_v3"
    )


def test_prose_template_keeps_raw_memory_event_and_future_catalog_out():
    safe_input = {
        "chapter_brief": {"beats": []},
        "visible_canon": {"entities": []},
        "chapter_length": {"min_chars": 2000, "target_chars": 2500, "max_chars": 3000},
    }
    prompt = prose_blocks_prompt(safe_input)
    surface = json.dumps(safe_input, ensure_ascii=False, separators=(",", ":"))

    assert surface in prompt
    for forbidden in ("world_events", "character_memories", "future_guard_index"):
        assert forbidden not in prompt


def test_prompt_template_audit_changes_with_rendered_input_not_template_source():
    first = prose_blocks_prompt({"x": 1})
    second = prose_blocks_prompt({"x": 2})

    first_audit = prompt_template_evidence(first)
    second_audit = prompt_template_evidence(second)
    assert first_audit["sources_hash"] == second_audit["sources_hash"]
    assert first_audit["rendered_hash"] != second_audit["rendered_hash"]


def test_task_generation_persists_and_binds_prompt_template_evidence(monkeypatch):
    prompt = prose_blocks_prompt({"chapter_brief": {"beats": []}})
    result = GeneratedNovelText("{}", {"invocation_id": 42})
    stored = []
    monkeypatch.setattr(
        story_novel_task_generation,
        "bind_invocation_prompt_template",
        lambda invocation_id, template: stored.append((invocation_id, template))
        or template,
    )

    story_novel_task_generation._bind_prompt_template(result, prompt)

    assert stored[0][0] == 42
    assert stored[0][1]["template"] == "story_novel_prose_blocks_v3"
    assert stored[0][1]["system_prompt"]["template"] == "story_novel_system_v3"
    assert result.invocation_evidence["prompt_template"] == stored[0][1]


@pytest.mark.asyncio
async def test_truncated_attempt_still_binds_user_and_system_prompt_templates(
    monkeypatch,
):
    prompt = prose_blocks_prompt({"chapter_brief": {"beats": []}})
    stored = []

    async def truncated(**_kwargs):
        raise TruncatedNovelOutput("length", "partial", {"invocation_id": 73})

    monkeypatch.setattr(
        story_novel_task_generation, "generate_story_novel_text", truncated
    )
    monkeypatch.setattr(
        story_novel_task_generation,
        "bind_invocation_prompt_template",
        lambda invocation_id, template: stored.append((invocation_id, template))
        or template,
    )
    revision = SimpleNamespace(
        business_id="revision-v3",
        model="deepseek:test",
        temperature=0.2,
        generation_plan={
            "model_policy": {
                "planning_model": "deepseek:test",
                "prose_model": "deepseek:test",
                "audit_model": "deepseek:test",
            }
        },
    )

    with pytest.raises(TruncatedNovelOutput):
        await story_novel_task_generation.generate_task_text(
            revision, prompt, max_tokens=16000, stage="prose.1"
        )

    assert stored[0][0] == 73
    assert stored[0][1]["template"] == "story_novel_prose_blocks_v3"
    assert stored[0][1]["system_prompt"]["template"] == "story_novel_system_v3"
