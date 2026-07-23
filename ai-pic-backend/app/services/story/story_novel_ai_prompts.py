from __future__ import annotations

from typing import Any

from .story_novel_domain import json_prompt_payload

SYSTEM_PROMPT = (
    "你是严谨的中文长篇叙事编辑。只使用提供的故事合同，不得引用任何既有剧集。"
)


def planning_prompt(*, planning_contract: dict[str, Any]) -> str:
    return f"""仅根据冻结的 StorySeed、人物与世界约束规划一部长篇小说。
规划合同：{json_prompt_payload(planning_contract)}
大纲必须唯一决定有限且完整的章节数量；不得按预设总字数凑章，也不得省略大纲阶段。
若大纲显式列出连续章节编号，必须逐章对应，禁止合并、省略或新增。
每章目标必须在 3000–5000 个非空白中文字符之间。
只输出严格 JSON：
{{"chapters":[{{"position":1,"title":"标题","goal":"情节目标","key_events":["关键事件"],"character_focus":["角色重点"],"open_threads":["本章埋设或待回收线索"],"end_state":"章末人物与情节状态","target_chars":4000}}]}}
position 必须从 1 连续编号；章节列表必须覆盖整个大纲直至结局方向。"""


def chapter_prompt(
    *,
    context_pack: dict[str, Any],
    target_chars: int,
) -> str:
    safe_target = min(max(target_chars, 3300), 3600)
    return f"""根据故事合同写一章通用小说正文。
当前章上下文包：{json_prompt_payload(context_pack)}
本章正文目标 {target_chars} 个非空白字符，硬性范围 3000–5000。
计数时去除全部空格与换行；为抵消模型估算偏长，请实际落在约 {safe_target} 字，推荐安全区间 3200–3800，绝对不要超过 4200。
必须遵守 Canon、角色知情边界、当前角色状态与未闭合线索；不得读取或预告未来章节。
只输出严格 JSON：
{{"title":"章节标题","content_text":"完整正文","summary":"200字内摘要","cliffhanger":"章末卡点","plot_delta":{{"key_events":["本章事件"],"unresolved_threads":["章末仍未闭合线索"],"resolved_threads":["本章回收线索"],"character_states":{{"角色":"章末状态"}}}}}}
不得写剧集、镜头、分镜或制作说明。"""


def chapter_length_repair_prompt(
    *,
    context_pack: dict[str, Any],
    prior_result: dict[str, Any],
    actual_chars: int,
    target_chars: int,
) -> str:
    content = str(prior_result.get("content_text") or "")
    repair_reference = {
        "title": prior_result.get("title"),
        "summary": prior_result.get("summary"),
        "cliffhanger": prior_result.get("cliffhanger"),
        "plot_delta": prior_result.get("plot_delta"),
        "opening_excerpt": content[:300],
        "closing_excerpt": content[-300:],
    }
    safe_target = min(max(target_chars, 3200), 3400)
    return f"""上一版章节正文有 {actual_chars} 个非空白字符，不符合 3000–5000 的硬门槛。
保持同一上下文、事件顺序、人物知识边界和章末状态，压缩重写到约 {safe_target} 个非空白字符。
计数时去除全部空格与换行；正文必须落在 3100–3700，绝对不要超过 4000。
上下文包：{json_prompt_payload(context_pack)}
上一版结构与首尾参考：{json_prompt_payload(repair_reference)}
只输出以下结构的严格 JSON，不要解释；完整正文必须放在 content_text，禁止改名为 body、content 或 text：
{{"title":"章节标题","content_text":"完整正文","summary":"200字内摘要","cliffhanger":"章末卡点","plot_delta":{{"key_events":["本章事件"],"unresolved_threads":["未闭合线索"],"resolved_threads":["回收线索"],"character_states":{{"角色":"章末状态"}}}}}}"""


def continuity_prompt(*, snapshot: dict[str, Any], chapters: list[dict]) -> str:
    return f"""检查小说章节之间的角色、时间、地点、因果、设定与未闭合线索。
故事合同：{json_prompt_payload(snapshot)}
章节：{json_prompt_payload(chapters)}
只输出严格 JSON：
{{"summary":"总体结论","issues":[{{"id":"stable-id","severity":"blocking|warning","chapter_business_ids":["id"],"message":"问题","suggestion":"修复建议"}}]}}
只有会破坏后续改编的矛盾才标 blocking。"""


def adaptation_prompt(*, snapshot: dict[str, Any], chapters: list[dict]) -> str:
    return f"""把已审批小说规划为可拍摄短剧分集。每集必须引用至少一个来源章节。
故事合同：{json_prompt_payload(snapshot)}
可用章节：{json_prompt_payload(chapters)}
只输出严格 JSON：
{{"episodes":[{{"episode_number":1,"title":"标题","source_chapter_business_ids":["id"],"adaptation_goal":"改编目标","summary":"概要","plot_points":["情节点"],"conflicts":["冲突"],"character_arcs":{{"角色":"本集变化"}},"cliffhanger":"卡点"}}]}}
episode_number 必须从 1 连续编号，不得捏造章节 id。"""
