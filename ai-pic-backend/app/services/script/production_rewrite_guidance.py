from __future__ import annotations

from typing import Any, Dict, List

from app.services.script_score_thresholds import (
    PASS_DIMENSION_THRESHOLD,
    PASS_OVERALL_THRESHOLD,
)

_DIMENSION_REWRITE_GUIDANCE = {
    "conflict_intensity": (
        "冲突强度需达到精品线：每场都加入新的外部代价或阻力，"
        "开场3秒爆点、中段反杀、结尾危机升级必须可拍。"
    ),
    "character_recognizability": (
        "角色辨识度需达到精品线：主角每场至少有一个稳定行为标签、"
        "一句可识别短对白，反派/配角必须有清楚动机。"
    ),
    "cultural_fit": (
        "文化适配需达到精品线：减少含混或合规风险表达，"
        "用职场合同、客户、证据、权限和责任链推动冲突。"
    ),
    "clip_ability": (
        "素材可剪性需达到精品线：每60秒至少两个台词+画面双钩子，"
        "明确15s/30s/60s可剪片段的首帧动作、关键台词和卡点。"
    ),
    "logic_coherence": (
        "逻辑一致性需达到精品线：补齐证据来源、录音/纪要/日志的取得路径、"
        "角色首次获知信息的画面依据，以及客户态度转变的可见证据。"
    ),
}


def extract_rewrite_guidance(scoring: Dict[str, Any]) -> List[str]:
    script_score = _safe_dict(scoring.get("script_score"))
    guidance = script_score.get("rewrite_guidance")
    items = (
        [str(item).strip() for item in guidance if str(item).strip()]
        if isinstance(guidance, list)
        else []
    )

    overall = _score_overall(scoring)
    if overall and overall < PASS_OVERALL_THRESHOLD:
        items.append(
            f"整体 ScriptScore 必须提升到 {PASS_OVERALL_THRESHOLD:.1f}+；"
            "不要只微调语气，需增加可拍反转、明确收获和更强卡点。"
        )

    dims = _safe_dict(script_score.get("dimension_scores"))
    for key, guidance_text in _DIMENSION_REWRITE_GUIDANCE.items():
        value = dims.get(key)
        if not _below_dimension_threshold(value):
            continue
        score_text = _format_score(value)
        items.append(
            f"{guidance_text} 当前 {key}={score_text}，需 >= {PASS_DIMENSION_THRESHOLD:.1f}。"
        )

    _append_risk_guidance(items, script_score)
    _append_asset_guidance(items, scoring)
    return _dedupe_strings(items)


def _append_risk_guidance(items: List[str], script_score: Dict[str, Any]) -> None:
    risks = script_score.get("risks")
    if not isinstance(risks, list):
        return
    for risk in risks[:3]:
        text = str(risk).strip()
        if text:
            items.append(f"修复评分风险：{text}")


def _append_asset_guidance(items: List[str], scoring: Dict[str, Any]) -> None:
    asset_tags = _safe_dict(scoring.get("asset_tags"))
    asset_count = asset_tags.get("asset_count")
    durations = asset_tags.get("durations")
    if not isinstance(asset_count, (int, float)) or asset_count < 3:
        items.append("投流素材不足：必须内置至少 15s、30s、60s 三类可剪高能段落。")
    elif isinstance(durations, list) and not {15, 30, 60}.issubset(
        {int(item) for item in durations if _looks_numeric(item)}
    ):
        items.append("投流时长覆盖不足：补齐 15s、30s、60s 的钩子、反杀和卡点片段。")


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _score_overall(scoring: Dict[str, Any]) -> float:
    value = _safe_dict(scoring.get("script_score")).get("overall_score")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _below_dimension_threshold(value: Any) -> bool:
    try:
        return float(value) < PASS_DIMENSION_THRESHOLD
    except (TypeError, ValueError):
        return True


def _format_score(value: Any) -> str:
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return "缺失"


def _looks_numeric(value: Any) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def _dedupe_strings(items: List[str]) -> List[str]:
    result: List[str] = []
    seen: set[str] = set()
    for item in items:
        text = item.strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
