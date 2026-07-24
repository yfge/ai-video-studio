"""Prompt contract for event-by-event chapter-plan semantic audits."""

from __future__ import annotations

from .story_novel_canon_service import canonical_json
from .story_novel_planning_batches import validated_prefix_context

EFFECT_FIELDS = (
    "knowledge_grants",
    "state_transitions",
    "location_transitions",
    "milestones_consumed",
)


def build_plan_semantic_audit_prompt(
    contract: dict,
    canon: dict,
    prior_chapters: list[dict],
    batch_chapters: list[dict],
) -> str:
    positions = [int(item["position"]) for item in batch_chapters]
    event_contract = [
        {
            "position": int(chapter["position"]),
            "event_id": event_id,
            "key_event": (chapter.get("key_events") or [])[index],
        }
        for chapter in batch_chapters
        for index, event_id in enumerate(chapter.get("required_event_ids") or [])
    ]
    output_skeleton = {
        "events": [
            {
                "position": item["position"],
                "event_id": item["event_id"],
                "missing_effects": {field: [] for field in EFFECT_FIELDS},
            }
            for item in event_contract
        ]
    }
    payload = {
        "event_contract": event_contract,
        "output_skeleton": output_skeleton,
        "state_before_batch": validated_prefix_context(canon, prior_chapters)["state"],
        "canon_entities": [
            {"id": item["id"], "kind": item["kind"], "name": item["name"]}
            for item in canon.get("entities") or []
        ],
        "canon_milestones": canon.get("milestones") or [],
        "prior_chapters": [
            {
                "position": item["position"],
                "key_events": item.get("key_events") or [],
                "knowledge_grants": item.get("knowledge_grants") or [],
            }
            for item in prior_chapters
        ],
        "chapters": [
            {
                key: item.get(key)
                for key in (
                    "position",
                    "key_events",
                    "character_focus",
                    "required_event_ids",
                    *EFFECT_FIELDS,
                )
            }
            for item in batch_chapters
        ],
        "story_constraints": {
            key: (contract.get("story_seed") or {}).get(key)
            for key in ("world_constraints", "content_constraints")
        },
    }
    return (
        "独立审计章节计划中的长期知识与状态效果，不得相信计划自报完整性。"
        f"\npositions={positions}；逐项审查 event_contract 中每个事件。"
        "\n必须逐字复制 input.output_skeleton 的 position、event_id、数量和顺序；"
        "只能填写各 missing_effects 数组，禁止合并为每章一项或自造 event_id。"
        "\n凡事件会让角色确认、获知、宣布、发现、判断或长期记住新事实，"
        "必须列出遗漏的 knowledge_grants；说话者本人和必然听见的在场者都不能漏。"
        "“怀疑”不得升级成“确认”。普通动作、气氛和既有事实不要生成长期知识。"
        "\n非 Canon milestone 的新知识 fact_id 固定为 "
        "fact-{source_event_id}-{从1开始的事实序号}；同一事实对多个角色复用同一 fact_id。"
        "Canon milestone knowledge outcome 必须逐字使用 outcome.value。"
        "\n同时列出 key_event 必然要求但计划遗漏的 state_transitions、"
        "location_transitions 与 milestones_consumed；地点转移只允许明确跨越两个"
        "不同的已有 location ID，地点内部移动必须为空且不得创建子地点；只返回遗漏项。"
        "\n只输出填充后的 input.output_skeleton 严格 JSON，不得缺失、额外或重复。"
        f"\n输入：{canonical_json(payload)}"
    )
