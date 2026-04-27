"""Episode audio timeline builder.

Concatenates scene dialogue tracks into one episode track
and merges beats into an episode timeline.
"""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene, SceneBeat
from app.repositories.audio_timeline_repository import (
    list_scene_beats,
    list_script_scenes,
)
from app.services.audio.audio_generator import (
    concat_mp3s,
    download_to_file,
    ensure_oss_configured,
)
from app.services.audio.episode_timeline_beats import build_episode_timeline_beats
from app.services.storage.oss_service import oss_service
from sqlalchemy.orm import Session

logger = get_logger(__name__)


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


async def generate_episode_audio_timeline(
    db: Session,
    *,
    story: Story,
    episode: Episode,
    script: Script,
) -> dict[str, Any]:
    """Concatenate scene dialogue tracks into 1 episode track and merge beats."""
    ensure_oss_configured()

    scenes = list_script_scenes(db, script.id)
    scenes_sorted = sorted(
        scenes,
        key=lambda s: (
            1 if str(getattr(s, "scene_number", "")).strip().isdigit() is False else 0,
            (
                int(str(getattr(s, "scene_number", 0)).strip())
                if str(getattr(s, "scene_number", "")).strip().isdigit()
                else 0
            ),
            str(getattr(s, "scene_number", "")),
        ),
    )
    if not scenes_sorted:
        raise RuntimeError("no_scenes_found")

    scene_audio_urls, scene_ids, missing_audio = _collect_scene_audio(scenes_sorted)
    if missing_audio:
        raise RuntimeError(f"missing_scene_dialogue_audio: {', '.join(missing_audio)}")

    beats_by_scene = _load_scene_beats(db, scenes_sorted, scene_ids)

    timeline_beats, duration_ms_total = build_episode_timeline_beats(
        scenes=scenes_sorted,
        beats_by_scene_id=beats_by_scene,
    )
    duration_seconds_total = round(duration_ms_total / 1000.0, 3)
    _log_duration(episode, script, duration_ms_total, duration_seconds_total)

    with tempfile.TemporaryDirectory(prefix="episode-audio-") as tmp_root:
        tmp_root_path = Path(tmp_root)
        mp3_paths: list[Path] = []
        for idx, url in enumerate(scene_audio_urls, start=1):
            p = tmp_root_path / f"scene-{idx}.mp3"
            await download_to_file(str(url), p)
            mp3_paths.append(p)

        episode_mp3 = tmp_root_path / "episode.mp3"
        concat_mp3s(mp3_paths, episode_mp3)

        oss_result = await oss_service.upload_file_content(
            file_content=episode_mp3.read_bytes(),
            filename=f"episode{episode.id}-script{script.id}.mp3",
            file_type="audio",
            prefix="episode-dialogue/episodes",
            metadata={
                "episode_id": episode.id,
                "script_id": script.id,
                "duration_seconds": duration_seconds_total,
                "generated_at": _utc_now_iso(),
            },
        )
        if not oss_result.get("success") or not oss_result.get("file_url"):
            raise RuntimeError(f"OSS 上传失败: {oss_result}")

    return _persist_episode_timeline(
        db,
        episode,
        script,
        oss_result,
        duration_seconds_total,
        timeline_beats,
    )


def _collect_scene_audio(
    scenes_sorted: list[Scene],
) -> tuple[list[str], list[int], list[str]]:
    """Collect audio URLs from scene metadata."""
    urls: list[str] = []
    ids: list[int] = []
    missing: list[str] = []
    for scene in scenes_sorted:
        meta = scene.extra_metadata if isinstance(scene.extra_metadata, dict) else {}
        payload = meta.get("dialogue_audio") if isinstance(meta, dict) else None
        if not isinstance(payload, dict) or not payload.get("oss_url"):
            missing.append(str(scene.scene_number))
            continue
        urls.append(str(payload["oss_url"]))
        ids.append(int(scene.id))
    return urls, ids, missing


def _load_scene_beats(
    db: Session,
    scenes_sorted: list[Scene],
    scene_ids: list[int],
) -> dict[int, list[SceneBeat]]:
    """Load and group scene beats, raising on missing data."""
    beats = list_scene_beats(db, scene_ids)
    by_scene: dict[int, list[SceneBeat]] = {sid: [] for sid in scene_ids}
    for beat in beats:
        by_scene.setdefault(int(beat.scene_id), []).append(beat)

    missing = [
        str(scene.scene_number)
        for scene in scenes_sorted
        if not by_scene.get(int(scene.id))
    ]
    if missing:
        raise RuntimeError(f"missing_scene_beats: {', '.join(missing)}")
    return by_scene


def _log_duration(
    episode: Episode,
    script: Script,
    duration_ms: int,
    duration_seconds: float,
) -> None:
    episode_duration_minutes = getattr(episode, "duration_minutes", None)
    if not episode_duration_minutes:
        return
    target_ms = episode_duration_minutes * 60 * 1000
    target_seconds = episode_duration_minutes * 60
    ratio = duration_ms / target_ms if target_ms > 0 else 0
    logger.info(
        "Episode timeline duration validation",
        extra={
            "episode_id": episode.id,
            "script_id": script.id,
            "target_duration_minutes": episode_duration_minutes,
            "target_duration_ms": target_ms,
            "actual_duration_ms": duration_ms,
            "actual_duration_seconds": duration_seconds,
            "duration_ratio": round(ratio, 2),
            "within_tolerance": 0.85 <= ratio <= 1.15,
        },
    )
    if ratio < 0.85:
        logger.warning(
            f"Timeline too short: {duration_seconds}s "
            f"vs target {target_seconds}s ({ratio:.0%})"
        )
    elif ratio > 1.15:
        logger.warning(
            f"Timeline too long: {duration_seconds}s "
            f"vs target {target_seconds}s ({ratio:.0%})"
        )


def _persist_episode_timeline(
    db: Session,
    episode: Episode,
    script: Script,
    oss_result: dict,
    duration_seconds: float,
    timeline_beats: list[dict[str, Any]],
) -> dict[str, Any]:
    extra = dict(episode.extra_metadata or {})
    prev = extra.get("audio_timeline")
    prev_version = 0
    if isinstance(prev, dict):
        ep_audio = prev.get("episode_audio")
        if isinstance(ep_audio, dict):
            try:
                prev_version = int(ep_audio.get("version") or 0)
            except Exception:
                prev_version = 0

    payload = {
        "script_id": script.id,
        "episode_audio": {
            "oss_url": oss_result["file_url"],
            "duration_seconds": duration_seconds,
            "generated_at": _utc_now_iso(),
            "version": prev_version + 1,
        },
        "beats": timeline_beats,
    }
    extra["audio_timeline"] = payload
    episode.extra_metadata = extra
    db.add(episode)
    db.commit()
    db.refresh(episode)
    return payload
