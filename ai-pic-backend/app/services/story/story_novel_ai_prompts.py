from __future__ import annotations

from typing import Any

from .story_novel_adaptation_prompt import adaptation_prompt as adaptation_prompt
from .story_novel_domain import json_prompt_payload
from .story_novel_planning_prompt import planning_prompt as planning_prompt
from .story_novel_repair_safety import fixed_date_repair_action

SYSTEM_PROMPT = (
    "你是严谨的中文长篇叙事编辑。只使用提供的故事合同，不得引用任何既有剧集。"
)
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
    "使用 compiled_canon 中该 character_id 的明确姓名，只出现一次得知、获悉、确认、"
    "听见、看见、收到、告诉、告知、通知、透露、说明或宣布等获知关系，并清楚指向"
    "该 source_event_id 对应事实。不要用省略拼接、隐含在场或旁人对话代替。"
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
    return f"""把普通文字大纲转换为可编辑的结构化章节大纲。
StorySeed：{json_prompt_payload(story_seed)}
{coverage}
每章必须有 title、goal、至少一个 key_event、character_focus、open_threads 和 end_state。
open_threads 只允许列出本章首次提出、且需要更晚章节回答的新线索；同一 ID 在全书只能
出现一次，后续章节不得重复携带仍未解决的旧 ID。已经在本章 key_events 中回答的问题
不得写入 open_threads。open_threads 可以为空，不得为每章强造卡点；
每个 ID 只表达一个原子问题，禁止用分号、顿号或“以及”合并多条线索。
稳定 thread_id 必须全书唯一，终章不得新开线索。
先在内部建立全书伏笔表，再输出 thread_payoffs：每个 open_threads ID 必须且只能在
严格更晚的一章回收一次；payoff_position 不能等于或早于打开章。每条 evidence_key_event
必须逐字复制目标章的一条 key_events，且必须写成
“关于“{{thread_id 原文}}”的最终证据确认：{{具体且有既有大纲依据的答案}}”；
答案不得新增 StorySeed 未给出的具体时刻、地点、人物、物件、能力或因果，不能用无关事件凑数。
同一章最多回收 3 条；若某条线索没有后续明确答案，必须改写后续 key_events 后再输出。
最后一章必须在 goal、key_events 或 end_state 中明确且原样覆盖 ending_direction。
只输出严格 JSON：
{{"structured_outline":{{"status":"draft","version":1,"thread_schedule_version":1,
"chapters":[{{"position":1,"title":"标题","goal":"情节目标","key_events":["关键事件"],"character_focus":[],"open_threads":[],"end_state":"章末状态"}}],
"thread_payoffs":[{{"thread_id":"逐字复制此前 open_threads ID","payoff_position":2,"evidence_key_event":"目标章 key_events 原文"}}]}}}}
不得输出正文，不得静默裁剪章节。"""


