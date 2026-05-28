"""Script-quality helpers for production quality regression."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from scripts.harness.production_script_payload import extract_script_payload
from scripts.harness.production_structured_score import (
    STRUCTURED_SCORE_PASS,
    beat_action_lines,
    beat_dialogue_lines,
    scene_beats,
    structured_script_score,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "ai-pic-backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

try:  # pragma: no cover - depends on backend runtime packages
    from app.schemas.script_quality import ScriptLintOptions
    from app.services.script_quality.lint_engine import (
        lint_script_content,
        lint_script_content_async,
    )
except Exception:  # noqa: BLE001 - live report still records provider evidence
    ScriptLintOptions = None  # type: ignore[assignment]
    lint_script_content = None  # type: ignore[assignment]
    lint_script_content_async = None  # type: ignore[assignment]

QUALITY_PASS_THRESHOLD = 9.0
SCRIPT_SCORE_PASS = 4.0
SCRIPT_SCORE_DIMENSION_PASS = 3.5


def provider_chain_script_text(payload: dict[str, Any]) -> str:
    script = extract_script_payload(payload)
    title = str(script.get("title") or "未命名短剧")
    logline = str(script.get("logline") or "")
    characters = script.get("characters") if isinstance(script.get("characters"), list) else []
    lines = [
        f"# {title}",
        f"▲3秒钩子：{logline or '主角开场遇到必须立刻解决的异常。'}",
        "【节奏】快",
        "【情绪目标】紧张/反转/推进",
        "【SFX】警报声",
    ]
    if characters:
        anchor = str(characters[0].get("consistency_anchor") or "")
        appearance = str(characters[0].get("appearance_prompt") or "")
        lines.append(f"▲角色锚点：{appearance} {anchor}".strip())
    scenes = script.get("scenes") if isinstance(script.get("scenes"), list) else []
    for index, scene in enumerate(scenes, start=1):
        lines.extend(_scene_to_lint_lines(index, scene))
    if scenes:
        final_cliffhanger = _final_cliffhanger_text(scenes[-1])
        lines.append(f"【悬念】{final_cliffhanger or '最后一秒出现新的反转。'}")
    return "\n".join(lines) + "\n"


def lint_script(payload: dict[str, Any]) -> dict[str, Any]:
    text = provider_chain_script_text(payload)
    if lint_script_content is None or ScriptLintOptions is None:
        return {
            "status": "skipped",
            "reason": "backend_script_quality_linter_unavailable",
            "passed": False,
            "overall_score": None,
            "pass_threshold": QUALITY_PASS_THRESHOLD,
            "screenplay": text,
        }
    result = lint_script_content(text, ScriptLintOptions(pass_threshold=9.0))
    return _lint_result_dict(result, text)


async def lint_script_async(
    payload: dict[str, Any],
    *,
    ai_manager: Any,
    model: str | None = None,
    prefer_provider: str | None = None,
) -> dict[str, Any]:
    text = provider_chain_script_text(payload)
    if lint_script_content_async is None or ScriptLintOptions is None:
        return {
            "status": "skipped",
            "reason": "backend_script_quality_linter_unavailable",
            "passed": False,
            "overall_score": None,
            "pass_threshold": QUALITY_PASS_THRESHOLD,
            "screenplay": text,
        }
    result = await lint_script_content_async(
        text,
        options=ScriptLintOptions(pass_threshold=9.0),
        ai_manager=ai_manager,
        model=model,
        prefer_provider=prefer_provider,
    )
    return _lint_result_dict(result, text)


def _lint_result_dict(result: Any, text: str) -> dict[str, Any]:
    return {
        "status": "completed",
        "passed": bool(result.passed),
        "overall_score": result.overall_score,
        "pass_threshold": QUALITY_PASS_THRESHOLD,
        "issue_count": len(result.issues),
        "rules": [
            {"rule_id": rule.rule_id, "score": rule.score, "passed": rule.passed}
            for rule in result.rules
        ],
        "issues": [
            {
                "severity": issue.severity,
                "rule_id": issue.rule_id,
                "message": issue.message,
                "line": issue.line,
            }
            for issue in result.issues[:20]
        ],
        "screenplay": text,
    }


def normalize_script_score(score: dict[str, Any] | None) -> dict[str, Any]:
    if not score:
        return {"status": "skipped", "reason": "script_score_not_run", "passed": False}
    status = score.get("status")
    if status in {"skipped", "failed"}:
        return {**score, "passed": False}
    dims = score.get("dimension_scores") or {}
    dim_values = {
        key: _maybe_float(value)
        for key, value in dims.items()
        if _maybe_float(value) is not None
    }
    overall = _maybe_float(score.get("overall_score"))
    passed = (
        score.get("verdict") == "pass"
        and overall is not None
        and overall >= SCRIPT_SCORE_PASS
        and bool(dim_values)
        and all(value >= SCRIPT_SCORE_DIMENSION_PASS for value in dim_values.values())
    )
    return {
        "status": "completed",
        "provider": score.get("provider", "deepseek"),
        "model": score.get("model", "deepseek-v4-flash"),
        "verdict": str(score.get("verdict") or ""),
        "overall_score": overall,
        "dimension_scores": dim_values,
        "passed": passed,
        "pass_threshold": SCRIPT_SCORE_PASS,
        "dimension_threshold": SCRIPT_SCORE_DIMENSION_PASS,
        "risks": score.get("risks") or [],
    }


def _scene_to_lint_lines(index: int, scene: dict[str, Any]) -> list[str]:
    plot = str(scene.get("plot") or "角色发现异常并立即行动。")
    video_prompt = str(scene.get("video_prompt") or scene.get("image_prompt") or "")
    lines = [f"[第{index}场]", f"▲动作：{plot}", f"【镜头】特写/推镜/{video_prompt}"]
    beats = scene_beats(scene)
    if beats:
        for beat in beats:
            visible = beat.get("visible_event")
            if visible:
                lines.append(f"▲beat{beat.get('order_index')}: {visible}")
            for action in beat_action_lines(beat):
                lines.append(f"▲动作：{action}")
            for line in beat_dialogue_lines(beat):
                speaker = line.get("speaker") or line.get("character")
                text = line.get("line") or line.get("content")
                if speaker and text:
                    lines.append(f"{speaker}: {text}")
    else:
        for line in scene.get("dialogue") or []:
            if isinstance(line, dict) and line.get("speaker") and line.get("line"):
                lines.append(f"{line['speaker']}: {line['line']}")
    lines.append("【SFX】电子提示音")
    return lines


def _final_cliffhanger_text(scene: dict[str, Any]) -> str:
    beats = scene_beats(scene)
    final = beats[-1] if beats else {}
    parts = [
        str(final.get("visible_event") or ""),
        str(final.get("cliffhanger_tag") or ""),
    ]
    parts.extend(beat_action_lines(final))
    for line in beat_dialogue_lines(final):
        text = line.get("line") or line.get("content")
        if text:
            parts.append(str(text))
    return "；".join(part for part in parts if part).strip()


def _maybe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
