"""Prompt for adapting an approved novel revision into episodes."""

from __future__ import annotations

from typing import Any

from .story_novel_domain import json_prompt_payload


def adaptation_prompt(*, snapshot: dict[str, Any], chapters: list[dict]) -> str:
    return f"""把已审批小说规划为可拍摄短剧分集。每集必须引用至少一个来源章节。
故事合同：{json_prompt_payload(snapshot)}
可用章节：{json_prompt_payload(chapters)}
只输出严格 JSON：
{{"episodes":[{{"episode_number":1,"title":"标题","source_chapter_business_ids":["id"],"adaptation_goal":"改编目标","summary":"概要","plot_points":["情节点"],"conflicts":["冲突"],"character_arcs":{{"角色":"本集变化"}},"cliffhanger":"卡点"}}]}}
episode_number 必须从 1 连续编号，不得捏造章节 id。"""
