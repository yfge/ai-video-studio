"""Timeline asset attachment helpers for provider-chain regression."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


def attach_timeline_video_assets(
    seed_spec: dict[str, Any],
    clips: list[dict[str, Any]],
    run_id: str,
    dialogue_audio: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec = deepcopy(seed_spec)
    if dialogue_audio:
        attach_timeline_dialogue_audio(spec, dialogue_audio, run_id)
    generated_by_id = {clip.get("clip_id"): clip for clip in clips}
    attached_ids: set[str] = set()
    missing_ids: list[str] = []
    for clip in _track_clips(spec, "video"):
        generated = generated_by_id.get(clip.get("clip_id"))
        if not generated:
            missing_ids.append(str(clip.get("clip_id")))
            continue
        attached_ids.add(str(clip.get("clip_id")))
        _attach_video_asset(clip, generated, run_id)
    unused_ids = {
        str(clip_id) for clip_id in generated_by_id if clip_id not in attached_ids
    }
    if missing_ids or unused_ids:
        raise RuntimeError(
            "timeline_asset_lineage_mismatch: "
            f"missing={sorted(missing_ids)} unused={sorted(unused_ids)}"
        )
    return spec


def attach_timeline_dialogue_audio(
    spec: dict[str, Any],
    dialogue_audio: dict[str, Any],
    run_id: str,
) -> None:
    audio_by_clip_id = {
        str(item.get("clip_id")): item
        for item in dialogue_audio.get("clips") or []
        if isinstance(item, dict) and item.get("clip_id")
    }
    if not audio_by_clip_id:
        raise RuntimeError("dialogue_audio_missing_clips")
    source = spec.setdefault("source", {})
    if isinstance(source, dict):
        source["dialogue_audio"] = {
            "mode": "per_clip",
            "clip_count": len(audio_by_clip_id),
            "provider": dialogue_audio.get("provider"),
            "model": dialogue_audio.get("model"),
            "run_id": run_id,
        }
        source.pop("episode_audio", None)
    attached_ids: set[str] = set()
    missing_ids: list[str] = []
    for clip in _track_clips(spec, "dialogue"):
        clip_id = str(clip.get("clip_id") or "")
        generated = audio_by_clip_id.get(clip_id)
        if not generated:
            missing_ids.append(clip_id)
            continue
        attached_ids.add(clip_id)
        _attach_dialogue_asset(clip, generated, dialogue_audio, run_id)
    unused_ids = {
        clip_id for clip_id in audio_by_clip_id if clip_id not in attached_ids
    }
    if missing_ids or unused_ids:
        raise RuntimeError(
            "timeline_dialogue_audio_lineage_mismatch: "
            f"missing={sorted(missing_ids)} unused={sorted(unused_ids)}"
        )


def _attach_dialogue_asset(
    clip: dict[str, Any],
    generated: dict[str, Any],
    dialogue_audio: dict[str, Any],
    run_id: str,
) -> None:
    audio_url = str(generated.get("audio_url") or "")
    if not audio_url.startswith(("http://", "https://")):
        raise RuntimeError(f"dialogue_audio_missing_public_url: {clip.get('clip_id')}")
    clip["asset_ref"] = {
        "kind": "provider_chain_dialogue_clip_audio",
        "url": audio_url,
        "file_url": audio_url,
        "provider": dialogue_audio.get("provider"),
        "model": dialogue_audio.get("model"),
        "start_ms": generated.get("start_ms"),
        "end_ms": generated.get("end_ms"),
    }
    refs = clip.setdefault("source_refs", {})
    refs.update(
        {
            "provider_chain_run_id": run_id,
            "provider_chain_stage": "dialogue_audio_generated",
            "audio_url": audio_url,
            "audio_provider": dialogue_audio.get("provider"),
            "audio_model": dialogue_audio.get("model"),
        }
    )


def _attach_video_asset(
    clip: dict[str, Any],
    generated: dict[str, Any],
    run_id: str,
) -> None:
    clip["placeholder"] = False
    clip["video_url"] = generated["video_url"]
    clip["asset_ref"] = {
        "kind": "provider_chain_video",
        "url": generated["video_url"],
        "file_url": generated["video_url"],
        "provider": generated["provider"],
        "model": generated["model"],
        "task_id": generated.get("task_id"),
    }
    refs = clip.setdefault("source_refs", {})
    refs.update(
        {
            "provider_chain_run_id": run_id,
            "provider_chain_stage": "video_generated",
            "image_url": generated.get("image_url"),
            "video_url": generated["video_url"],
            "task_id": generated.get("task_id"),
            "provider": generated["provider"],
            "model": generated["model"],
        }
    )


def _track_clips(spec: dict[str, Any], track_type: str) -> list[dict[str, Any]]:
    for track in spec.get("tracks") or []:
        if isinstance(track, dict) and track.get("track_type") == track_type:
            return [clip for clip in track.get("clips") or [] if isinstance(clip, dict)]
    return []
