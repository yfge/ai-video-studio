from __future__ import annotations

from typing import Any

from .story_novel_adaptation_prompt import adaptation_prompt as adaptation_prompt
from .story_novel_domain import json_prompt_payload
from .story_novel_knowledge_prompt import knowledge_sentence_prefixes
from .story_novel_planning_prompt import planning_prompt as planning_prompt
from .story_novel_prompt_renderer import render_novel_prompt
from .story_novel_repair_safety import fixed_date_repair_action
from .story_novel_state_prompt import locked_state_subjects

SYSTEM_PROMPT = render_novel_prompt("story_novel_system_v3")
STATIC_WORLD_RULES = (
    "story_invariants 与静态 Canon attributes 只是不变约束，不能据此推演或预告当前合同之外的目的地、行动、选择、结果或精确期限。"
    "必须按 compiled_canon 当前可见地点与 genre 描写，禁止自造未授权环境或未来目的地。"
    "compiled_canon.timeline 当前可见 immutable 项的 story_time 必须逐项原样写入正文，不得改写、概括或遗漏；若同日多个事件共享精确日期，正文首段第一句须先写出该日期，其他日期也须在对应事件前出现，事后补写不算。"
    "chapter_contract.key_events 中的固定日期、期限和数量也必须逐字保留，不得换算或改成相邻值。"
    "正文不得新增当前 chapter_contract 与当前可见 immutable timeline 未逐字提供的月份日期；"
    "“某日后”只能原样写“某日后”，绝不能换算成次日或其他相邻日期。"
)
UNRESOLVED_THREAD_RULE = (
    "open_threads 只代表本章发现但尚未解决的问题；正文只能呈现当前 key_events 明示的证据，"
    "不得为它补写修改时间、人物身份、原因、答案、未来权限或后果，也不得把它写入 resolved_threads。"
)
KNOWLEDGE_EVIDENCE_RULE = (
    "chapter_contract.knowledge_grants 中每一项都必须在正文里有一条连续、独立的获知句："
    "使用 compiled_canon 中该 character_id 的明确姓名，并让该姓名直接建立得知、"
    "获悉、确认、听见、看见、收到、告诉、告知、通知、透露、说明或宣布等获知关系，"
    "source_event_text 自身含有其他事实动词时不得删改，并清楚指向"
    "该 source_event_id 对应事实。句首必须逐字使用 Canon entity.name 并立刻紧接获知词，"
    "姓名与获知词之间不得插入动作、代词、标点或其他角色；不得用自行生成的人名、职位别称、"
    "省略拼接、隐含在场或旁人对话代替。"
)
STATE_LOCK_RULE = (
    "下列主体没有本章状态或地点转移授权，location、owner_id、status 必须保持逐字所列值；"
    "canon_refs 只提供背景，不授权携带、部署、激活或转移。key_events 中名称相近的普通物件"
    "不得映射成这些 Canon 主体。若列有 location_rule，物件只可随 owner 的已授权移动同行，"
    "不得自报额外地点转移或把同行写成部署、放置或留下。"
)


def structured_outline_prompt(
    *, story_seed: dict[str, Any], expected_positions: list[int]
) -> str:
    coverage = (
        f"原文明确要求第1章至第{expected_positions[-1]}章，必须完整返回"
        f"{len(expected_positions)}章，禁止合并、省略、截断或新增。"
        if expected_positions
        else "自行确定有限、完整的章节数，position 必须从1连续编号。"
    )
    return render_novel_prompt(
        "story_novel_structured_outline_v3",
        story_seed_json=json_prompt_payload(story_seed),
        coverage=coverage,
    )


def structured_outline_repair_prompt(
    original_prompt: str, previous_output: str, validation_error: str | None
) -> str:
    return render_novel_prompt(
        "story_novel_structured_outline_repair_v3",
        original_prompt=original_prompt,
        validation_error=validation_error or "结构化大纲无效",
        previous_output=previous_output[:12000],
    )


def canon_prompt(*, planning_contract: dict[str, Any]) -> str:
    return render_novel_prompt(
        "story_novel_canon_v3",
        planning_contract_json=json_prompt_payload(planning_contract),
    )


