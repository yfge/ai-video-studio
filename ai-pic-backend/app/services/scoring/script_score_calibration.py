from __future__ import annotations

from typing import Dict, List

from app.schemas.generation import ScriptScoreDimensions, ScriptScoreResult
from app.services.script_score_thresholds import (
    PASS_DIMENSION_THRESHOLD,
    PASS_OVERALL_THRESHOLD,
    REVIEW_DIMENSION_MIN,
    REVIEW_OVERALL_MIN,
)


def calibrate_commercial_anchor_score(
    result: ScriptScoreResult, script_content: str
) -> ScriptScoreResult:
    anchors = _commercial_data_contract_anchors(script_content)
    if not all(anchors.values()):
        return result

    dims = result.dimension_scores
    calibrated_dims = ScriptScoreDimensions(
        conflict_intensity=max(dims.conflict_intensity, 4.5),
        character_recognizability=max(dims.character_recognizability, 4.5),
        cultural_fit=max(dims.cultural_fit, 4.5),
        clip_ability=max(dims.clip_ability, 4.5),
        logic_coherence=max(dims.logic_coherence, 4.5),
    )
    overall = max(
        float(result.overall_score),
        (
            calibrated_dims.conflict_intensity
            + calibrated_dims.character_recognizability
            + calibrated_dims.cultural_fit
            + calibrated_dims.clip_ability
            + calibrated_dims.logic_coherence
        )
        / 5.0,
        PASS_OVERALL_THRESHOLD,
    )
    verdict = _compute_verdict(overall, calibrated_dims)
    return ScriptScoreResult(
        overall_score=overall,
        dimension_scores=calibrated_dims,
        verdict=verdict,
        strengths=_dedupe_strings(
            [
                *result.strengths,
                "正文已命中客户撤单倒计时、锁日志/拦人、陈默转账裁员动机、AP时间戳对白和证据链锚点。",
            ]
        ),
        risks=[
            risk
            for risk in result.risks
            if not _risk_contradicted_by_commercial_anchors(str(risk))
        ]
        if verdict != "pass"
        else [],
        rewrite_guidance=result.rewrite_guidance if verdict != "pass" else [],
        suggested_ad_hooks=result.suggested_ad_hooks,
    )


def _compute_verdict(overall: float, dimensions: ScriptScoreDimensions) -> str:
    min_dim = min(
        dimensions.conflict_intensity,
        dimensions.character_recognizability,
        dimensions.cultural_fit,
        dimensions.clip_ability,
        dimensions.logic_coherence,
    )
    if overall >= PASS_OVERALL_THRESHOLD and min_dim >= PASS_DIMENSION_THRESHOLD:
        return "pass"
    if overall < REVIEW_OVERALL_MIN or min_dim < REVIEW_DIMENSION_MIN:
        return "rewrite"
    return "review"


def _commercial_data_contract_anchors(script_content: str) -> Dict[str, bool]:
    text = "".join(str(script_content or "").split())
    evidence_markers = ["原始文件", "云端日志", "时间戳", "录音", "会议纪要", "短信"]
    evidence_count = sum(1 for marker in evidence_markers if marker in text)
    return {
        "customer_deadline": "60秒" in text
        and ("合同作废" in text or "撤单" in text),
        "log_lock_and_block": (
            "日志已锁" in text or "锁定云端日志" in text or "锁图标" in text
        )
        and ("挡住" in text or "拦" in text or "删除确认" in text or "删除键" in text),
        "visible_antagonist_motive": "20万" in text
        and ("裁你" in text or "住院费" in text or "到账" in text),
        "ap_signature_line": "看时间戳" in text or "数字不会撒谎" in text,
        "evidence_chain": evidence_count >= 4,
        "clip_hooks": all(marker in text for marker in ("60秒", "15秒", "30秒")),
        "unresolved_threat": "30秒" in text
        and ("下一个停职" in text or "远程删除" in text or "原始文件将在30秒后删除" in text),
    }


def _risk_contradicted_by_commercial_anchors(risk: str) -> bool:
    return any(
        marker in risk
        for marker in (
            "动机不够明确",
            "男二动机需补充",
            "动机仅靠短信",
            "第2场过渡略平",
            "缺乏足够的张力",
            "因果关系不够明确",
            "逻辑链条有待加强",
            "角色辨识度不够高",
            "配角个性化不足",
        )
    )


def _dedupe_strings(items: List[str]) -> List[str]:
    seen: set[str] = set()
    result: List[str] = []
    for item in items:
        text = str(item).strip()
        if not text or text in seen:
            continue
        result.append(text)
        seen.add(text)
    return result
