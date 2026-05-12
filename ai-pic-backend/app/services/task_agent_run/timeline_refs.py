from __future__ import annotations

from typing import Any


def timeline_ref_for_script(db, script) -> dict[str, Any]:
    episode_id = getattr(script, "episode_id", None)
    script_id = getattr(script, "id", None)
    if episode_id is None or script_id is None:
        return {}

    from app.repositories.timeline_repository import TimelineRepository

    timeline = TimelineRepository(db).get_latest_for_episode_script(
        episode_id=episode_id,
        script_id=script_id,
    )
    if timeline is None:
        return {}
    return {
        "timeline_id": getattr(timeline, "id", None),
        "timeline_version": getattr(timeline, "version", None),
        "timeline_status": getattr(timeline, "status", None),
        "source_audio_timeline_version": getattr(
            timeline, "source_audio_timeline_version", None
        ),
    }
