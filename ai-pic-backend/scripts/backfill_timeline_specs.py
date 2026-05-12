#!/usr/bin/env python3
"""Backfill Timeline Spec v1 rows from legacy episode audio timelines.

Safe defaults:
- Dry-run by default.
- Requires --apply to write Timeline rows.
- Scans episodes with legacy episodes.extra_metadata.audio_timeline and imports
  only when no active Timeline exists for the matching episode/script pair.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, joinedload

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.database import SessionLocal  # noqa: E402
from app.models.script import Episode, Script, Story  # noqa: E402
from app.repositories.timeline_repository import TimelineRepository  # noqa: E402
from app.services.timeline_import_service import (  # noqa: E402
    import_audio_timeline_to_timeline_spec,
)


def backfill_timeline_specs(
    session: Session,
    *,
    apply: bool = False,
    user_id: int | None = None,
    episode_id: int | None = None,
    script_id: int | None = None,
    limit: int = 500,
) -> Counter[str]:
    counters: Counter[str] = Counter()
    timelines = TimelineRepository(session)
    query = (
        session.query(Episode)
        .join(Story, Episode.story_id == Story.id)
        .options(joinedload(Episode.story), joinedload(Episode.scripts))
        .filter(Episode.is_deleted.is_(False), Story.is_deleted.is_(False))
        .order_by(Episode.id.asc())
    )
    if user_id is not None:
        query = query.filter(Story.user_id == user_id)
    if episode_id is not None:
        query = query.filter(Episode.id == episode_id)
    if script_id is not None:
        query = query.join(Script, Script.episode_id == Episode.id).filter(
            Script.id == script_id,
            Script.is_deleted.is_(False),
        )

    for episode in query.limit(limit).all():
        counters["scanned"] += 1
        audio_timeline = _episode_audio_timeline(episode)
        if audio_timeline is None:
            counters["skipped"] += 1
            counters["no_audio_timeline"] += 1
            continue

        timeline_script_id = _maybe_int(audio_timeline.get("script_id"))
        script = _script_for_episode(episode, timeline_script_id)
        if script is None or (script_id is not None and script.id != script_id):
            counters["script_mismatch"] += 1
            continue

        existing = timelines.get_latest_for_episode_script(
            episode_id=episode.id,
            script_id=script.id,
        )
        if existing is not None:
            counters["skipped"] += 1
            counters["already_has_timeline"] += 1
            continue

        if not apply:
            counters["would_create"] += 1
            continue

        try:
            result = import_audio_timeline_to_timeline_spec(
                session,
                episode=episode,
                script=script,
                audio_timeline=audio_timeline,
                overwrite=False,
                user_id=getattr(episode.story, "user_id", None),
            )
        except Exception:
            session.rollback()
            counters["failed"] += 1
            continue
        counters[result.action] += 1

    return counters


def _episode_audio_timeline(episode: Episode) -> dict[str, Any] | None:
    meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    timeline = meta.get("audio_timeline")
    if not isinstance(timeline, dict):
        return None
    beats = timeline.get("beats")
    episode_audio = timeline.get("episode_audio")
    if not isinstance(beats, list) or not beats:
        return None
    if not isinstance(episode_audio, dict) or not episode_audio.get("oss_url"):
        return None
    return timeline


def _script_for_episode(episode: Episode, script_id: int | None) -> Script | None:
    if script_id is None:
        return None
    for script in episode.scripts or []:
        if script.id == script_id and not getattr(script, "is_deleted", False):
            return script
    return None


def _maybe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backfill Timeline Spec v1 rows from legacy audio_timeline data"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write Timeline rows (default: dry-run only)",
    )
    parser.add_argument("--user-id", type=int, default=None)
    parser.add_argument("--episode-id", type=int, default=None)
    parser.add_argument("--script-id", type=int, default=None)
    parser.add_argument("--limit", type=int, default=500)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = SessionLocal()
    try:
        counters = backfill_timeline_specs(
            session,
            apply=args.apply,
            user_id=args.user_id,
            episode_id=args.episode_id,
            script_id=args.script_id,
            limit=args.limit,
        )
        payload = {"apply": args.apply, **dict(counters)}
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
