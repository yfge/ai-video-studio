from __future__ import annotations

from typing import Any

from .story_novel_domain import json_prompt_payload

SYSTEM_PROMPT = (
    "你是严谨的中文长篇叙事编辑。只使用提供的故事合同，不得引用任何既有剧集。"
)


def chapter_prompt(
    *,
    snapshot: dict[str, Any],
    chapter_plan: dict,
    previous: list[dict],
    target_words: int,
) -> str:
    return f"""根据故事合同写一章通用小说正文。
故事合同：{json_prompt_payload(snapshot)}
本章计划：{json_prompt_payload(chapter_plan)}
此前章节摘要：{json_prompt_payload(previous)}
本章目标约 {target_words} 个中文字符。
只输出严格 JSON：
{{"title":"章节标题","content_text":"完整正文","summary":"200字内摘要","cliffhanger":"章末卡点"}}
不得写剧集、镜头、分镜或制作说明。"""


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
