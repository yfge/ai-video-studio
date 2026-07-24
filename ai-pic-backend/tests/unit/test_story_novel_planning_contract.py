import pytest
from app.schemas.generation_requests import StoryNovelExportRequest
from app.services.story.story_novel_ai_prompts import canon_prompt, planning_prompt
from app.services.story.story_novel_planning_phases import _plan_repair_prompt
from app.services.story.story_novel_planning_service import planning_contract
from pydantic import ValidationError


def test_prose_ignores_legacy_limits_but_zhihu_keeps_them():
    prose = StoryNovelExportRequest(
        style="prose", target_words=999999, chapter_count=999
    )
    assert prose.target_words is None
    assert prose.chapter_count is None
    with pytest.raises(ValidationError):
        StoryNovelExportRequest(style="zhihu", target_words=999999)


def test_v2_planning_uses_confirmed_structured_outline_not_stale_outline_text():
    structured = {
        "status": "confirmed",
        "version": 7,
        "chapters": [{"position": 1, "title": "权威当前章"}],
    }
    contract = planning_contract(
        {
            "story_seed": {
                "schema": "story_seed_v2",
                "title": "故事",
                "premise": "前提",
                "outline": "LEGACY_STALE_OUTLINE",
                "outline_text": "STALE_CONTRADICTORY_TEXT",
                "structured_outline": structured,
                "ending_direction": "结局",
            }
        }
    )

    seed = contract["story_seed"]
    assert seed["structured_outline"] == structured
    assert seed["premise"] == "前提"
    assert seed["ending_direction"] == "结局"
    assert "outline" not in seed
    assert "outline_text" not in seed


def test_canon_prompt_separates_physical_location_from_object_ownership():
    prompt = canon_prompt(planning_contract={})
    assert "物件所有者必须写 owner_id" in prompt
    assert "禁止把角色 ID 写入 location" in prompt
    assert "entities.attributes 只允许年龄、职业、类型" in prompt
    assert "可变或未来字段一律写入 initial_state 的事件前值" in prompt
    assert "规则和里程碑只写入各自专用数组" in prompt
    assert "第1章任何事件发生前（position=0）" in prompt
    assert "不得把未来接收者、未来知识或未来伤势提前写入" in prompt
    assert "车厢、缆车或路线区段" in prompt
    assert "不得为了逐章对齐而每章都创建 milestone" in prompt
    assert "只是确认、验证或保持此前已经成立的状态" in prompt
    assert "临时权限的取得、到期或撤销只属于章节状态变化" in prompt
    assert "null→持有人→null 状态链" in prompt
    assert "status 应写 opened 或 verified" in prompt
    assert "owner_id eq null 重复写成 outcome" in prompt
    assert "只保留 planned_position 最早" in prompt
    assert "在 milestone 所在章结束后新变为真" in prompt
    chapter_prompt = planning_prompt(planning_contract={}, canon={})
    assert "required_event_ids 必须与 key_events 等长并按索引一一对应" in chapter_prompt
    assert "timeline_event_bindings 的 keys 必须精确等于" in chapter_prompt
    assert "禁止自行选择同章其他事件" in chapter_prompt
    assert "timeline_event_bindings={}" in chapter_prompt
    assert "不得假设未初始化的载具、地点或物件状态" in chapter_prompt
    assert "字段此前从未建立时写 null" in chapter_prompt
    assert "knowledge/contains 用授予 outcome.subject_id" in chapter_prompt
    assert "必须逐字节复用 Canon outcome" in chapter_prompt
    assert "主动公开身份的人" in chapter_prompt
    assert "只列本章新打开的线索" in chapter_prompt
    assert "绝不能重复携带" in chapter_prompt
    assert "to_location_id 必须是非空 Canon location ID" in chapter_prompt
    assert "物件于同章通过 status 从不存在变为存在" in chapter_prompt
    assert "人物、组织与普通旅行绝不能用 null 起点" in chapter_prompt
    assert "未来 milestone 的 location outcome" in chapter_prompt
    assert "即使随后离开再返回也算提前到达" in chapter_prompt
    assert "最后一章后的系统累计集合必须为空" in chapter_prompt
    assert "单章最多回收 3 条" in chapter_prompt
    assert "不接受计划外“自然得知”" in chapter_prompt
    assert "possessions 是物件 owner_id 的派生状态" in chapter_prompt
    assert "from_value 与 to_value 完全相同" in chapter_prompt
    assert "planned_position 指定章消费" in chapter_prompt


