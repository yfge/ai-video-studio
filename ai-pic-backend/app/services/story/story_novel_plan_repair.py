"""One-shot repair prompt for executable long-form chapter contracts."""

from __future__ import annotations

from app.utils.json_utils import extract_json_block

from .story_novel_canon_service import canonical_json
from .story_novel_initial_state import canonical_initial_subjects
from .story_novel_location_rules import (
    ABSENT_OBJECT_STATUS_LITERALS,
    TERMINAL_OBJECT_STATUS_LITERALS,
)
from .story_novel_plan_refs import known_canon_ids


def plan_repair_prompt(
    prompt: str,
    text: str,
    error: str | None,
    expected_positions: list[int],
    *,
    canon: dict | None = None,
    frozen_spec: dict | None = None,
    thread_payoffs: list[dict] | None = None,
) -> str:
    coverage = (
        f"\n本批次显式列出第{expected_positions[0]}章至第{expected_positions[-1]}章；"
        "修复结果必须逐章完整覆盖，不能合并、省略或新增。"
        if expected_positions
        else ""
    )
    context = _repair_context(
        text, error, canon or {}, frozen_spec or {}, thread_payoffs
    )
    absence_literals = "、".join(
        f'"{value}"' for value in ABSENT_OBJECT_STATUS_LITERALS
    )
    terminal_literals = "、".join(
        f'"{value}"' for value in TERMINAL_OBJECT_STATUS_LITERALS
    )
    return (
        prompt
        + f"\n\n上一次完整但无效的输出：{text}"
        + "\n\n上一次规划无效或被截断，请只修复并完整重输一次。"
        + coverage
        + "\n为避免再次截断，每个字符串字段保持一句话，数组只保留必要条目。"
        + "\n只修改校验错误关联字段；但全书 open_threads/payoffs_due 必须按 "
        "repair_context 全量重建，不受此限制。knowledge/location 不能写 "
        "state_transitions；knowledge/location 都不能写 state_transitions，"
        "分别只用 knowledge_grants/location_transitions。"
        + "角色 possessions 是物件 owner_id 的派生状态，禁止直接写 possessions "
        "state_transition；物件转交只写物件 owner_id，系统会更新双方 possessions。"
        "所有 from_value 与 to_value 完全相同的 no-op transition 必须删除。"
        + "\n逐章核对 knowledge_grants：同章 source_event_id 必须加入该章 required_event_ids，"
        "且必须是当前章实际发生并传达该事实的事件；required_event_ids 必须覆盖每一项 key_events。"
        + "\n逐章 key_events 必须逐字、逐项、同序复制 "
        "repair_context.authoritative_key_events；禁止重排后沿用旧 required_event_ids。"
        + "\n逐章重建 timeline_event_bindings：keys 必须精确等于 canon_refs 中的 "
        "immutable timeline IDs，values 必须是本章 required_event_ids；"
        "canon_refs 只能逐字复制 repair_context.valid_canon_ids，必须删除 canon-N "
        "等占位符与所有未知 ID；按 repair_context.timeline_contracts 在来源章加入精确 timeline ID；"
        "每个 timeline 只能在 source_chapter_position 指定章引用，"
        "source_key_event 必须逐字命中本章唯一 key_event，并绑定该 key_event"
        "同索引的 required_event_id，禁止自行选择同章其他事件。"
        "没有 timeline 引用时也必须输出空 object。"
        + "\n从 Canon initial_state 开始逐章重放所有 subject/field；"
        + "precondition 与 from_value 必须等于当时已知值。"
        + "若字段此前不存在，删除该 precondition，并把 transition.from_value 写为 null；"
        + "同一错误涉及的 precondition 与 transition 必须一起修正。"
        + "地点 precondition 也必须等于按前章 movement 重放出的当前地点；若 key_event "
        "不要求该角色在所写地点，就删除无来源的地点 precondition，禁止凭空补旅程来迁就错误前置。"
        + "\nrepair_context.authoritative_initial_state 是 position=0 的精确完整状态；"
        + "其中未出现的 subject/field 就是未定义，禁止补默认值。"
        + "其中已经定义的空数组 [] 是精确旧值，不是未定义；precondition.value 与 "
        "transition.from_value 必须保留 []，绝不能改成 null。"
        + "\n逐个重放 consumed milestone 的 Canon outcomes；"
        + "repair_context.failing_milestones 与 consumed_milestone_contracts "
        "都是必须逐字节落实的权威值。"
        + "repair_context.milestone_outcome_contracts 覆盖全部已排期不可逆 milestone；逐项确认 "
        "planned_position 当章消费 ID，并用精确 field/operator/value 落地全部 outcomes，"
        "禁止漏消费或改写值，例如 opened 不能改成已开启。"
        + "必须逐字节复制 outcome；knowledge/contains 给 outcome.subject_id 添加 "
        "knowledge_grant，主动公开身份的角色本人也必须授予；"
        + "location/eq 写 movement，其余写 state_transition。"
        + "planned_position 为 null 的不可逆 milestone 是未排期目录项，禁止消费。"
        + "\n若错误指出状态提前包含未来 location outcome，删除 planned_position 之前所有"
        "以该 outcome.value 为 to_location_id 的 movement，并从最近合法地点重算后续起点；"
        "禁止用先到达、离开、再返回规避，跨桥或启程不等于提前抵达后文地点。"
        + "\nopen_threads 只保留本章新打开的 ID。先在内部建立全书伏笔表，再输出 "
        "JSON：逐章 open_threads 必须逐项复制 "
        "repair_context.thread_openings；若 authoritative_thread_payoffs 非 null，"
        "payoffs_due 必须逐章精确复制该权威调度，禁止重排；否则每个未回收 ID "
        "都必须按 repair_context.payoff_capacity 分散到真正解决它的章节。"
        "每个 ID 必须且只能在更晚章节出现一次，严禁集中到终章；终章 open_threads 必须为空，"
        "最终累计集合必须为空。"
        + "\n正文会产生的长期事实必须给实际知情角色编入 knowledge_grants；"
        + "包括公开期限、身份、权限、物件状态与因果结论，不能留给运行时补猜。"
        + "\nnull、数组与对象必须使用真实 JSON 类型；movement 的 to 必须是非空 "
        "Canon location ID；from 仅在 Canon object 同章从不存在变为存在且首次落点时可为 null，"
        "人物与普通移动必须给出真实 Canon 起点；角色已在该地点或只是首次出场时删除 movement。"
        + f"\n不存在只认这 7 个精确 status 字面值：{absence_literals}。null、缺失 "
        "status，以及“未发现”“未找到”“未签发”“未采集”均表示对象已存在或状态未定义，"
        "绝不能据此输出 null 起点 movement。逐项读取 "
        "repair_context.unlocated_object_initial_states 的精确 status/owner/location 定义。"
        + "null 起点还要求 Canon 初态与本章起始 status 都命中允许值，本章对该物件恰有一个"
        "从精确起始值到非不存在、非空、非终止值的 status transition，transition.reason "
        f"必须非空；终止值包括 {terminal_literals}。且恰有一个 location transition；"
        "任一条件不满足就省略 movement。"
        + "\n已存在但地点未知的物件，只有 key_event 明确发生真实所有权转移时，才可用 "
        "owner_id state_transition 从精确旧 owner_id 转到实际接收者，并省略 location_transition；"
        "否则保持地点未知并省略 movement，禁止猜测落点或接收者。"
        + f"\nrepair_context：{canonical_json(context)}"
        + f"\n必须修复的最终校验错误：{error}"
        + "\n不要复读上一次输出；修复完成后只返回一份完整、严格 JSON。"
    )