def canon_prompt(*, planning_contract: dict[str, Any]) -> str:
    return f"""仅根据冻结的 StorySeed、人物与世界约束编译唯一 Canon。
规划合同：{json_prompt_payload(planning_contract)}
所有 ID 使用简短稳定英文标识；同一人物、地点、物件、规则或里程碑只能有一个 ID。
entities 只允许 character、location、object、organization；规则和里程碑只写入各自专用数组。
entities.attributes 只允许年龄、职业、类型等不会随剧情改变的静态元数据；location、owner_id、status、identity、knowledge、permissions、injuries、destroyed_at 等可变或未来字段一律写入 initial_state 的事件前值，禁止提前写入 attributes。
world_rules 只能逐字复制 StorySeed.world_constraints 中不含章号或未来剧情的独立静态约束；
不得从 structured_outline、结局、未来事件、里程碑或角色弧推导世界规则。
location 必须覆盖大纲中每个物理停靠点，以及“本章出发、后章才抵达”时人物真实所在的车厢、缆车或路线区段；跨章旅途不得临时发明未注册地点 ID。
initial_state 按实体 ID 记录地点、身份、关系、知识、伤势、能力、权限、所有者或物理状态。
initial_state.location 只能引用 kind=location 的实体；物件所有者必须写 owner_id，禁止把角色 ID 写入 location。
initial_state 的时间截面固定为第1章任何事件发生前（position=0），绝不能写入任何 planned_position>=1 的里程碑结果。
若后续章节才会移交、取得、发现、封存、公开、受伤、升级、激活或熔毁，initial_state 必须保留事件发生前的来源所有者、未知/未取得状态和原有权限；不得把未来接收者、未来知识或未来伤势提前写入。
timeline、milestones 与 character_arcs 可以描述未来计划，但它们绝不是 initial_state 已发生的事实。
timeline 的 story_time 只能使用 StorySeed 明示的日期、相对时间或行程时长；未给出具体时刻时禁止擅自补小时和分钟。
每个 immutable timeline 必须用 source_chapter_position 与 source_key_event 指向冻结 structured_outline 中唯一一条逐字 key_event；source_key_event 与 label 必须完全相同并完整逐字复制该 key_event，禁止概括、改写或指向 goal/end_state。没有明确大纲事件来源的时间描述不得编入 immutable timeline。
story_time 去除空白与标点后的完整字面值必须位于 source_key_event 开头，表示该事件自身的发生时间；嵌在“宣布某未来日期”“截止某日”等宾语里的日期不是事件发生时间。日期、时刻、时段或相对时间任一部分未被该 key_event 开头明示时，必须删除该 timeline，禁止从 goal、end_state、setting_time 或其他章节借用。
milestones 只收录不可逆且只能发生一次的揭露、选择、激活、合并、死亡或归属变化。
不得为了逐章对齐而每章都创建 milestone；若事件只是确认、验证或保持此前已经成立的状态，必须删除该 milestone。
临时权限的取得、到期或撤销只属于章节状态变化，不得创建 Canon milestone；尤其不得让“取得”和“到期”重复使用同一个 contains outcome。
每个 planned_position>=1 且 repeatable=false 的 milestone 必须提供至少一个 typed outcomes；outcomes 只允许 eq 或 contains，并用稳定实体/事实 ID 表达该里程碑完成后必然成立的状态。
身份公开、身份揭露或合法身份变更必须用该角色的 identity eq 最终公开身份表达，不能只授予旁观者 knowledge。
物件销毁、熔毁或耗尽时，终态 milestone 必须同时令 status 进入终态且 owner_id eq null；残片或替代物必须使用独立 object 实体。
终态 outcome 包含 owner_id eq null 时，initial_state 应写 StorySeed 明示的非空来源所有者；若第1章后另有更早 milestone 明确把 owner_id 从 null 改给持有人，则必须保留这条完整 null→持有人→null 状态链。
印章、文件或凭证若开封/核验后仍作为证据存在，status 应写 opened 或 verified，不得误写 consumed、spent 等销毁终态。
若物件最终被交入档案、仓库或设施，必须把该物理存放点注册为 location 实体，并让物件最终 location 指向它。
每个 outcome 必须在此前为假，并在 milestone 所在章结束后新变为真；不同 milestone 不得声明完全相同的 typed outcome。
若多个候选 milestone 得到完全相同的 outcome，只保留 planned_position 最早、真正使它首次成立的那一条；更晚的“仍然成立”不是 milestone。
物件会跟随 owner_id 对应角色移动；若持有者按大纲在 milestone 之前已抵达目标地点，禁止把该地点写成 milestone 的 location outcome，应只保留届时才首次成立的 status、owner_id 或 knowledge outcome。
归档或公开时若 owner_id 本来就是 null，不得把 owner_id eq null 重复写成 outcome；只记录真正改变的 location、status 或权限状态。
initial_state 必须让所有未来 milestone outcomes 都不成立；例如未来才移交给 char-b 的 object owner_id 在 position=0 必须是来源角色或 null，未来才揭露的 fact-id 不得出现在知识数组。
JSON 的空值必须写字面量 null，数组必须写真实 JSON 数组，禁止写成字符串 "null"、"[]" 或 JSON 字符串。
只输出严格 JSON：
{{"timeline":[{{"id":"time-1","label":"第1日 08:00 发生的逐字 key_event","order":1,"story_time":"第1日 08:00","immutable":true,"source_chapter_position":1,"source_key_event":"第1日 08:00 发生的逐字 key_event"}}],
"entities":[{{"id":"char-a","kind":"character|location|object|organization","name":"名称","aliases":[],"attributes":{{}}}}],
"world_rules":[{{"id":"rule-1","statement":"不可违反的规则","exceptions":[]}}],
"gate_version":2,
"milestones":[{{"id":"mile-1","label":"只发生一次的节点","planned_position":3,"repeatable":false,"outcomes":[{{"subject_id":"object-a","field":"owner_id","operator":"eq","value":"char-a"}},{{"subject_id":"char-a","field":"knowledge","operator":"contains","value":"fact-id"}}]}}],
"character_arcs":[{{"character_id":"char-a","start_state":"起点","checkpoints":[{{"position":3,"state":"转折"}}],"end_state":"终态"}}],
"initial_state":{{"char-a":{{"location":"location-id","knowledge":[],"permissions":[],"possessions":[]}},"object-a":{{"location":"location-id","owner_id":null,"status":"尚未移交"}}}}}}
不得加入 StorySeed 没有依据的未来设定。"""


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
{KNOWLEDGE_EVIDENCE_RULE}
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
{KNOWLEDGE_EVIDENCE_RULE}
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
    paragraph_count = max(4, round(safe_target / 160))
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
返修正文硬性范围 {min_chars}–{max_chars}，安全目标约 {safe_target}；建议约 {paragraph_count} 个完整叙事段落，每段约 140–180 个非空白字符。
{length_action}
输出前必须自检 content_text 的非空白字符数；低于 {safe_min} 时不得结束输出。
必须在正文中真实呈现计划事件、移动过程、知识来源、权限变化和因果桥；不得只在摘要声明。
{KNOWLEDGE_EVIDENCE_RULE}
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