def test_plan_repair_clarifies_milestone_subject_and_thread_delta_semantics():
    repair = _plan_repair_prompt(
        "原始提示",
        '{"chapters":[]}',
        "里程碑结果未落地；计划存在未回收伏笔",
        [1, 2],
    )

    assert "主动公开身份的角色本人也必须授予" in repair
    assert "必须逐字节复制 outcome" in repair
    assert "open_threads 只保留本章新打开的 ID" in repair
    assert "终章 open_threads 必须为空" in repair
    assert "movement 的 to 必须是非空" in repair
    assert "Canon object 同章从不存在变为存在" in repair
    assert "人物与普通移动必须给出真实 Canon 起点" in repair
    assert "删除 planned_position 之前所有" in repair
    assert "先到达、离开、再返回" in repair
    assert "逐章重建 timeline_event_bindings" in repair
    assert repair.index("上一次完整但无效的输出") < repair.index(
        "必须修复的最终校验错误"
    )
    assert repair.endswith("修复完成后只返回一份完整、严格 JSON。")


def test_plan_repair_exposes_exact_milestone_and_global_thread_schedule():
    canon = {
        "milestones": [
            {
                "id": "mile-r17-sourced",
                "outcomes": [
                    {
                        "subject_id": "char-liyan",
                        "field": "knowledge",
                        "operator": "contains",
                        "value": "fact-r17-artificial-drought",
                    }
                ],
            }
        ]
    }
    frozen = {
        "chapters": [
            {
                "position": 1,
                "key_events": ["发现样本"],
                "open_threads": ["R-17 来自哪里"],
            },
            {
                "position": 2,
                "key_events": ["确认样本来源"],
                "open_threads": [],
            },
        ]
    }

    repair = _plan_repair_prompt(
        "原始提示",
        '{"chapters":[]}',
        "mile-r17-sourced 里程碑结果未落地",
        [1, 2],
        canon=canon,
        frozen_spec=frozen,
    )

    assert '"value":"fact-r17-artificial-drought"' in repair
    assert '"thread_ids":["R-17 来自哪里"]' in repair
    assert '"position":2,"thread_ids":[]' in repair
    assert '"thread_count":1' in repair
    assert '"authoritative_key_events"' in repair
    assert (
        '"terminal_payoff_capacity":{"key_events":["确认样本来源"],"max_payoffs":3,"position":2}'
        in repair
    )
    assert "每个 ID 必须且只能在更晚章节" in repair


def test_plan_repair_exposes_valid_canon_ids_and_timeline_sources():
    canon = {
        "timeline": [
            {
                "id": "time-8",
                "immutable": True,
                "source_chapter_position": 8,
                "source_key_event": "8月10日清晨货列离开澄砂港",
            }
        ],
        "entities": [{"id": "char-liyan"}],
    }

    repair = _plan_repair_prompt(
        "原始提示",
        '{"chapters":[]}',
        "第 8 章引用未知 Canon: ['canon-8']",
        list(range(1, 9)),
        canon=canon,
    )

    assert '"valid_canon_ids":["char-liyan","time-8"]' in repair
    assert '"timeline_id":"time-8"' in repair
    assert '"position":8' in repair
    assert "必须删除 canon-N 等占位符" in repair


def test_plan_repair_context_covers_all_48_chapter_thread_capacity():
    chapters = [
        {
            "position": position,
            "key_events": (
                ["第一场雨抵达", "风钥残片归档"]
                if position == 48
                else [f"事件-{position}"]
            ),
            "open_threads": [] if position == 48 else [f"thread-{position}"],
        }
        for position in range(1, 49)
    ]

    repair = _plan_repair_prompt(
        "原始提示",
        '{"chapters":[]}',
        "终章集中回收",
        list(range(1, 49)),
        frozen_spec={"chapters": chapters},
    )

    assert '"thread_count":47' in repair
    assert '"thread_ids":["thread-1"]' in repair
    assert '"thread_ids":["thread-47"]' in repair
    assert (
        '"terminal_payoff_capacity":{"key_events":["第一场雨抵达","风钥残片归档"],'
        '"max_payoffs":3,"position":48}' in repair
    )
