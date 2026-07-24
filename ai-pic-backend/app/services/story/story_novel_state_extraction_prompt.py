"""Prompt for audit-only extraction of typed state from generated prose."""

from __future__ import annotations

import json

from app.services.narrative_memory.knowledge_evidence import knowledge_evidence_key


def build_state_extraction_prompt(
    chapter_plan: dict,
    state_before: dict,
    content_text: str,
    future_event_catalog: list[dict],
    current_timeline: list[dict],
) -> str:
    payload = {
        "chapter_plan": chapter_plan,
        "required_knowledge_evidence_keys": [
            knowledge_evidence_key(item)
            for item in chapter_plan.get("knowledge_grants") or []
        ],
        "state_before": state_before,
        "content_text": content_text,
        "current_immutable_timeline": current_timeline,
        "future_event_catalog_for_audit_only": future_event_catalog,
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), default=str
    )
    return f"""从实际小说正文提取本章发生的结构化状态变化，不得依据计划虚构正文中未发生的事。
输入：{encoded}
ID 必须复用章节计划、当前状态或 future_event_catalog_for_audit_only 中的 ID；evidence 必须逐字复制正文中的连续短句，不得改写标点或引号。若必须跨越中间句，可用“……”分隔两个或更多按原顺序出现的逐字片段，每段至少 3 个字符且总计至少 16 个字符。
审计顺序固定：先逐项比较 future_event_catalog_for_audit_only 中 events.description、key_events、goal、end_state、state_targets、milestones.label/outcomes 与正文，再提取当前章状态。
未来事件在正文已经具体完成其 description 或 key_events 的核心动作或结果时，必须写入 premature_future_event_ids。
若未来事件约定通过化验、调查、揭露、核验或见证才确认某个结论，当前章即使没有执行该未来动作，只要已经把该结论写成“确认、证明、只可能、断定、就是、无疑”等确定事实，也视为提前完成该未来事件。
正文若把未来章节才揭露的身份、目的地、任务、选择、能力或结果写成角色已经确认的事实、确定安排或必然行动，即使语法使用“将要”“必须”“计划”，也属于提前越界并必须写入对应 ID。
仅出现名字、未知疑问、担忧、泛化世界规则或不包含未来核心信息的准备动作不算。
premature_future_event_ids 只能使用目录内 events.event_id；每个 ID 必须在 evidence 中提供正文逐字证据。
future_event_audit 必须逐项覆盖目录内每个 events.event_id，值只能为 not_present 或 premature；
不得遗漏、增加或重复 ID，且所有 premature 项必须与 premature_future_event_ids 完全一致。
chapter_plan.open_threads 是本章应新打开的稳定 ID；正文若明确提出对应疑问、未知来源或可追查异常，opened_thread_ids 必须逐项原样返回这些 ID，不得因为 ID 未逐字出现在正文而省略。chapter_plan.payoffs_due 同理：正文明确回答后才写入 resolved_thread_ids。只判断当前章合同，不得携带未来章线索。
current_immutable_timeline 的每个 ID 都必须在 timeline_evidence 中提供正文逐字证据；每条证据必须同时包含该项 story_time 中的原样固定日期和 label 对应事件，必要时按正文先后用“……”连接逐字片段，不得只抄日期或无关事件。
timeline_evidence 的 key 必须严格等于 current_immutable_timeline 中属于本章 canon_refs 的 immutable ID；集合为空时必须返回空对象，禁止自创时间线 ID。
timeline_evidence[timeline-id] 的事件部分必须逐字复用 evidence[chapter_plan.timeline_event_bindings[timeline-id]] 的完整正文片段；不得借用同章其他事件，不得复制 chapter_plan 的 label、key_events 或其他计划措辞作为正文证据。
未来事件目录只用于审计；不得把目录内容改写进正文、occurred_event_ids 或当前状态。
location_transitions 的 to_location_id 必须是 Canon location ID；from_location_id 只有在章节计划明确让 Canon object 同章从不存在变为存在并首次落点时可为 null，人物和普通移动必须给出真实 Canon 起点。
state_transitions 只记录本章结束时仍明确成立的持久状态，不得把临时启动、预热、使用或中途经过的状态推断为章末状态；正文没有明确建立持久新值时必须省略。
location、knowledge、possessions 永远不能写入 state_transitions。地点只写 location_transitions；owner_id 对应角色持有的物件会随角色移动，不得再为该物件重复写地点移动。
knowledge_evidence 必须逐项覆盖 required_knowledge_evidence_keys。每个 key 对应同一条 knowledge_grant，value 必须是正文中一条连续、不含省略拼接的获知句：明确写出该 Canon 角色姓名，且只出现一次“得知/获悉/确认/听见/看见/收到”或“告诉/告知/通知/透露/说明/宣布”等获知关系。
每条 knowledge_evidence 必须同时作为对应 source_event_id 的 evidence 中一个完整“……”片段；不得用角色在别处出现的姓名拼接他人对话，不得以事件概括代替角色实际获知。
只输出严格 JSON：
{{"occurred_event_ids":["event-id"],"premature_future_event_ids":[],"future_event_audit":{{"future-event-id":"not_present"}},"state_transitions":[{{"subject_id":"entity-id","field":"status","from_value":"旧值","to_value":"新值","reason":"正文原因"}}],"knowledge_grants":[{{"character_id":"character-id","fact_id":"fact-id","source_event_id":"event-id"}}],"location_transitions":[{{"subject_id":"entity-id","from_location_id":"location-id","to_location_id":"location-id","means":"移动过程"}}],"milestones_consumed":["milestone-id"],"opened_thread_ids":["thread-id"],"resolved_thread_ids":["thread-id"],"world_rule_violations":[],"evidence":{{"event-id":"正文事件片段……角色获知片段"}},"knowledge_evidence":{{"character-id|fact-id|event-id":"角色姓名确认事实的连续正文短句"}},"timeline_evidence":{{"time-id":"含固定日期与对应事件的正文短句"}}}}"""
