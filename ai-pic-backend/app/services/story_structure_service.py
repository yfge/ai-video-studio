from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.models.script import Script, Story
from app.models.story_structure import (
    Environment,
    Scene,
    SceneBeat,
    Shot,
    StoryStepOutline,
    StoryTreatment,
)
from app.schemas.story_structure import (
    SceneBeatCreate,
    SceneCreate,
    ShotCreate,
    StoryStepOutlineCreate,
    StoryTreatmentCreate,
)
from sqlalchemy.orm import Session


def _not_deleted(query, model):
    return query.filter(model.is_deleted == False)  # noqa: E712


def list_treatments_by_story(db: Session, story_id: int) -> List[StoryTreatment]:
    return (
        _not_deleted(db.query(StoryTreatment), StoryTreatment)
        .filter(StoryTreatment.story_id == story_id)
        .order_by(StoryTreatment.revision_number.desc())
        .all()
    )


def get_treatment(db: Session, treatment_id: int) -> Optional[StoryTreatment]:
    return (
        _not_deleted(db.query(StoryTreatment), StoryTreatment)
        .filter(StoryTreatment.id == treatment_id)
        .first()
    )


def create_treatment(db: Session, data: StoryTreatmentCreate) -> StoryTreatment:
    obj = StoryTreatment(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def ensure_auto_treatment(
    db: Session, story: Story, prompt_snapshot: Optional[dict[str, Any]] = None
) -> StoryTreatment:
    """
    Ensure a StoryTreatment row exists for the story.

    - If there is an existing non-deleted treatment, increment revision_number.
    - Otherwise create revision 1.
    """
    latest = (
        _not_deleted(db.query(StoryTreatment), StoryTreatment)
        .filter(StoryTreatment.story_id == story.id)
        .order_by(StoryTreatment.revision_number.desc())
        .first()
    )
    next_revision = (latest.revision_number + 1) if latest else 1
    title = (
        f"{story.title} Step Outline v{next_revision}"
        if story.title
        else f"Step Outline v{next_revision}"
    )
    treatment = StoryTreatment(
        story_id=story.id,
        revision_number=next_revision,
        status="draft",
        title=title[:255],
        logline=story.premise or story.synopsis,
        theme_summary=story.theme,
        ai_prompt_snapshot=prompt_snapshot,
    )
    db.add(treatment)
    db.commit()
    db.refresh(treatment)
    return treatment


def list_step_outlines(db: Session, treatment_id: int) -> List[StoryStepOutline]:
    return (
        _not_deleted(db.query(StoryStepOutline), StoryStepOutline)
        .filter(StoryStepOutline.story_treatment_id == treatment_id)
        .order_by(StoryStepOutline.sequence_number.asc())
        .all()
    )


def create_step_outline(db: Session, data: StoryStepOutlineCreate) -> StoryStepOutline:
    obj = StoryStepOutline(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def bulk_create_step_outlines(
    db: Session, rows: List[StoryStepOutlineCreate]
) -> List[StoryStepOutline]:
    """Insert multiple step outlines in one transaction."""
    if not rows:
        return []
    objects: List[StoryStepOutline] = []
    for row in rows:
        obj = StoryStepOutline(**row.model_dump())
        db.add(obj)
        objects.append(obj)
    db.commit()
    for obj in objects:
        db.refresh(obj)
    return objects


def list_scenes_by_script(db: Session, script_id: int) -> List[Scene]:
    return (
        _not_deleted(db.query(Scene), Scene)
        .filter(Scene.script_id == script_id)
        .order_by(Scene.scene_number.asc())
        .all()
    )


def get_scene(db: Session, scene_id: int) -> Optional[Scene]:
    """Get scene by numeric id."""
    return _not_deleted(db.query(Scene), Scene).filter(Scene.id == scene_id).first()


def get_scene_by_business_id(db: Session, business_id: str) -> Optional[Scene]:
    """Get scene by business_id."""
    return (
        _not_deleted(db.query(Scene), Scene)
        .filter(Scene.business_id == business_id)
        .first()
    )


def resolve_scene(db: Session, identifier: int | str | None) -> Optional[Scene]:
    """Resolve scene by id or business_id."""
    if identifier is None:
        return None
    if isinstance(identifier, int):
        return get_scene(db, identifier)
    try:
        int_id = int(str(identifier))
        scene = get_scene(db, int_id)
        if scene:
            return scene
    except ValueError:
        pass
    return get_scene_by_business_id(db, str(identifier))


def get_shot(db: Session, shot_id: int) -> Optional[Shot]:
    """Get shot by numeric id."""
    return _not_deleted(db.query(Shot), Shot).filter(Shot.id == shot_id).first()


def get_shot_by_business_id(db: Session, business_id: str) -> Optional[Shot]:
    """Get shot by business_id."""
    return (
        _not_deleted(db.query(Shot), Shot)
        .filter(Shot.business_id == business_id)
        .first()
    )


def resolve_shot(db: Session, identifier: int | str | None) -> Optional[Shot]:
    """Resolve shot by id or business_id."""
    if identifier is None:
        return None
    if isinstance(identifier, int):
        return get_shot(db, identifier)
    try:
        int_id = int(str(identifier))
        shot = get_shot(db, int_id)
        if shot:
            return shot
    except ValueError:
        pass
    return get_shot_by_business_id(db, str(identifier))


def get_scene_beat(db: Session, beat_id: int) -> Optional[SceneBeat]:
    """Get scene beat by numeric id."""
    return (
        _not_deleted(db.query(SceneBeat), SceneBeat)
        .filter(SceneBeat.id == beat_id)
        .first()
    )


def get_scene_beat_by_business_id(db: Session, business_id: str) -> Optional[SceneBeat]:
    """Get scene beat by business_id."""
    return (
        _not_deleted(db.query(SceneBeat), SceneBeat)
        .filter(SceneBeat.business_id == business_id)
        .first()
    )


def resolve_scene_beat(
    db: Session, identifier: int | str | None
) -> Optional[SceneBeat]:
    """Resolve scene beat by id or business_id."""
    if identifier is None:
        return None
    if isinstance(identifier, int):
        return get_scene_beat(db, identifier)
    try:
        int_id = int(str(identifier))
        beat = get_scene_beat(db, int_id)
        if beat:
            return beat
    except ValueError:
        pass
    return get_scene_beat_by_business_id(db, str(identifier))


def get_script_structure(db: Session, script_id: int) -> Optional[List[Dict[str, Any]]]:
    script = (
        _not_deleted(db.query(Script), Script).filter(Script.id == script_id).first()
    )
    if not script:
        return None

    scenes = list_scenes_by_script(db, script_id)
    if not scenes:
        return []

    scene_ids = [s.id for s in scenes]
    beats = (
        _not_deleted(db.query(SceneBeat), SceneBeat)
        .filter(SceneBeat.scene_id.in_(scene_ids))
        .order_by(SceneBeat.scene_id.asc(), SceneBeat.order_index.asc())
        .all()
    )
    shots = (
        _not_deleted(db.query(Shot), Shot)
        .filter(Shot.scene_id.in_(scene_ids))
        .order_by(Shot.scene_id.asc(), Shot.shot_number.asc())
        .all()
    )

    beats_by_scene: Dict[int, List[SceneBeat]] = {sid: [] for sid in scene_ids}
    for beat in beats:
        beats_by_scene.setdefault(beat.scene_id, []).append(beat)

    shots_by_scene: Dict[int, List[Shot]] = {sid: [] for sid in scene_ids}
    for shot in shots:
        shots_by_scene.setdefault(shot.scene_id, []).append(shot)

    assembled: List[Dict[str, Any]] = []
    for scene in scenes:
        assembled.append(
            {
                "scene": scene,
                "beats": beats_by_scene.get(scene.id, []),
                "shots": shots_by_scene.get(scene.id, []),
            }
        )
    return assembled


def create_scene(db: Session, data: SceneCreate) -> Scene:
    # ensure script exists
    script = (
        _not_deleted(db.query(Script), Script)
        .filter(Script.id == data.script_id)
        .first()
    )
    if not script:
        raise ValueError("script_not_found")
    if data.environment_id:
        env = (
            _not_deleted(db.query(Environment), Environment)
            .filter(Environment.id == data.environment_id)
            .first()
        )
        if not env:
            raise ValueError("environment_not_found")
    obj = Scene(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_beats_by_scene(db: Session, scene_id: int) -> List[SceneBeat]:
    return (
        _not_deleted(db.query(SceneBeat), SceneBeat)
        .filter(SceneBeat.scene_id == scene_id)
        .order_by(SceneBeat.order_index.asc())
        .all()
    )


def create_scene_beat(db: Session, data: SceneBeatCreate) -> SceneBeat:
    scene = (
        _not_deleted(db.query(Scene), Scene).filter(Scene.id == data.scene_id).first()
    )
    if not scene:
        raise ValueError("scene_not_found")
    # enforce unique order_index within scene (only among non-deleted beats)
    existing = (
        _not_deleted(db.query(SceneBeat), SceneBeat)
        .filter(
            SceneBeat.scene_id == data.scene_id,
            SceneBeat.order_index == data.order_index,
        )
        .first()
    )
    if existing:
        raise ValueError("duplicate_order_index")
    obj = SceneBeat(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_shots_by_scene(db: Session, scene_id: int) -> List[Shot]:
    return (
        _not_deleted(db.query(Shot), Shot)
        .filter(Shot.scene_id == scene_id)
        .order_by(Shot.shot_number.asc())
        .all()
    )


def create_shot(db: Session, data: ShotCreate) -> Shot:
    scene = (
        _not_deleted(db.query(Scene), Scene).filter(Scene.id == data.scene_id).first()
    )
    if not scene:
        raise ValueError("scene_not_found")
    # enforce shot_number uniqueness per scene (only among non-deleted shots)
    exists = (
        _not_deleted(db.query(Shot), Shot)
        .filter(Shot.scene_id == data.scene_id, Shot.shot_number == data.shot_number)
        .first()
    )
    if exists:
        raise ValueError("duplicate_shot_number")
    if data.scene_beat_id:
        beat = (
            _not_deleted(db.query(SceneBeat), SceneBeat)
            .filter(SceneBeat.id == data.scene_beat_id)
            .first()
        )
        if not beat or beat.scene_id != data.scene_id:
            raise ValueError("beat_scene_mismatch")
    obj = Shot(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def create_scene_with_children(
    db: Session,
    scene_data: SceneCreate,
    beats: Optional[List[SceneBeatCreate]] = None,
    shots: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Create scene plus optional beats/shots in one transaction."""
    if scene_data.environment_id:
        env = (
            _not_deleted(db.query(Environment), Environment)
            .filter(Environment.id == scene_data.environment_id)
            .first()
        )
        if not env:
            raise ValueError("environment_not_found")
    scene = Scene(**scene_data.model_dump())
    db.add(scene)
    db.flush()

    beat_map: Dict[int, int] = {}
    created_beats: List[SceneBeat] = []
    for beat in beats or []:
        beat_obj = SceneBeat(
            scene_id=scene.id,
            order_index=beat.order_index,
            beat_type=beat.beat_type,
            beat_summary=beat.beat_summary,
            characters_involved=beat.characters_involved,
            dialogue_excerpt=beat.dialogue_excerpt,
            camera_notes=beat.camera_notes,
            duration_seconds=beat.duration_seconds,
            extra_metadata=beat.metadata,
        )
        db.add(beat_obj)
        db.flush()
        beat_map[beat.order_index] = beat_obj.id
        created_beats.append(beat_obj)

    created_shots: List[Shot] = []
    for raw in shots or []:
        # Accept either ShotCreate or dict; support mapping by beat order when id missing.
        if isinstance(raw, ShotCreate):
            shot_data = raw.model_dump()
        else:
            shot_data = dict(raw)
        target_scene_beat_id = shot_data.get("scene_beat_id")
        beat_order = shot_data.get("scene_beat_order_index")
        if not target_scene_beat_id and beat_order is not None:
            target_scene_beat_id = beat_map.get(int(beat_order))

        shot_obj = Shot(
            scene_id=scene.id,
            scene_beat_id=target_scene_beat_id,
            shot_number=shot_data["shot_number"],
            shot_type=shot_data.get("shot_type"),
            camera_setup=shot_data.get("camera_setup"),
            camera_movement=shot_data.get("camera_movement"),
            framing=shot_data.get("framing"),
            focus_subject=shot_data.get("focus_subject"),
            duration_seconds=shot_data.get("duration_seconds"),
            storyboard_frame_asset_id=shot_data.get("storyboard_frame_asset_id"),
            lighting_notes=shot_data.get("lighting_notes"),
            audio_notes=shot_data.get("audio_notes"),
            status=shot_data.get("status", "planned"),
            extra_metadata=shot_data.get("metadata"),
        )
        db.add(shot_obj)
        db.flush()
        created_shots.append(shot_obj)

    db.commit()
    db.refresh(scene)
    for obj in created_beats + created_shots:
        db.refresh(obj)

    return {"scene": scene, "beats": created_beats, "shots": created_shots}


def update_scene(
    db: Session, scene_id: int, payload: Dict[str, Any]
) -> Optional[Scene]:
    obj = _not_deleted(db.query(Scene), Scene).filter(Scene.id == scene_id).first()
    if not obj:
        return None
    if "environment_id" in payload and payload["environment_id"]:
        env = (
            _not_deleted(db.query(Environment), Environment)
            .filter(Environment.id == payload["environment_id"])
            .first()
        )
        if not env:
            raise ValueError("environment_not_found")
    for field, value in payload.items():
        if value is not None and hasattr(obj, field):
            setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_scene(
    db: Session, scene_id: int, *, user_id: int | None = None, reason: str | None = None
) -> bool:
    """Soft delete a scene and its children (shots, scene_beats)."""
    obj = _not_deleted(db.query(Scene), Scene).filter(Scene.id == scene_id).first()
    if not obj:
        return False
    # Soft delete children
    for shot in (
        _not_deleted(db.query(Shot), Shot).filter(Shot.scene_id == scene_id).all()
    ):
        shot.soft_delete(user_id=user_id, reason=reason or "parent_scene_deleted")
    for beat in (
        _not_deleted(db.query(SceneBeat), SceneBeat)
        .filter(SceneBeat.scene_id == scene_id)
        .all()
    ):
        beat.soft_delete(user_id=user_id, reason=reason or "parent_scene_deleted")
    obj.soft_delete(user_id=user_id, reason=reason)
    db.commit()
    return True


def update_scene_beat(
    db: Session, beat_id: int, payload: Dict[str, Any]
) -> Optional[SceneBeat]:
    obj = (
        _not_deleted(db.query(SceneBeat), SceneBeat)
        .filter(SceneBeat.id == beat_id)
        .first()
    )
    if not obj:
        return None
    # handle order_index conflict (only among non-deleted beats)
    new_order = payload.get("order_index")
    if new_order is not None and new_order != obj.order_index:
        conflict = (
            _not_deleted(db.query(SceneBeat), SceneBeat)
            .filter(
                SceneBeat.scene_id == obj.scene_id, SceneBeat.order_index == new_order
            )
            .first()
        )
        if conflict:
            raise ValueError("duplicate_order_index")
    for field, value in payload.items():
        if value is not None and hasattr(obj, field):
            setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_scene_beat(
    db: Session, beat_id: int, *, user_id: int | None = None, reason: str | None = None
) -> bool:
    """Soft delete a scene beat."""
    obj = (
        _not_deleted(db.query(SceneBeat), SceneBeat)
        .filter(SceneBeat.id == beat_id)
        .first()
    )
    if not obj:
        return False
    obj.soft_delete(user_id=user_id, reason=reason)
    db.commit()
    return True


def update_shot(db: Session, shot_id: int, payload: Dict[str, Any]) -> Optional[Shot]:
    obj = _not_deleted(db.query(Shot), Shot).filter(Shot.id == shot_id).first()
    if not obj:
        return None
    new_number = payload.get("shot_number")
    if new_number and new_number != obj.shot_number:
        conflict = (
            _not_deleted(db.query(Shot), Shot)
            .filter(Shot.scene_id == obj.scene_id, Shot.shot_number == new_number)
            .first()
        )
        if conflict:
            raise ValueError("duplicate_shot_number")
    if "scene_beat_id" in payload and payload["scene_beat_id"]:
        beat = (
            _not_deleted(db.query(SceneBeat), SceneBeat)
            .filter(SceneBeat.id == payload["scene_beat_id"])
            .first()
        )
        if not beat or beat.scene_id != obj.scene_id:
            raise ValueError("beat_scene_mismatch")
    for field, value in payload.items():
        if value is not None and hasattr(obj, field):
            setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_shot(
    db: Session, shot_id: int, *, user_id: int | None = None, reason: str | None = None
) -> bool:
    """Soft delete a shot."""
    obj = _not_deleted(db.query(Shot), Shot).filter(Shot.id == shot_id).first()
    if not obj:
        return False
    obj.soft_delete(user_id=user_id, reason=reason)
    db.commit()
    return True


# Environment CRUD


def list_environments(db: Session, owner_id: int | None = None) -> List[Environment]:
    query = _not_deleted(db.query(Environment), Environment)
    if owner_id is not None:
        query = query.filter(Environment.user_id == owner_id)
    return query.order_by(Environment.id.asc()).all()


def get_environment(db: Session, env_id: int) -> Optional[Environment]:
    return (
        _not_deleted(db.query(Environment), Environment)
        .filter(Environment.id == env_id)
        .first()
    )


def get_environment_by_business_id(
    db: Session, business_id: str
) -> Optional[Environment]:
    return (
        _not_deleted(db.query(Environment), Environment)
        .filter(Environment.business_id == business_id)
        .first()
    )


def resolve_environment(
    db: Session, env_identifier: int | str | None
) -> Optional[Environment]:
    if env_identifier is None:
        return None
    env: Optional[Environment] = None
    # prefer numeric id if provided
    if isinstance(env_identifier, int):
        env = get_environment(db, env_identifier)
    else:
        try:
            env_int = int(str(env_identifier))
        except Exception:
            env_int = None
        if env_int is not None:
            env = get_environment(db, env_int)
        if not env:
            env = get_environment_by_business_id(db, str(env_identifier))
    return env


def create_environment(db: Session, payload: Dict[str, Any]) -> Environment:
    env = Environment(**payload)
    db.add(env)
    db.commit()
    db.refresh(env)
    return env


def update_environment(
    db: Session, env_id: int | str, payload: Dict[str, Any]
) -> Optional[Environment]:
    env = resolve_environment(db, env_id)
    if not env:
        return None
    for k, v in payload.items():
        setattr(env, k, v)
    db.commit()
    db.refresh(env)
    return env


def delete_environment(
    db: Session,
    env_id: int | str,
    *,
    user_id: int | None = None,
    reason: str | None = None,
) -> bool:
    """Soft delete an environment."""
    env = resolve_environment(db, env_id)
    if not env:
        return False
    env.soft_delete(user_id=user_id, reason=reason)
    db.commit()
    return True


def _to_slug_line(item: dict[str, Any]) -> str:
    time = (item.get("time") or "").upper()
    location = item.get("location") or "UNKNOWN"
    segs = [s for s in [time, location] if s]
    return " ".join(segs) or "SCENE"


def _to_scene_number_str(idx: int, item: dict[str, Any]) -> str:
    num = item.get("scene_number")
    if isinstance(num, int) and num > 0:
        return str(num)
    try:
        if isinstance(num, str) and num.strip():
            n = int(num)
            if n > 0:
                return str(n)
    except Exception:
        pass
    return str(idx + 1)


def seed_scenes_from_script_json(
    db: Session, script_id: int, *, dry_run: bool = False
) -> int:
    """Seed `scenes` rows from `Script.scenes` JSON for given script.

    Returns number of prepared/inserted rows.
    """
    script = (
        _not_deleted(db.query(Script), Script).filter(Script.id == script_id).first()
    )
    if not script:
        return 0
    source_scenes: List[dict[str, Any]] = list(script.scenes or [])  # type: ignore
    if not source_scenes:
        return 0

    existing = (
        _not_deleted(db.query(Scene), Scene).filter(Scene.script_id == script_id).all()
    )
    existing_keys = {(s.scene_number) for s in existing}

    to_insert: List[Scene] = []
    for idx, item in enumerate(source_scenes):
        sn = _to_scene_number_str(idx, item)
        if sn in existing_keys:
            continue
        sc = Scene(
            script_id=script_id,
            scene_number=sn,
            slug_line=_to_slug_line(item),
            environment_type=None,
            location=item.get("location"),
            time_of_day=item.get("time"),
            summary=item.get("description"),
            page_length_eighths=None,
            primary_characters=None,
            conflict_notes=None,
            ai_prompt_snapshot=None,
            status="draft",
            extra_metadata=None,
        )
        to_insert.append(sc)

    if not to_insert:
        return 0
    if dry_run:
        return len(to_insert)

    db.add_all(to_insert)
    db.commit()
    return len(to_insert)
