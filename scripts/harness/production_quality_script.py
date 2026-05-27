"""Script-quality helpers for production quality regression."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "ai-pic-backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))

try:  # pragma: no cover - depends on backend runtime packages
    from app.schemas.script_quality import ScriptLintOptions
    from app.services.script_quality.lint_engine import lint_script_content
except Exception:  # noqa: BLE001 - live report still records provider evidence
    ScriptLintOptions = None  # type: ignore[assignment]
    lint_script_content = None  # type: ignore[assignment]

QUALITY_PASS_THRESHOLD = 9.0
SCRIPT_SCORE_PASS = 4.0
SCRIPT_SCORE_DIMENSION_PASS = 3.5
STRUCTURED_SCORE_PASS = 3.5
STRUCTURED_CORE_MIN = 3.0


def extract_script_payload(payload: dict[str, Any]) -> dict[str, Any]:
    raw = ((payload.get("key_artifacts") or {}).get("script") or {}).get("raw_content")
    if not isinstance(raw, str) or not raw.strip():
        return {}
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if fence:
        text = fence.group(1)
    elif not text.startswith("{"):
        match = re.search(r"\{.*\}", text, flags=re.S)
        if match:
            text = match.group(0)
    data = json.loads(text)
    return data if isinstance(data, dict) else {}


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
        last_plot = str(scenes[-1].get("plot") or "")
        lines.append(f"【悬念】{last_plot or '最后一秒出现新的反转。'}")
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


def structured_script_score(payload: dict[str, Any]) -> dict[str, Any]:
    script = extract_script_payload(payload)
    scenes = script.get("scenes") if isinstance(script.get("scenes"), list) else []
    dialogue_lines = [
        str(line.get("line") or "")
        for scene in scenes
        for line in scene.get("dialogue") or []
        if isinstance(line, dict)
    ]
    values = {
        "hook_3s": _score_text(
            " ".join([str(script.get("logline") or ""), _first_plot(scenes)]),
            ["发现", "警报", "失控", "最后", "反转", "不能", "倒计时"],
            base=3.0,
        ),
        "conflict_clarity": _score_text(
            " ".join(str(scene.get("plot") or "") for scene in scenes),
            ["冲突", "阻止", "抢", "危机", "质疑", "失败", "必须", "倒计时"],
            base=3.0,
        ),
        "dialogue_audibility": _dialogue_score(dialogue_lines),
        "filmability": _filmability_score(scenes),
        "ending_twist": _score_text(
            str(scenes[-1].get("plot") if scenes else ""),
            ["反转", "真相", "却", "原来", "最后", "悬念", "门开了"],
            base=3.0,
        ),
    }
    average = round(sum(values.values()) / len(values), 2) if values else 0.0
    core_min = min(values.values()) if values else 0.0
    return {
        "status": "completed",
        "scores": values,
        "average": average,
        "core_min": core_min,
        "passed": average >= STRUCTURED_SCORE_PASS and core_min >= STRUCTURED_CORE_MIN,
        "pass_threshold": STRUCTURED_SCORE_PASS,
        "core_min_threshold": STRUCTURED_CORE_MIN,
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
    lines = [f"# 第{index}场", f"▲动作：{plot}", f"【镜头】特写/推镜/{video_prompt}"]
    for line in scene.get("dialogue") or []:
        if isinstance(line, dict) and line.get("speaker") and line.get("line"):
            lines.append(f"{line['speaker']}: {line['line']}")
    lines.append("【SFX】电子提示音")
    return lines


def _score_text(text: str, keywords: list[str], *, base: float) -> float:
    hits = sum(1 for keyword in keywords if keyword in text)
    return min(5.0, round(base + hits * 0.4, 2))


def _dialogue_score(dialogue_lines: list[str]) -> float:
    if not dialogue_lines:
        return 0.0
    visible_lengths = [_visible_chars(line) for line in dialogue_lines]
    max_len = max(visible_lengths)
    avg_len = sum(visible_lengths) / len(visible_lengths)
    if max_len <= 15 and avg_len <= 12:
        return 4.5
    if max_len <= 22 and avg_len <= 18:
        return 3.8
    if max_len <= 30:
        return 3.0
    return 2.5


def _filmability_score(scenes: list[dict[str, Any]]) -> float:
    if not scenes:
        return 0.0
    complete = sum(
        1
        for scene in scenes
        if scene.get("plot") and scene.get("video_prompt") and scene.get("dialogue")
    )
    return round(min(5.0, 3.0 + (complete / len(scenes)) * 1.5), 2)


def _first_plot(scenes: list[dict[str, Any]]) -> str:
    return str(scenes[0].get("plot") if scenes else "")


def _visible_chars(text: str) -> int:
    return len(re.sub(r"[\s，。！？!?：:、,.…\"'“”‘’]", "", text))


def _maybe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
