"""Bounded provider repair prompt for an invalid compiled Canon."""

from __future__ import annotations

from app.utils.json_utils import extract_json_block

from .story_novel_canon_service import canonical_json


def canon_repair_prompt(prompt: str, text: str, error: str | None) -> str:
    payload = extract_json_block(text) or {}
    error_text = str(error or "")
    milestones = payload.get("milestones") or []
    failing = [
        item for item in milestones if item.get("id") and str(item["id"]) in error_text
    ]
    initial_state_error = any(
        marker in error_text for marker in ("初始状态", "状态提前")
    )
    preserve_initial = None if initial_state_error else payload.get("initial_state")
    repair_context = {
        "failing_milestones": failing,
        "delete_milestone_ids": _milestones_empty_after_dedup(milestones, error_text),
        "preserve_initial_state_exactly": preserve_initial,
        "existing_milestone_ids": [item["id"] for item in milestones if item.get("id")],
    }
    previous_canon = canonical_json(payload) if payload else text
    return (
        prompt
        + "\n\n上一次 Canon 无效或被截断，请只修复并完整重输一次。"
        + "\n所有字符串保持一句话，数组只保留会约束后文的项目。"
        + "\n禁止新增、拆分、改名或顺带重写未报错的 milestone；临时权限的取得与到期不得创建 milestone。"
        + "\n逐项复核所有 future outcomes：eq 的初态值必须不相等，"
        + "contains 的初态数组必须不包含该值。"
        + "\n校验错误中的重复 outcome 必须只保留 planned_position 最早的一条，"
        + "从所有更晚 milestone 删除完全相同的 subject_id/field/operator/value。"
        + "\nrepair_context.delete_milestone_ids 中每个 ID 都必须从 milestones 数组整条删除，"
        + "禁止只清空 outcomes 后保留空 milestone。"
        + "\n若报错 outcome 只是重复一个始终成立的 owner_id、location 或权限值，删除该冗余 outcome；"
        + "若它确实表达变化，则按 StorySeed 明示事实修正事件前初态。"
        + "\n去重后 outcomes 为空的 milestone 必须整条删除，禁止保留空数组。"
        + "\n对 owner_id eq null 的状态提前错误：若更早 milestone 已明确把 null 改给持有人，保留完整状态链；"
        + "否则销毁物件把初态改为明示来源所有者，普通归档物件删除冗余 owner_id outcome。"
        + "\n任何状态提前错误若来自 entity.attributes，必须删除其中的未来字段，并在 initial_state 写事件发生前的真实值。"
        + "\n若 repair_context 给出 preserve_initial_state_exactly，"
        + "必须逐字段原样复制该干净初态，不得重新推演。"
        + "\nnull、[]、{} 必须是 JSON 字面量，不能加引号。"
        + f"\n校验错误：{error}"
        + f"\nrepair_context：{canonical_json(repair_context)}"
        + f"\n上一次完整 Canon：{previous_canon}"
    )


def _milestones_empty_after_dedup(milestones: list[dict], error_text: str) -> list[str]:
    seen: set[str] = set()
    delete_ids: list[str] = []
    ordered = sorted(
        enumerate(milestones),
        key=lambda item: (
            item[1].get("planned_position") is None,
            item[1].get("planned_position") or 0,
            item[0],
        ),
    )
    for _index, milestone in ordered:
        milestone_id = str(milestone.get("id") or "")
        outcomes = milestone.get("outcomes") or []
        signatures = [canonical_json(item) for item in outcomes]
        if milestone_id in error_text and (
            not signatures or all(signature in seen for signature in signatures)
        ):
            delete_ids.append(milestone_id)
        seen.update(signatures)
    return delete_ids
