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
            desc = (
                point.get("description") or point.get("summary") or point.get("title")
            )
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
    sections.append(_commercial_score_contract())
    if attempt_no > 1 and rewrite_guidance:
        sections.append(
            "## 自动返修要求\n"
            "上一版 ScriptScore 未达标，请在保留角色与基本因果的前提下重写：\n"
            + "\n".join(f"- {item}" for item in rewrite_guidance if item)
            + "\n\n"
            + _rewrite_closure_contract(rewrite_guidance)
        )
    return "\n\n".join(section for section in sections if section.strip())


def _commercial_score_contract() -> str:
    return (
        "## 商业评分硬交付清单\n"
        "本轮生成必须能直接通过 ScriptScore：overall_score >= 4.5，"
        "conflict_intensity / character_recognizability / cultural_fit / "
        "clip_ability / logic_coherence 每项 >= 4.2。不要只在说明里承诺，"
        "必须落到正文、场景 summary、structured_script_contract.beats、"
        "dialogue_lines 和 action_lines。\n"
        "- Prompt 忠实度：原始目标中的专有名词、人物、产品、技术、模型、风格、"
        "必须出现和禁止出现项都要落实；不得用评分样板替换用户题材。\n"
        "- 角色辨识度：沿用 brief/content plan 中的稳定角色名、行为方式、动机和"
        "跨集状态；不得为了凑评分擅自新增无关人物。\n"
        "- 逻辑一致性：每个关键信息必须有题材内合理的可见来源、验证动作和结果；"
        "来源可以是人物行为、物件、环境变化、对话、记录或规则，但必须来自当前故事。\n"
        "- 阻力与动机：对手或阻力不能无条件让步；必须通过本题材中的具体选择、"
        "资源限制、关系代价或规则后果体现，不能套用别的题材桥段。\n"
        "- 配角功能：每个出现的配角都要承担不可替代的行动或选择；若 brief 未要求"
        "配角，不得只为评分强行添加。\n"
        "- 场景合理性：冲突升级必须由当前人物目标、场景资产和前序状态自然触发，"
        "不能依赖巧合或无来源道具。\n"
        "- 素材可剪性：按实际成片总时长设计可独立理解的投流片段，"
        "每个片段都要有首帧动作、关键台词、结果变化和卡点/CTA；"
        "每 60 秒至少 2 个台词+画面双钩子，短于 60 秒时按比例设计。\n"
        "- 冲突强度：0-3 秒直接爆外部损失或威胁；每场都要新增阻力、"
        "代价或时间压力，不能只重复同一种动作或解释。\n"
        "- 文化适配：服从 brief 的市场、受众、语言与内容限制，避免工具式对白、"
        "题材错位和敏感可复制的违规细节。"
    )


def _rewrite_closure_contract(rewrite_guidance: List[str]) -> str:
    actionable = [str(item).strip() for item in rewrite_guidance if str(item).strip()]
    checklist = "\n".join(
        f"{idx}. 针对「{item}」：必须新增或改写至少 1 个 visible_event、"
        "1 个 action_line、1 句短对白和 1 个外部后果；不能只改旁白或说明。"
        for idx, item in enumerate(actionable[:8], start=1)
    )
    return (
        "## 返修落地校验\n"
        "生成前先逐条消除上一版风险；生成结果里必须能看到以下变化：\n"
        f"{checklist}\n"
        "如果上一版被指出角色辨识弱、过渡平、动机不足、逻辑跳跃或素材不足，"
        "本版必须新增具名人物动作、关键信息来源镜头、关键关系或外部状态变化镜头，"
        "并按实际成片时长补足可剪片段，不允许复用上一版的同一组动作节奏。"
    )


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
