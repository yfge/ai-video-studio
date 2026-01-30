from __future__ import annotations

from typing import Optional, Sequence

from app.models.story_structure import Scene
from sqlalchemy.orm import Session, joinedload

from .storyboard_audio_context_utils import pick_first_url, truncate


def load_scene_environment_hints(
    db: Session,
    *,
    script_id: int,
    scene_ids: Sequence[int],
    scene_numbers: Sequence[int],
) -> tuple[
    dict[int, tuple[Optional[str], Optional[str]]],
    dict[int, tuple[Optional[str], Optional[str]]],
]:
    """Return (by_scene_id, by_scene_number) -> (env_url, env_hint)."""
    by_id: dict[int, tuple[Optional[str], Optional[str]]] = {}
    by_number: dict[int, tuple[Optional[str], Optional[str]]] = {}

    ids = sorted({int(i) for i in scene_ids if isinstance(i, int) and i > 0})
    nums = sorted({int(n) for n in scene_numbers if isinstance(n, int) and n > 0})

    scenes: list[Scene] = []
    if ids:
        scenes.extend(
            db.query(Scene)
            .options(joinedload(Scene.environment))
            .filter(Scene.id.in_(ids), Scene.is_deleted.is_(False))
            .all()
        )
    if nums:
        scenes.extend(
            db.query(Scene)
            .options(joinedload(Scene.environment))
            .filter(
                Scene.script_id == script_id,
                Scene.scene_number.in_([str(n) for n in nums]),
                Scene.is_deleted.is_(False),
            )
            .all()
        )

    for scene in scenes:
        try:
            scene_number_int = int(str(getattr(scene, "scene_number", "") or "0"))
        except Exception:
            scene_number_int = 0

        env = getattr(scene, "environment", None)
        env_url = pick_first_url(getattr(env, "reference_images", None) if env else None)
        env_name = str(getattr(env, "name", "") or "").strip() if env else ""

        location = str(getattr(scene, "location", "") or "").strip()
        time_of_day = str(getattr(scene, "time_of_day", "") or "").strip()
        slug_line = str(getattr(scene, "slug_line", "") or "").strip()

        hint_parts = [p for p in (env_name, location, time_of_day, slug_line) if p]
        env_hint = truncate("，".join(hint_parts), 160) if hint_parts else None

        scene_id_int = int(getattr(scene, "id"))
        by_id.setdefault(scene_id_int, (env_url, env_hint))
        if scene_number_int > 0:
            by_number.setdefault(scene_number_int, (env_url, env_hint))

    return by_id, by_number

