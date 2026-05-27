"""Quality gate evaluation for timeline-first provider samples."""

from __future__ import annotations

from typing import Any

from scripts.harness.production_quality_script import (
    QUALITY_PASS_THRESHOLD,
    STRUCTURED_SCORE_PASS,
    lint_script,
    normalize_script_score,
    structured_script_score,
)
from scripts.harness.provider_chain_payloads import SEEDANCE_CANONICAL

CHARACTER_SCORE_PASS = 3.5

def evaluate_provider_chain_sample(
    payload: dict[str, Any],
    *,
    provider_chain_artifact: str,
    script_lint: dict[str, Any] | None = None,
    script_score: dict[str, Any] | None = None,
    frame_artifacts: list[str] | None = None,
    contact_sheet: str | None = None,
    sample_id: str | None = None,
    attempt: int | None = None,
) -> dict[str, Any]:
    lint = script_lint or lint_script(payload)
    structured = structured_script_score(payload)
    timeline = evaluate_timeline_order(payload)
    render = evaluate_render_structure(payload)
    character = evaluate_character_consistency(
        payload,
        frame_artifacts=frame_artifacts or [],
        contact_sheet=contact_sheet,
    )
    score = normalize_script_score(script_score)
    hard_failures = _failed_gate_names(
        {
            "timeline_order": timeline,
            "render_structure": render,
            "character_consistency": character,
        }
    )
    if not bool(payload.get("ok")):
        hard_failures.append("provider_chain")
    script_failures = _script_failures(lint, score, structured)
    return {
        "sample_id": sample_id,
        "attempt": attempt,
        "provider_chain_artifact": provider_chain_artifact,
        "provider_chain_ok": bool(payload.get("ok")),
        "passed": not hard_failures and not script_failures,
        "hard_failures": hard_failures,
        "script_failures": script_failures,
        "failure_categories": list(payload.get("failure_categories") or []),
        "final_url": _final_url(payload),
        "timeline_id": _timeline_id(payload),
        "timings": extract_step_timings(payload),
        "script_lint": lint,
        "script_score": score,
        "structured_script_score": structured,
        "timeline_order": timeline,
        "render_structure": render,
        "character_consistency": character,
    }


def evaluate_timeline_order(payload: dict[str, Any]) -> dict[str, Any]:
    labels = [str(item.get("label") or "") for item in payload.get("request_chain") or []]
    required = [
        "deepseek-script",
        "timeline-create",
        "timeline-shot-plan",
        "openai-character-image",
        "seedance-video-1",
        "seedance-video-2",
        "timeline-assets-update",
    ]
    positions = {label: _first_index(labels, label) for label in required}
    missing = [label for label, index in positions.items() if index is None]
    ordered = not missing and _ordered_positions(
        [positions[label] for label in required if positions[label] is not None]
    )
    artifacts = payload.get("key_artifacts") or {}
    seed = artifacts.get("timeline_seed") or {}
    shot = artifacts.get("timeline_shot_plan") or {}
    timeline = artifacts.get("timeline") or {}
    version_ok = (
        seed.get("version") == 1
        and shot.get("seed_version") == 1
        and shot.get("version") == 2
        and int(timeline.get("version") or 0) >= 3
    )
    return {
        "passed": bool(ordered and version_ok),
        "required_labels": required,
        "positions": positions,
        "missing_labels": missing,
        "ordered": ordered,
        "version_ok": version_ok,
    }


def evaluate_render_structure(payload: dict[str, Any]) -> dict[str, Any]:
    probe = ((payload.get("key_artifacts") or {}).get("render_media_probe") or {})
    checks = probe.get("checks") if isinstance(probe.get("checks"), dict) else {}
    passed = bool(probe.get("ok")) and all(bool(value) for value in checks.values())
    return {
        "passed": passed,
        "expected_duration_seconds": probe.get("expected_duration_seconds"),
        "format_duration_seconds": probe.get("format_duration_seconds"),
        "video_duration_seconds": probe.get("video_duration_seconds"),
        "audio_duration_seconds": probe.get("audio_duration_seconds"),
        "checks": checks,
        "frame_artifacts": probe.get("frame_artifacts") or [],
        "output_url": probe.get("output_url") or _final_url(payload),
    }


def evaluate_character_consistency(
    payload: dict[str, Any], *, frame_artifacts: list[str], contact_sheet: str | None
) -> dict[str, Any]:
    artifacts = payload.get("key_artifacts") or {}
    reference_url = (artifacts.get("image") or {}).get("oss_url")
    videos = artifacts.get("videos") if isinstance(artifacts.get("videos"), list) else []
    clip_results = [_character_clip_result(clip, reference_url) for clip in videos]
    hard_pass = bool(videos) and all(item["passed"] for item in clip_results)
    frame_pass = len(frame_artifacts) >= len(videos) * 3 if videos else False
    return {
        "passed": hard_pass and frame_pass,
        "auto_score": CHARACTER_SCORE_PASS if hard_pass and frame_pass else 0.0,
        "pass_threshold": CHARACTER_SCORE_PASS,
        "reference_image_url": reference_url,
        "clip_results": clip_results,
        "frame_gate": {
            "required_frames": len(videos) * 3,
            "actual_frames": len(frame_artifacts),
            "passed": frame_pass,
        },
        "frame_artifacts": frame_artifacts,
        "contact_sheet": contact_sheet,
        "manual_visual_review_required": True,
    }