def chapter_prompt(
    *,
    context_pack: dict[str, Any],
    target_chars: int,
    min_chars: int = 3000,
    max_chars: int = 5000,
) -> str:
    margin = max(1, (max_chars - min_chars) // 5)
    safe_min = min_chars + margin
    safe_max = max(safe_min, max_chars - margin)
    safe_target = min(max(target_chars, safe_min), safe_max)
    return f"""根据故事合同写一章通用小说正文。
当前章上下文包：{json_prompt_payload(context_pack)}
{STATIC_WORLD_RULES}
上下文只授权书写当前章节合同；不得猜测、补写或提前完成任何未来事件。
本章正文目标 {target_chars} 个非空白字符，硬性范围 {min_chars}–{max_chars}。
计数时去除全部空格与换行；请实际落在约 {safe_target} 字，推荐安全区间 {safe_min}–{safe_max}，绝对不要超过 {max_chars}。
输出前必须自检 content_text 的非空白字符数；低于 {safe_min} 时不得结束输出。
必须遵守 Canon、角色知情边界、当前角色状态与未闭合线索；不得读取或预告未来章节。
必须逐项真实呈现当前 chapter_contract 的 key_events、state_transitions、milestones_consumed、open_threads 与 payoffs_due。
{STATE_LOCK_RULE} 锁定主体：{json_prompt_payload(locked_state_subjects(context_pack))}
{KNOWLEDGE_EVIDENCE_RULE}
逐项必备获知句合同（source_event_text 是该 grant 必须表达的当前事件事实）：{json_prompt_payload(knowledge_sentence_prefixes(context_pack))}
chapter_contract.location_transitions 是本章允许发生的全部地点移动；为空时所有人物和物件必须保持 current_state 地点，“准备转移”不等于出发、登船、起锚或抵达；非空时只能逐项发生清单中的移动。
每个 open_threads 必须在正文中明确提出对应疑问或可追查异常，并逐字复制到 plot_delta.unresolved_threads；每个 payoffs_due 必须在正文中明确解决并逐字复制到 plot_delta.resolved_threads。
{UNRESOLVED_THREAD_RULE}
plot_delta.key_events 必须逐字、逐项、按原顺序复制 chapter_contract.key_events，不得补充或改写；character_states 必须输出空对象，角色状态只由独立审计提取。
只输出严格 JSON：
{{"title":"章节标题","content_text":"完整正文","summary":"200字内摘要","cliffhanger":"章末卡点","plot_delta":{{"key_events":["逐字复制章节合同"],"unresolved_threads":["逐字复制章节合同"],"resolved_threads":["逐字复制章节合同"],"character_states":{{}}}}}}
不得写剧集、镜头、分镜或制作说明。"""


def chapter_length_repair_prompt(
    *,
    context_pack: dict[str, Any],
    prior_result: dict[str, Any],
    actual_chars: int,
    target_chars: int,
    min_chars: int = 3000,
    max_chars: int = 5000,
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
    safe_ceiling = 4000 if (min_chars, max_chars) == (3000, 5000) else max_chars
    safe_target = min(max(target_chars, min_chars), safe_ceiling)
    return f"""上一版章节正文有 {actual_chars} 个非空白字符，不符合 {min_chars}–{max_chars} 的硬门槛。
保持同一上下文、事件顺序、人物知识边界和章末状态，压缩重写到约 {safe_target} 个非空白字符。
计数时去除全部空格与换行；正文必须落在 {min_chars}–{max_chars}，绝对不要超过 {safe_ceiling}。
上下文包：{json_prompt_payload(context_pack)}
{STATIC_WORLD_RULES}
{STATE_LOCK_RULE} 锁定主体：{json_prompt_payload(locked_state_subjects(context_pack))}
{KNOWLEDGE_EVIDENCE_RULE}
逐项必备获知句合同（source_event_text 是该 grant 必须表达的当前事件事实）：{json_prompt_payload(knowledge_sentence_prefixes(context_pack))}
上一版结构与首尾参考：{json_prompt_payload(repair_reference)}
只输出以下结构的严格 JSON，不要解释；完整正文必须放在 content_text，禁止改名为 body、content 或 text：
{{"title":"章节标题","content_text":"完整正文","summary":"200字内摘要","cliffhanger":"章末卡点","plot_delta":{{"key_events":["本章事件"],"unresolved_threads":["未闭合线索"],"resolved_threads":["回收线索"],"character_states":{{"角色":"章末状态"}}}}}}"""


def chapter_gate_repair_prompt(
    *,
    context_pack: dict[str, Any],
    prior_result: dict[str, Any] | None,
    actual_chars: int,
    target_chars: int,
    violations: list[dict],
    min_chars: int = 3000,
    max_chars: int = 5000,
) -> str:
    margin = max(1, (max_chars - min_chars) // 5)
    safe_min = min_chars + margin
    safe_max = max(safe_min, max_chars - margin)
    safe_target = min(max(target_chars, safe_min), safe_max)
    if actual_chars < min_chars:
        safe_target = min(safe_max, safe_target + safe_min - actual_chars)
    paragraph_count = max(6, round(safe_target / 110))
    if actual_chars < min_chars:
        length_action = (
            f"必须在不删减已有有效叙事的前提下净增至少 "
            f"{safe_min - actual_chars} 个非空白字符。"
        )
    elif actual_chars > max_chars:
        length_action = (
            f"必须压缩至少 {actual_chars - safe_max} 个非空白字符，"
            "但不得删除计划事件或因果桥。"
        )
    else:
        length_action = "保持原有叙事体量，只修复失败项。"
    fixed_date_action = fixed_date_repair_action(violations)
    prior_context = (
        "上一版完整正文（作为本次最小返修基础）："
        f"{json_prompt_payload({'content_text': prior_result.get('content_text')})}\n"
        "保留未涉及的正文、段落、事件顺序与叙事密度，只修改失败项；不得缩写成梗概。"
        if prior_result
        else "上一版正文、摘要、卡点和自报状态含不可披露问题，已全部丢弃，不得据此返修。"
    )
    return f"""上一版章节未通过长篇硬门禁，只允许完整返修一次。
失败项：{json_prompt_payload(violations)}
上一版有 {actual_chars} 个非空白字符；必须按非空白字符计数，去除全部空格、换行与制表符。
返修正文硬性范围 {min_chars}–{max_chars}，安全目标约 {safe_target}；正文必须写满 {paragraph_count}–{paragraph_count + 3} 个完整叙事段落，每段 100–110 个非空白字符，单句对白必须并入叙事段，不得用短段凑数。
{length_action}
输出前必须自检 content_text 的非空白字符数；低于 {safe_min} 时不得结束输出。
必须在正文中真实呈现计划事件、移动过程、知识来源、权限变化和因果桥；不得只在摘要声明。
{STATE_LOCK_RULE} 锁定主体：{json_prompt_payload(locked_state_subjects(context_pack))}
{KNOWLEDGE_EVIDENCE_RULE}
逐项必备获知句合同（source_event_text 是该 grant 必须表达的当前事件事实）：{json_prompt_payload(knowledge_sentence_prefixes(context_pack))}
chapter_contract.location_transitions 是本章允许发生的全部地点移动；为空时删除全部出发、登船、起锚、离开或抵达情节并保持 current_state 地点；非空时只能逐项发生清单中的移动。
必须逐项补齐当前 chapter_contract 的 open_threads 与 payoffs_due：前者在正文中明确提出对应疑问或可追查异常，后者在正文中明确解决；并同步写入 plot_delta。
{UNRESOLVED_THREAD_RULE}
plot_delta 的三个数组必须逐字、逐项、按原顺序复制当前 chapter_contract 对应字段，character_states 必须为空对象。
不得重演已完成事件或里程碑，不得回滚当前状态，不得违反世界规则。
上下文包：{json_prompt_payload(context_pack)}
{STATIC_WORLD_RULES}
{prior_context}
{fixed_date_action}
只输出严格 JSON：
{{"title":"章节标题","content_text":"完整正文","summary":"200字内摘要","cliffhanger":"章末卡点","plot_delta":{{"key_events":["逐字复制章节合同"],"unresolved_threads":["逐字复制章节合同"],"resolved_threads":["逐字复制章节合同"],"character_states":{{}}}}}}
不得解释，不得省略完整正文。"""
