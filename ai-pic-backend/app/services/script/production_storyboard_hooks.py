from __future__ import annotations

from typing import Any


def annotate_storyboard_frames_with_hooks(
    frames: list[dict[str, Any]],
    *,
    hook_schedule: dict[str, Any],
    scoring: dict[str, Any] | None = None,
) -> int:
    """Apply hook/ad metadata to storyboard placeholder frames in-place."""

    if not frames:
        return 0

    ad_snippets = _traffic_ad_snippets(scoring or {})
    changed = 0
    candidates = [frame for frame in frames if isinstance(frame, dict)]
    non_pause = [frame for frame in candidates if frame.get("beat_type") != "pause"]
    if not non_pause:
        non_pause = candidates

    first = non_pause[0]
    changed += _set_frame_hook(
        first,
        "opening_hook",
        ad_snippets[0] if ad_snippets else _schedule_ad_snippet(hook_schedule, 0),
    )

    payoff_frame = _find_frame(non_pause, ("爽", "反击", "揭露", "证据", "逆转"))
    if payoff_frame:
        changed += _set_frame_hook(
            payoff_frame,
            "payoff",
            (
                ad_snippets[1]
                if len(ad_snippets) > 1
                else _schedule_ad_snippet(hook_schedule, 1)
            ),
        )

    last = non_pause[-1]
    if last is not first:
        changed += _set_frame_hook(
            last,
            "cliffhanger",
            ad_snippets[-1] if ad_snippets else _schedule_ad_snippet(hook_schedule, 2),
        )
    return changed


def _traffic_ad_snippets(scoring: dict[str, Any]) -> list[dict[str, Any]]:
    traffic = _safe_dict(scoring.get("traffic_sheet"))
    snippets: list[dict[str, Any]] = []
    for asset in _as_list(traffic.get("assets")):
        if not isinstance(asset, dict):
            continue
        hook = (
            asset.get("key_line") or asset.get("visual_hook") or asset.get("hook_type")
        )
        if not hook:
            continue
        snippets.append(
            {
                "duration_seconds": asset.get("duration_seconds"),
                "hook": hook,
                "visual_summary": asset.get("visual_hook"),
                "call_to_action": asset.get("cliff_or_cta"),
            }
        )
    return snippets


def _schedule_ad_snippet(
    hook_schedule: dict[str, Any],
    index: int,
) -> dict[str, Any] | None:
    candidates = _as_list(hook_schedule.get("ad_candidate_beats"))
    if index < len(candidates) and isinstance(candidates[index], dict):
        candidate = candidates[index]
        hook = candidate.get("hook")
        if hook:
            return {
                "duration_seconds": candidate.get("duration_seconds"),
                "hook": hook,
                "visual_summary": candidate.get("visual_summary"),
                "call_to_action": candidate.get("call_to_action"),
            }
    return None


def _set_frame_hook(
    frame: dict[str, Any],
    hook_tag: str,
    ad_snippet: dict[str, Any] | None,
) -> int:
    changed = 0
    if not frame.get("hook_tag"):
        frame["hook_tag"] = hook_tag
        changed += 1
    if ad_snippet and not frame.get("ad_snippet"):
        frame["ad_snippet"] = ad_snippet
        changed += 1
    return changed


def _find_frame(
    frames: list[dict[str, Any]],
    keywords: tuple[str, ...],
) -> dict[str, Any] | None:
    for frame in frames:
        text = " ".join(
            str(frame.get(key) or "")
            for key in ("description", "beat_text", "prompt_description", "ai_prompt")
        )
        if any(keyword in text for keyword in keywords):
            return frame
    return None


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
