"""Prompt for Canon-backed long-form chapter contract planning."""

from __future__ import annotations

from typing import Any

from .story_novel_domain import json_prompt_payload
from .story_novel_location_rules import (
    ABSENT_OBJECT_STATUS_LITERALS,
    TERMINAL_OBJECT_STATUS_LITERALS,
)


def planning_prompt(
    *,
    planning_contract: dict[str, Any],
    canon: dict,
    thread_payoffs: list[dict] | None = None,
) -> str:
    absence_literals = "、".join(
        f'"{value}"' for value in ABSENT_OBJECT_STATUS_LITERALS
    )
    terminal_literals = "、".join(
        f'"{value}"' for value in TERMINAL_OBJECT_STATUS_LITERALS
    )
    schedule = (
        "未提供冻结伏笔调度，按章节合同自行规划。"
        if thread_payoffs is None
        else "以下机器校验后的 thread_payoffs 是唯一权威，逐章 payoffs_due 必须按 "
        "payoff_position 精确复制 thread_id，不得遗漏、重排或另行推断："
        f"{json_prompt_payload(thread_payoffs)}"
    )
    return f"""仅根据冻结的 StorySeed、人物与世界约束规划一部长篇小说。
规划合同：{json_prompt_payload(planning_contract)}
唯一 Canon：{json_prompt_payload(canon)}
伏笔回收调度：{schedule}
大纲必须唯一决定有限且完整的章节数量；不得按预设总字数凑章，也不得省略大纲阶段。
若大纲显式列出连续章节编号，必须逐章对应，禁止合并、省略或新增。
每章目标必须在 3000–5000 个非空白中文字符之间。
每章必须声明稳定且全书唯一的 required_event_ids，以及可机器校验的前置状态和状态变化。
每章 key_events 必须逐字、逐项、按原顺序复制冻结 structured_outline 当前章；不得概括、改写或重排，否则事件 ID 与知识来源无法安全绑定。
required_event_ids 必须与 key_events 等长并按索引一一对应：第 i 个 required_event_id 是第 i 个 key_event 的稳定 ID；同章 knowledge_grants 的每个 source_event_id 也必须出现在该章 required_event_ids 中。
每章 timeline_event_bindings 的 keys 必须精确等于该章 canon_refs 中的 immutable timeline IDs，values 必须是本章 required_event_ids。
canon_refs 的每个值都必须逐字取自唯一 Canon 的现有 ID，禁止输出 canon-1、canon-N 等占位符或任何未知 ID；每个 immutable timeline ID 必须只加入其 source_chapter_position 指定章。
每个 timeline 只能在 source_chapter_position 指定章引用；其 source_key_event 必须逐字等于本章唯一一条 key_event，binding value 必须是该 key_event 同索引的 required_event_id，禁止自行选择同章其他事件。
运行时 timeline_evidence[timeline-id] 只允许复用 evidence[timeline_event_bindings[timeline-id]] 的完整正文逐字证据。
没有 immutable timeline 引用的章节也必须输出空 object timeline_event_bindings={{}}。
preconditions 只能断言 Canon initial_state 或更早章节已经建立的值；不得假设未初始化的载具、地点或物件状态。
state_transitions.from_value 必须等于当时已知值；字段此前从未建立时写 null，且不要为该未知值添加 precondition。Canon 中已经定义的空数组 [] 是精确旧值，不是未定义，from_value 必须逐字使用 []，绝不能改成 null。
知识授予的 source_event_id 必须是当章 required_event_ids 中实际传达、阅读或揭示该事实的事件；不得直接复用早先章节的事件 ID。地点移动必须写明起点、终点和过程。
knowledge 只能通过 knowledge_grants 增加，禁止在 state_transitions 中重复写 knowledge 字段。
地点只写入 location_transitions，不要在 state_transitions 重复 location 变化。
角色 possessions 是物件 owner_id 的派生状态，绝不能写入 state_transitions；物件转交只写该物件的 owner_id transition，系统会原子更新旧、新持有者 possessions。任何 from_value 与 to_value 完全相同的 transition 都是非法 no-op，必须省略。
只有真实发生地点变化时才写 location_transitions；人物已在本章起点地点时不要输出 null 起点或原地移动。
location_transitions 的 to_location_id 必须是非空 Canon location ID；from_location_id 仅在 Canon kind=object 的物件于同章通过 status 从不存在变为存在、且此前没有地点时可写 null，人物、组织与普通旅行绝不能用 null 起点；角色在既有地点首次出场不算移动，直接省略该 transition。
“不存在”只认这 7 个精确 status 字面值：{absence_literals}。null、缺失 status，以及“未发现”“未找到”“未签发”“未采集”都不表示对象不存在；这些对象即使 location 为 null 也已经存在，绝不能输出 null 起点 movement。
null 起点首次落点还必须同时满足：Canon 初态与本章起始 status 都是上述允许值，本章对该物件恰有一个从精确起始值到非不存在、非空、非终止值的 status transition，reason 必须非空；终止值包括 {terminal_literals}。且恰有一个 location transition；任一条件不满足就省略 movement。
已存在但地点未知的物件若在当前 key_event 中明确交给某个实际接收者，只能用 owner_id state_transition 从精确旧 owner_id 转到该接收者，并省略 location_transition；接收者地点会确定物件地点。若当前事件没有明确所有权转移，则保持地点未知并省略 movement，禁止猜测落点或接收者。
location_transitions 的起终点只能引用 Canon kind=location 的 ID；跨章旅途必须使用 Canon 已注册的车厢、缆车或路线区段，禁止自造 en-route ID。
未来 milestone 的 location outcome 在其 planned_position 之前绝不能成为任何 movement 的终点，即使随后离开再返回也算提前到达；跨桥、启程或进入途中不等于抵达后文地点，若 Canon 没有更精确中间地点就保持最近合法地点或省略伪造移动。
已设 planned_position 的不可逆 milestones 只能在 Canon 指定章节消费一次；planned_position 为 null 的不可逆 milestone 是未排期目录项，任何章都不得消费。forbidden_event_ids 列出不得重演的旧事件。
每个已排期不可逆 milestone 必须在 planned_position 指定章消费并逐项落实其精确 outcomes；不得漏消费，也不得把字段或值改成近义表达，例如 Canon status 为 "opened" 就只能写 "opened"。
消费 milestone 的当章 typed effects 必须令该 milestone 的全部 outcomes 成立；任何更晚 milestone 的 outcomes 在当前章后仍不得成立。
逐项把 consumed milestone outcomes 编译到 typed effects：knowledge/contains 用授予 outcome.subject_id 的 knowledge_grants，location/eq 用 location_transitions，其余字段用 state_transitions；不得只写在 key_events 或摘要。
typed effect 的 fact_id、subject_id、field 和 value 必须逐字节复用 Canon outcome，禁止创建近义 ID、翻译 ID 或改写值。
即使 knowledge outcome 的 subject_id 是当章主动公开身份的人，也必须给该 subject_id 本人添加对应 knowledge_grant；不能只授予旁观者。
preconditions、state_transitions 和 outcomes 必须保留真实 JSON 类型：空值写 null，数组写 []，禁止写成字符串 "null"、"[]" 或嵌套 JSON 字符串。
冻结 structured_outline 中每章 open_threads 已是稳定 ID；必须逐项、按原顺序、原样复制，数量也必须一致，禁止翻译或另造近义 ID。只列本章新打开的线索，绝不能重复携带此前章节累计集合。
payoffs_due 只能引用此前章节已经打开的 ID；一旦 key_events 已解决某条线索，必须在该章 payoffs_due 精确填入其 ID。同一 key_event 确实同时回答多条语义相关线索时可以共享，单章最多回收 3 条；禁止把未规划回收位置的线索集中堆到终章。终章不得新开线索，最后一章后的系统累计集合必须为空。
凡 key_events 会让任何角色获知新的长期事实（包括公开宣布的期限、身份、权限、物件状态或因果结论），都必须为实际知情角色逐项编入 knowledge_grants；运行时不接受计划外“自然得知”。
非 Canon milestone outcome 的新知识 fact_id 必须按 source_event_id 稳定派生为 fact-{{source_event_id}}-{{从1开始的事实序号}}；同一事实对多个角色复用同一 fact_id。计划完成后系统会逐事件独立语义审计，遗漏 typed effect 将在正文前失败。
只输出严格 JSON：
{{"chapters":[{{"position":1,"title":"标题","goal":"情节目标","key_events":["关键事件"],"character_focus":["角色重点"],"open_threads":["thread-id"],"end_state":"章末状态","target_chars":4000,
"preconditions":[{{"subject_id":"entity-id","field":"status","operator":"eq|ne|contains|not_contains","value":"值"}}],
"required_event_ids":["event-id"],"timeline_event_bindings":{{"time-id":"event-id"}},"state_transitions":[{{"subject_id":"entity-id","field":"status","from_value":"旧值","to_value":"新值","reason":"原因"}}],
"knowledge_grants":[{{"character_id":"character-id","fact_id":"fact-id","source_event_id":"event-id"}}],
"location_transitions":[{{"subject_id":"entity-id","from_location_id":"location-id","to_location_id":"location-id","means":"移动过程"}}],
"milestones_consumed":["milestone-id"],"forbidden_event_ids":["旧event-id"],"payoffs_due":["thread-id"],"canon_refs":["canon-id"]}}]}}
position 必须从 1 连续编号；章节列表必须覆盖整个大纲直至结局方向。"""
