from __future__ import annotations

from typing import Any

SHOT_PLAN_BATCH_SIZE = 8


def shot_plan_batch_max_tokens(clip_count: int) -> int:
    return min(12000, max(4000, clip_count * 1200))


def batched(
    items: list[dict[str, Any]],
    size: int,
) -> list[list[dict[str, Any]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def spec_for_video_clip_ids(
    spec: dict[str, Any],
    clip_ids: set[str],
) -> dict[str, Any]:
    scoped = dict(spec)
    scoped_tracks: list[Any] = []
    for track in spec.get("tracks") or []:
        if not isinstance(track, dict):
            scoped_tracks.append(track)
            continue
        if track.get("track_type") == "video" or track.get("type") == "video":
            scoped_tracks.append(
                {
                    **track,
                    "clips": [
                        clip
                        for clip in track.get("clips") or []
                        if isinstance(clip, dict)
                        and str(clip.get("clip_id")) in clip_ids
                    ],
                }
            )
        else:
            scoped_tracks.append(track)
    scoped["tracks"] = scoped_tracks
    return scoped


def plan_mismatch_errors(mismatch: dict[str, Any] | None) -> list[dict[str, Any]] | None:
    if mismatch is None:
        return None
    return [mismatch]


def invalid_batch_detail(
    result: dict[str, Any],
    *,
    batch_index: int,
    batch_count: int,
    clip_ids: list[str],
    max_tokens: int,
) -> dict[str, Any]:
    attempt = last_attempt(result)
    metadata = attempt.get("metadata") if isinstance(attempt.get("metadata"), dict) else {}
    return {
        "message": "timeline shot plan JSON invalid",
        "stage": "timeline_shot_plan",
        "batch_index": batch_index,
        "batch_count": batch_count,
        "clip_ids": clip_ids,
        "errors": safe_validation_errors(result.get("validation_errors")),
        "provider": attempt.get("provider_used"),
        "model": attempt.get("model_used"),
        "usage": attempt.get("usage") if isinstance(attempt.get("usage"), dict) else {},
        "finish_reason": metadata.get("finish_reason"),
        "max_tokens": max_tokens,
        "repair_attempts": len(result.get("repair_attempts") or []),
    }


def last_attempt(result: dict[str, Any]) -> dict[str, Any]:
    attempts = result.get("repair_attempts")
    if isinstance(attempts, list) and attempts:
        last = attempts[-1]
        return last if isinstance(last, dict) else {}
    first = result.get("first_attempt")
    return first if isinstance(first, dict) else {}


def safe_validation_errors(errors: Any) -> list[dict[str, Any]]:
    if not isinstance(errors, list):
        return []
    safe: list[dict[str, Any]] = []
    for item in errors:
        if not isinstance(item, dict):
            safe.append({"msg": str(item)})
            continue
        safe.append(
            {
                key: value
                for key, value in item.items()
                if key not in {"input", "ctx", "url"}
            }
        )
    return safe


def merge_usage(
    current: dict[str, Any],
    usage: Any,
) -> dict[str, Any]:
    if not isinstance(usage, dict):
        return current
    merged = dict(current)
    for key, value in usage.items():
        existing = merged.get(key)
        if isinstance(existing, int) and isinstance(value, int):
            merged[key] = existing + value
        elif key not in merged:
            merged[key] = value
    return merged