def aggregate_quality_report(
    samples: list[dict[str, Any]], *, expected_sample_count: int
) -> dict[str, Any]:
    first_attempts = [s for s in samples if int(s.get("attempt") or 1) == 1]
    finals = _latest_attempts(samples)
    first_success = sum(1 for sample in first_attempts if sample.get("passed"))
    retry_success = sum(1 for sample in finals if sample.get("passed"))
    timeline_errors = _count_hard_failure(finals, "timeline_order")
    render_errors = _count_hard_failure(finals, "render_structure")
    character_errors = _count_hard_failure(finals, "character_consistency")
    lint_scores = _numeric_values(finals, "script_lint", "overall_score")
    structured_scores = _numeric_values(finals, "structured_script_score", "average")
    checks = {
        "sample_count_matches": len(finals) == expected_sample_count,
        "first_pass_success_at_least_8_of_10": first_success >= 8,
        "retry_success_at_least_9_of_10": retry_success >= 9,
        "timeline_order_errors_zero": timeline_errors == 0,
        "render_structure_errors_zero": render_errors == 0,
        "character_hard_failures_zero": character_errors == 0,
        "script_lint_average_at_least_9": _avg(lint_scores) >= QUALITY_PASS_THRESHOLD,
        "structured_script_average_at_least_3_5": _avg(structured_scores)
        >= STRUCTURED_SCORE_PASS,
    }
    verdict = "trial_ready" if all(checks.values()) else "not_trial_ready"
    if checks["timeline_order_errors_zero"] and checks["render_structure_errors_zero"]:
        if character_errors == 0 and not all(checks.values()):
            verdict = "chain_ready_quality_not_proven"
    return {
        "verdict": verdict,
        "checks": checks,
        "expected_sample_count": expected_sample_count,
        "sample_count": len(finals),
        "first_attempt_count": len(first_attempts),
        "first_success_count": first_success,
        "retry_adjusted_success_count": retry_success,
        "timeline_order_error_count": timeline_errors,
        "render_structure_error_count": render_errors,
        "character_hard_failure_count": character_errors,
        "script_lint_average": round(_avg(lint_scores), 2),
        "structured_script_average": round(_avg(structured_scores), 2),
    }


def extract_step_timings(payload: dict[str, Any]) -> dict[str, float]:
    groups = {
        "deepseek_seconds": ["deepseek-script", "timeline-shot-plan"],
        "gpt_image_seconds": ["openai-character-image"],
        "seedance_seconds": ["seedance-video-"],
        "render_seconds": ["timeline-render-"],
    }
    timings: dict[str, float] = {}
    for key, prefixes in groups.items():
        total = 0.0
        for item in payload.get("request_chain") or []:
            label = str(item.get("label") or "")
            if any(label.startswith(prefix) for prefix in prefixes):
                total += float(item.get("duration_seconds") or 0.0)
        timings[key] = round(total, 3)
    generation = (payload.get("key_artifacts") or {}).get("video_generation") or {}
    if generation.get("wall_time_seconds") is not None:
        timings["seedance_wall_seconds"] = float(generation["wall_time_seconds"])
    return timings


def _character_clip_result(clip: dict[str, Any], reference_url: str | None) -> dict:
    plan = clip.get("timeline_shot_plan")
    checks = {
        "has_timeline_shot_plan": isinstance(plan, dict),
        "has_character_anchor": bool(
            plan.get("character_anchor") if isinstance(plan, dict) else None
        ),
        "uses_same_reference_image": bool(reference_url) and clip.get("image_url") == reference_url,
        "has_seedance_task_id": bool(clip.get("task_id")),
        "has_clip_id_lineage": bool(clip.get("clip_id")),
        "uses_seedance_2": (
            clip.get("provider") == "volcengine"
            and SEEDANCE_CANONICAL in str(clip.get("model") or "")
        ),
        "has_video_url": str(clip.get("video_url") or "").startswith(("http://", "https://")),
    }
    return {"clip_id": clip.get("clip_id"), "checks": checks, "passed": all(checks.values())}


def _script_failures(lint: dict, score: dict, structured: dict) -> list[str]:
    failures = []
    if lint.get("status") == "completed" and not lint.get("passed"):
        failures.append("script_lint")
    if score.get("status") == "completed" and not score.get("passed"):
        failures.append("script_score")
    if score.get("status") == "failed":
        failures.append("script_score")
    if not structured.get("passed"):
        failures.append("structured_script_score")
    return failures


def _latest_attempts(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for sample in samples:
        sample_id = str(sample.get("sample_id") or len(latest) + 1)
        latest[sample_id] = sample
    return list(latest.values())


def _failed_gate_names(gates: dict[str, dict[str, Any]]) -> list[str]:
    return [name for name, gate in gates.items() if not gate.get("passed")]


def _count_hard_failure(samples: list[dict[str, Any]], failure: str) -> int:
    return sum(1 for sample in samples if failure in sample.get("hard_failures", []))


def _numeric_values(samples: list[dict[str, Any]], group: str, key: str) -> list[float]:
    values = []
    for sample in samples:
        value = _maybe_float(sample.get(group, {}).get(key))
        if value is not None:
            values.append(value)
    return values


def _first_index(labels: list[str], target: str) -> int | None:
    for index, label in enumerate(labels):
        if label == target or label.startswith(target):
            return index
    return None


def _ordered_positions(positions: list[int | None]) -> bool:
    integers = [int(position) for position in positions if position is not None]
    return integers == sorted(integers) and len(integers) == len(positions)


def _maybe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _final_url(payload: dict[str, Any]) -> str | None:
    render = (payload.get("key_artifacts") or {}).get("render_job") or {}
    return render.get("output_url")


def _timeline_id(payload: dict[str, Any]) -> Any:
    artifacts = payload.get("key_artifacts") or {}
    timeline = artifacts.get("timeline") or artifacts.get("timeline_seed") or {}
    return timeline.get("id")
