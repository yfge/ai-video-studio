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
        "- 角色辨识度：主角每场至少 2 次具名出场、1 个稳定行为标签、"
        "1 句可复用短对白；配角/反派必须写清可见动机和当场选择，"
        "禁止只写“助理/篡改者/团队成员”而不交代行为标签。\n"
        "- 逻辑一致性：每个指控必须有可见证据链：信息来源 -> 现场验证 -> "
        "客户/合同/权限/文件后果；录音、日志、短信、合同、原始文件第一次出现时"
        "必须写清是谁拿出、从哪里来、屏幕上出现什么。\n"
        "- 嫌疑人/反派动机：不能被主角一问就承认；必须先抗拒、试图离开、"
        "删除文件或甩锅，并通过转账记录、上级短信、绩效威胁、债务或合同利益"
        "露出具体动机。\n"
        "- 助理/配角功能：助理必须有具名动作标签和不可替代贡献，例如拦住嫌疑人、"
        "调出云端日志、锁定删除时间戳、把客户倒计时提醒给主角；不能只说“马上查”。\n"
        "- 私下对峙合理性：走廊/办公室对峙必须有外部压力，例如客户60秒后离场、"
        "合同即将作废、文件正在删除、助理堵住出口或权限即将失效；"
        "录音/证据获取不能靠巧合。\n"
        "- 无明确配角名时必须主动命名并稳定使用：客户张总、助理小陈、"
        "篡改者陈默/李明等；禁止在正文或对白里只写“客户/助理/篡改者”。\n"
        "- 职场数据/合同题材必须使用强桥段：客户张总给出60秒撤单倒计时，"
        "助理小陈锁住云端日志并拦住嫌疑人，篡改者陈默先抢手机/删文件/甩锅，"
        "随后被转账短信或上级威胁短信暴露动机；主角固定短对白可用“数字不会撒谎，看时间戳”。\n"
        "- 第二场必须具备广告切片强度：陈默手指停在删除确认键、小陈挡住出口、"
        "张总电话倒计时只剩15秒、AP夺回手机或按下取消删除；陈默动机必须在画面上出现，"
        "例如短信“改完给你20万，不做就裁你”或银行到账提醒，不能只说“上级让我做”。\n"
        "- 素材可剪性：正文必须内置 15s、30s、60s 三类投流片段，"
        "每类都要有首帧动作、关键台词、结果变化和卡点/CTA；"
        "每 60 秒至少 2 个台词+画面双钩子。\n"
        "- 冲突强度：0-3 秒直接爆外部损失或威胁；每场都要新增阻力、"
        "代价或倒计时，不能只重复举文件、看屏幕、解释误会。\n"
        "- 文化适配：用合同、客户、权限、证据、责任链推进冲突，"
        "避免工具式对白和敏感可复制的违规细节。"
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
        "本版必须新增具名人物动作、证据来源镜头、客户态度变化镜头，以及"
        "15s/30s/60s 可剪片段，不允许复用上一版的同一组动作节奏。"
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
