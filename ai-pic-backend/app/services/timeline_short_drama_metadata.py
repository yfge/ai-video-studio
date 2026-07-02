from __future__ import annotations

from typing import Any

from app.models.script import Episode, Script


def build_production_context(
    episode: Episode,
    script: Script,
    duration_ms: int,
) -> dict[str, Any]:
    story = getattr(episode, "story", None)
    language = getattr(script, "language", None) or "zh-CN"
    aspect_ratio = (
        getattr(episode, "aspect_ratio", None)
        or getattr(story, "default_aspect_ratio", None)
        or "9:16"
    )
    target_region = "CN" if str(language).lower().startswith("zh") else "global"
    return {
        "format": getattr(story, "story_format", None) or "short_drama",
        "target_region": target_region,
        "target_platforms": _target_platforms(target_region),
        "episode_duration_seconds": round(duration_ms / 1000, 3),
        "genre": getattr(story, "genre", None),
        "target_audience": getattr(story, "target_audience", None),
        "language": language,
        "aspect_ratio": aspect_ratio,
        "business_goal": "validate_hook_then_scale",
        "compliance": {
            "operator_review_required": True,
            "copyright_review_required": True,
            "ai_content_classification": "micro_drama_ai_assisted",
            "filing_required": target_region == "CN",
        },
    }


def build_short_drama_spec_metadata(
    episode: Episode,
    script: Script,
    beats: list[dict[str, Any]],
    *,
    duration_ms: int,
) -> dict[str, Any]:
    production_context = build_production_context(episode, script, duration_ms)
    return {
        "production_context": production_context,
        "concept_test_pack": build_concept_test_pack(episode, beats),
        "short_drama_quality": build_short_drama_quality(
            beats,
            duration_ms=duration_ms,
            aspect_ratio=production_context["aspect_ratio"],
        ),
        "localization_exports": build_localization_exports(production_context),
        "feedback_loop": {
            "status": "manual_or_csv_pending",
            "metrics": [
                "three_second_retention",
                "completion_rate",
                "click_through_rate",
                "paid_unlock_rate",
                "comment_tags",
            ],
        },
    }


def build_concept_test_pack(
    episode: Episode,
    beats: list[dict[str, Any]],
) -> dict[str, Any]:
    title = getattr(episode, "title", None) or "Episode"
    hook = _first_text(beats) or title
    payoff = _last_text(beats) or hook
    return {
        "status": "draft",
        "scoring_method": "rule_and_operator_review",
        "variants": [
            {
                "opening_hook": hook,
                "poster_copy": f"{title}: {hook}",
                "first_10s_script": hook,
                "paid_unlock_point": payoff,
            },
            {
                "opening_hook": f"反转开场：{hook}",
                "poster_copy": "她必须在十秒内证明自己",
                "first_10s_script": f"{hook} {payoff}",
                "paid_unlock_point": "下一集揭示关键证据",
            },
            {
                "opening_hook": f"冲突直给：{payoff}",
                "poster_copy": "证据、背叛和最后通牒",
                "first_10s_script": payoff,
                "paid_unlock_point": "反派反击前切断",
            },
        ],
    }


def build_short_drama_quality(
    beats: list[dict[str, Any]],
    *,
    duration_ms: int,
    aspect_ratio: str,
) -> dict[str, Any]:
    first = beats[0] if beats else {}
    hook_score = (
        1.0
        if first.get("start_ms") == 0 and first.get("end_ms", 9999) <= 3000
        else 0.6
    )
    conflict_beats = [beat for beat in beats if _has_conflict_text(beat)]
    duration_windows = max(1.0, duration_ms / 15_000)
    return {
        "hook_score": hook_score,
        "conflict_turn_rate": round(len(conflict_beats) / duration_windows, 2),
        "cliffhanger_score": (
            1.0 if _has_conflict_text(beats[-1] if beats else {}) else 0.6
        ),
        "vertical_readability": 1.0 if aspect_ratio == "9:16" else 0.5,
        "compliance_risk": "operator_review_required",
    }


def attach_short_drama_video_metadata(
    video_clips: list[dict[str, Any]],
    production_context: dict[str, Any],
) -> None:
    if production_context.get("format") != "short_drama":
        return
    total = len(video_clips)
    for index, clip in enumerate(video_clips):
        refs = clip.setdefault("source_refs", {})
        refs["vertical_visual_contract"] = {
            "aspect_ratio": production_context["aspect_ratio"],
            "safe_zones": ["subtitle_bottom_safe", "face_center_safe"],
            "framing": "close_up_or_medium_close_up_first",
            "readability": ["face_readable", "key_action_readable", "mobile_first"],
        }
        refs["short_drama_quality"] = {
            "hook_role": _hook_role(index, total),
            "vertical_readability": (
                1.0 if production_context["aspect_ratio"] == "9:16" else 0.5
            ),
        }
        refs["human_review"] = {
            "required": True,
            "status": "pending",
            "checks": ["script_quality", "compliance_risk", "keyframe_identity"],
        }


def build_localization_exports(production_context: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_language": production_context["language"],
        "source_region": production_context["target_region"],
        "variants": ["source_subtitles", "localized_subtitles", "localized_dubbing"],
        "status": "not_started",
    }


def _target_platforms(target_region: str) -> list[str]:
    if target_region == "CN":
        return ["douyin", "kuaishou", "wechat_channels"]
    return ["tiktok", "youtube_shorts", "instagram_reels"]


def _hook_role(index: int, total: int) -> str:
    if index == 0:
        return "opening_hook"
    return "cliffhanger" if index == total - 1 else "conflict_turn"


def _first_text(beats: list[dict[str, Any]]) -> str:
    return next((text for beat in beats if (text := _text(beat))), "")


def _last_text(beats: list[dict[str, Any]]) -> str:
    return next((text for beat in reversed(beats) if (text := _text(beat))), "")


def _has_conflict_text(beat: dict[str, Any]) -> bool:
    markers = ("假", "证据", "反击", "背叛", "秘密", "除非", "威胁", "冲突")
    return any(marker in _text(beat) for marker in markers)


def _text(beat: dict[str, Any]) -> str:
    value = beat.get("text") or beat.get("beat_summary") or ""
    return value.strip() if isinstance(value, str) else ""
