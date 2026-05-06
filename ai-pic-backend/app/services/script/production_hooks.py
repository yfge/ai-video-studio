from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def build_hook_schedule(
    story: Dict[str, Any],
    episode: Dict[str, Any],
    marketing_overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the production hook schedule contract for script generation."""

    marketing = _merge_non_empty(story, episode, marketing_overrides or {})
    hook_plan = _safe_dict(marketing.get("hook_plan"))
    opening_hook = (
        hook_plan.get("opening_hook")
        or _first_non_empty(episode.get("summary"), story.get("main_conflict"))
        or "开场直接抛出本集核心冲突或身份/证据爆点"
    )
    payoff = (
        hook_plan.get("payoff_plan")
        or _first_non_empty(episode.get("payoff"), story.get("resolution"))
        or "主角必须赢到一个具体收获，并用可拍动作兑现爽点"
    )
    cliffhanger = _first_from_list(marketing.get("cliffhanger_plan")) or (
        "结尾留下更大危机或未解真相，不做完全收束"
    )

    conflict_ladder: List[Dict[str, Any]] = []
    for idx, point in enumerate(_as_list(episode.get("plot_points"))[:5], start=1):
        if isinstance(point, dict):
            desc = point.get("description") or point.get("summary") or point.get("title")
            timing = point.get("timing")
        else:
            desc = str(point)
            timing = None
        if desc:
            conflict_ladder.append(
                {"sequence": idx, "description": str(desc), "timing": timing}
            )

    if not conflict_ladder:
        summary = _first_non_empty(episode.get("summary"), story.get("synopsis"))
        if summary:
            conflict_ladder.append(
                {"sequence": 1, "description": str(summary), "timing": "中段"}
            )

    ad_candidate_beats = []
    for idx, snippet in enumerate(_as_list(marketing.get("ad_snippets"))[:5], start=1):
        if not isinstance(snippet, dict):
            continue
        hook = snippet.get("hook") or snippet.get("key_line")
        if not hook:
            continue
        ad_candidate_beats.append(
            {
                "sequence": idx,
                "duration_seconds": snippet.get("duration_seconds"),
                "hook": hook,
                "visual_summary": snippet.get("visual_summary")
                or snippet.get("visual_hook"),
                "call_to_action": snippet.get("call_to_action")
                or snippet.get("cliff_or_cta"),
            }
        )

    return {
        "opening_hook": opening_hook,
        "conflict_ladder": conflict_ladder,
        "payoff": payoff,
        "cliffhanger": cliffhanger,
        "twist_density": marketing.get("twist_density"),
        "market_region": marketing.get("market_region"),
        "micro_genre": marketing.get("micro_genre"),
        "ad_candidate_beats": ad_candidate_beats,
    }


def render_production_requirements(
    *,
    base_additional_requirements: Optional[str],
    hook_schedule: Dict[str, Any],
    rewrite_guidance: List[str],
    attempt_no: int,
) -> str:
    sections: List[str] = []
    if base_additional_requirements:
        sections.append(str(base_additional_requirements).strip())
    sections.append(
        "## 生产级剧本链路要求\n"
        "严格遵守以下 hook_schedule。剧本必须把 opening_hook、conflict_ladder、"
        "payoff、cliffhanger 写成可拍动作、短对白和明确场景事件。\n"
        f"{json.dumps(hook_schedule, ensure_ascii=False, indent=2)}"
    )
    if attempt_no > 1 and rewrite_guidance:
        sections.append(
            "## 自动返修要求\n"
            "上一版 ScriptScore 未达标，请在保留角色与基本因果的前提下重写：\n"
            + "\n".join(f"- {item}" for item in rewrite_guidance if item)
        )
    return "\n\n".join(section for section in sections if section.strip())


def _merge_non_empty(*sources: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key, value in source.items():
            if value not in (None, "", [], {}):
                merged[key] = value
    return merged


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _first_from_list(value: Any) -> Optional[str]:
    for item in _as_list(value):
        if item not in (None, "", [], {}):
            return str(item)
    return None


def _first_non_empty(*values: Any) -> Optional[str]:
    for value in values:
        if value not in (None, "", [], {}):
            return str(value)
    return None
