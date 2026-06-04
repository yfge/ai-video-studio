"""Repository helpers for audio timeline persistence."""

from __future__ import annotations

from app.models.story_structure import Scene, SceneBeat
from sqlalchemy.orm import Session


def list_script_scenes(db: Session, script_id: int) -> list[Scene]:
    """Return all scenes for a script."""
    return (
        db.query(Scene)
        .filter(Scene.script_id == script_id, Scene.is_deleted.is_(False))
        .all()
    )


def list_scene_beats(db: Session, scene_ids: list[int]) -> list[SceneBeat]:
    """Return beats for the given scene IDs in timeline order."""
    if not scene_ids:
        return []
    return (
        db.query(SceneBeat)
        .filter(SceneBeat.scene_id.in_(scene_ids), SceneBeat.is_deleted.is_(False))
        .order_by(SceneBeat.scene_id.asc(), SceneBeat.order_index.asc())
        .all()
    )


def list_active_scene_beats(db: Session, scene_id: int) -> list[SceneBeat]:
    """Return active beats for one scene."""
    return (
        db.query(SceneBeat)
        .filter(
            SceneBeat.scene_id == scene_id,
            SceneBeat.is_deleted == False,  # noqa: E712
        )
        .all()
    )


def prune_soft_deleted_scene_beats(db: Session, scene_id: int) -> int:
    """Hard-delete soft-deleted generated beats before another overwrite."""
    return (
        db.query(SceneBeat)
        .filter(SceneBeat.scene_id == scene_id, SceneBeat.is_deleted.is_(True))
        .delete(synchronize_session="fetch")
    )


def count_scene_beats(db: Session, scene_id: int) -> int:
    """Return the number of beats persisted for a scene."""
    return (
        db.query(SceneBeat)
        .filter(SceneBeat.scene_id == scene_id, SceneBeat.is_deleted.is_(False))
        .count()
    )