def _repair_context(
    text: str,
    error: str | None,
    canon: dict,
    frozen_spec: dict,
    thread_payoffs: list[dict] | None,
) -> dict:
    payload = extract_json_block(text) or {}
    initial_state = canonical_initial_subjects(canon)
    object_ids = {
        item["id"]
        for item in canon.get("entities") or []
        if item.get("id") and item.get("kind") == "object"
    }
    unpositioned_once = {
        item["id"]
        for item in canon.get("milestones") or []
        if item.get("id")
        and not item.get("repeatable")
        and "planned_position" in item
        and item.get("planned_position") is None
    }
    source = list(frozen_spec.get("chapters") or payload.get("chapters") or [])
    consumed_ids = {
        milestone_id
        for item in payload.get("chapters") or []
        for milestone_id in item.get("milestones_consumed") or []
    }
    failing = [
        item
        for item in canon.get("milestones") or []
        if item.get("id")
        and str(item["id"]) in str(error or "")
        and (
            item.get("repeatable")
            or item.get("planned_position") is not None
            or "planned_position" not in item
        )
    ]
    openings = [
        {
            "position": int(item["position"]),
            "thread_ids": list(item.get("open_threads") or []),
        }
        for item in source
    ]
    capacity = [
        {
            "position": int(item["position"]),
            "max_payoffs": 3,
            "key_events": list(item.get("key_events") or []),
        }
        for item in source
    ]
    terminal = capacity[-1] if capacity else None
    return {
        "failing_milestones": failing,
        "consumed_milestone_contracts": [
            item
            for item in canon.get("milestones") or []
            if item.get("id") in consumed_ids
            and (
                item.get("repeatable")
                or item.get("planned_position") is not None
                or "planned_position" not in item
            )
        ],
        "milestone_outcome_contracts": [
            {
                "id": item["id"],
                "planned_position": item.get("planned_position"),
                "outcomes": item.get("outcomes") or [],
            }
            for item in canon.get("milestones") or []
            if item.get("id")
            and not item.get("repeatable")
            and (
                item.get("planned_position") is not None
                or "planned_position" not in item
            )
        ],
        "valid_canon_ids": sorted(known_canon_ids(canon) - unpositioned_once),
        "timeline_contracts": [
            {
                "position": int(item.get("source_chapter_position") or 0),
                "timeline_id": item["id"],
                "source_key_event": item.get("source_key_event"),
            }
            for item in canon.get("timeline") or []
            if item.get("immutable") and item.get("id")
        ],
        "authoritative_initial_state": initial_state,
        "object_location_contract": {
            "absence_status_literals": list(ABSENT_OBJECT_STATUS_LITERALS),
            "non_absence_status_examples": ["未发现", "未找到", "未签发", "未采集"],
        },
        "state_value_contract": {
            "undefined_field_from_value": None,
            "defined_empty_array_from_value": [],
            "copy_authoritative_values_without_coercion": True,
        },
        "derived_state_contract": {
            "possessions": "derived_from_object_owner_id_never_transition_directly"
        },
        "unlocated_object_initial_states": [
            {
                "subject_id": subject_id,
                "status": initial_state[subject_id].get("status"),
                "status_is_defined": "status" in initial_state[subject_id],
                "owner_id": initial_state[subject_id].get("owner_id"),
                "owner_id_is_defined": "owner_id" in initial_state[subject_id],
                "location": initial_state[subject_id].get("location"),
                "location_is_defined": "location" in initial_state[subject_id],
            }
            for subject_id in sorted(object_ids)
            if subject_id in initial_state
            and initial_state[subject_id].get("location") is None
        ],
        "authoritative_key_events": [
            {
                "position": int(item["position"]),
                "key_events": list(item.get("key_events") or []),
            }
            for item in source
        ],
        "authoritative_thread_payoffs": thread_payoffs,
        "thread_openings": openings,
        "thread_count": sum(len(item["thread_ids"]) for item in openings),
        "payoff_capacity": capacity,
        "terminal_payoff_capacity": terminal,
    }
