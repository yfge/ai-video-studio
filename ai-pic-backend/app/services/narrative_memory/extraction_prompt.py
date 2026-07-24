"""Prompt for source-grounded Narrative Event and Character Memory extraction."""

from __future__ import annotations

import json


def build_extraction_prompt(source_text, characters, anchors, contract=None) -> str:
    contract = contract or {}
    return f"""从来源正文提取客观事件和每个角色的主观记忆候选。
角色白名单：{json.dumps(characters, ensure_ascii=False)}
可用锚点：{json.dumps([{"business_id": a.business_id, "source": a.source_artifact_business_id} for a in anchors], ensure_ascii=False)}
当前章 typed extraction contract：{json.dumps(contract, ensure_ascii=False)}
严格区分：客观事件、角色获知/信念、观众显隐。离场发生用 presentation=offscreen；不要把潜台词写成长期记忆。
只保留会影响后续连续性、知情边界、关系、能力或世界规则的增量；忽略重复信息、气氛描写、普通动作和逐句对话。
硬性控制输出规模：events 最多 8 条；无 typed contract 时 memories 总计最多 6 条，有 typed contract 时 memories 数量必须逐项覆盖 required_memory_grants，不得因数量省略；summary、content、belief、perception 各字段都用一句简洁中文。
角色没有获得新的长期认知时不要为其创建 memory；允许 events 或 memories 为空数组。
若 typed extraction contract 非空，events 必须逐项覆盖 event_evidence：每条只填一个对应 typed_event_ids，evidence 必须逐字等于该 ID 的 event_evidence；不得用正文中的其他真实动作替代。
此时 events 数量必须精确等于 event_evidence 数量，不得添加 typed_event_ids 为空、重复、未知或绑定多个 ID 的额外事件。
memories 必须逐项覆盖 required_memory_grants：每条只绑定一个 typed_character_id + typed_fact_id + typed_source_event_id，evidence 必须逐字等于对应 grant 自己的 evidence，而不是整段 source event 的 event_evidence。该证据必须是一个不含省略拼接的连续获知句，明确写出目标角色和“得知/获悉/确认/听见/看见/收到”或“告诉/告知/通知/透露/说明/宣布”等获知关系；不得用角色在别处出现的姓名拼接他人对话。
此时 memories 数量必须精确等于 required_memory_grants 数量；required_memory_grants 为空时必须输出空 memories，禁止添加未绑定的普通印象。
只输出严格 JSON，字段和值必须遵守以下合同，不得自创别名或枚举：
每一条 event/memory 都必须提供 evidence：逐字复制来源正文中直接支持该候选的连续短句；跨句时可用“……”连接两个或更多按原顺序出现的片段，不得改写或用无关句充当证据。不得擅自在引语前添加“某人说：”；只有来源正文以同一引语结构明确归因时才能复制说话人。
event.summary 和 memory.content 必须逐字等于各自 evidence，不得概括、补充未来信息或改换主体。memory.evidence 必须包含对应角色在正文中的明确姓名；participant_character_ids 只能列 evidence 中明确出现姓名的角色。所有锚点 ID 必须逐字取自可用锚点。
{{"events":[{{"event_type":"action|reveal|relationship|state_change|world_fact","summary":"客观事实","typed_event_ids":["当前 typed event ID"],"participant_character_ids":["角色 business_id"],"occurred_at_anchor_business_id":"锚点 business_id","presentation":"on_screen|offscreen|withheld","audience_disclosure":"hidden|hinted|partial|revealed","evidence":"正文逐字证据"}}],"memories":[{{"character_business_id":"角色 business_id","virtual_ip_business_id":"虚拟IP business_id","typed_character_id":"Canon角色ID","typed_fact_id":"事实ID","typed_source_event_id":"当前typed event ID","memory_type":"witnessed|heard|inferred|dreamed|misled|remembered","content":"角色长期记住的内容","belief":"可选信念","belief_confidence":0.8,"perception":"可选感知","emotional_impact":["情绪"],"salience":0.8,"occurred_at_anchor_business_id":"锚点 business_id","learned_at_anchor_business_id":"锚点 business_id","effective_from_anchor_business_id":"锚点 business_id","invalidated_at_anchor_business_id":null,"growth_delta":{{}},"evidence":"正文逐字证据"}}]}}
participant_character_ids、character_business_id 只能取角色白名单中的 character_business_id；锚点字段只能取可用锚点 business_id。
来源正文：\n{source_text}"""
