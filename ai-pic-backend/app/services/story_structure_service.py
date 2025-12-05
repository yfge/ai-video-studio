from __future__ import annotations

from typing import List, Optional, Any, Dict

from sqlalchemy.orm import Session

from app.models.story_structure import (
    StoryTreatment,
    StoryStepOutline,
    Scene,
    SceneBeat,
    Shot,
)
from app.models.script import Script
from app.schemas.story_structure import (
    StoryTreatmentCreate,
    StoryStepOutlineCreate,
    SceneCreate,
    SceneBeatCreate,
    ShotCreate,
)


def list_treatments_by_story(db: Session, story_id: int) -> List[StoryTreatment]:
    return (
        db.query(StoryTreatment)
        .filter(
            StoryTreatment.story_id == story_id, StoryTreatment.is_deleted == False
        )  # noqa: E712
        .order_by(StoryTreatment.revision_number.desc())
        .all()
    )


def get_treatment(db: Session, treatment_id: int) -> Optional[StoryTreatment]:
    return (
        db.query(StoryTreatment)
        .filter(
            StoryTreatment.id == treatment_id, StoryTreatment.is_deleted == False
        )  # noqa: E712
        .first()
    )


def create_treatment(db: Session, data: StoryTreatmentCreate) -> StoryTreatment:
    obj = StoryTreatment(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_step_outlines(db: Session, treatment_id: int) -> List[StoryStepOutline]:
    return (
        db.query(StoryStepOutline)
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


def list_scenes_by_script(db: Session, script_id: int) -> List[Scene]:
    return (
        db.query(Scene)
        .filter(Scene.script_id == script_id)
        .order_by(Scene.scene_number.asc())
        .all()
    )


def get_script_structure(db: Session, script_id: int) -> Optional[List[Dict[str, Any]]]:
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        return None

    scenes = list_scenes_by_script(db, script_id)
    if not scenes:
        return []

    scene_ids = [s.id for s in scenes]
    beats = (
        db.query(SceneBeat)
        .filter(SceneBeat.scene_id.in_(scene_ids))
        .order_by(SceneBeat.scene_id.asc(), SceneBeat.order_index.asc())
        .all()
    )
    shots = (
        db.query(Shot)
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
    obj = Scene(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_beats_by_scene(db: Session, scene_id: int) -> List[SceneBeat]:
    return (
        db.query(SceneBeat)
        .filter(SceneBeat.scene_id == scene_id)
        .order_by(SceneBeat.order_index.asc())
        .all()
    )


def create_scene_beat(db: Session, data: SceneBeatCreate) -> SceneBeat:
    obj = SceneBeat(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_shots_by_scene(db: Session, scene_id: int) -> List[Shot]:
    return (
        db.query(Shot)
        .filter(Shot.scene_id == scene_id)
        .order_by(Shot.shot_number.asc())
        .all()
    )


def create_shot(db: Session, data: ShotCreate) -> Shot:
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


def update_scene(db: Session, scene_id: int, payload: Dict[str, Any]) -> Optional[Scene]:
    obj = db.query(Scene).filter(Scene.id == scene_id).first()
    if not obj:
        return None
    for field, value in payload.items():
        if value is not None and hasattr(obj, field):
            setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_scene(db: Session, scene_id: int) -> bool:
    obj = db.query(Scene).filter(Scene.id == scene_id).first()
    if not obj:
        return False
    # Explicitly delete children to avoid ORM nulling FKs in SQLite
    db.query(Shot).filter(Shot.scene_id == scene_id).delete(synchronize_session=False)
    db.query(SceneBeat).filter(SceneBeat.scene_id == scene_id).delete(synchronize_session=False)
    db.delete(obj)
    db.commit()
    return True


def update_scene_beat(db: Session, beat_id: int, payload: Dict[str, Any]) -> Optional[SceneBeat]:
    obj = db.query(SceneBeat).filter(SceneBeat.id == beat_id).first()
    if not obj:
        return None
    for field, value in payload.items():
        if value is not None and hasattr(obj, field):
            setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_scene_beat(db: Session, beat_id: int) -> bool:
    obj = db.query(SceneBeat).filter(SceneBeat.id == beat_id).first()
    if not obj:
        return False
    # shots referencing this beat will set FK to NULL (ondelete=SET NULL)
    db.delete(obj)
    db.commit()
    return True


def update_shot(db: Session, shot_id: int, payload: Dict[str, Any]) -> Optional[Shot]:
    obj = db.query(Shot).filter(Shot.id == shot_id).first()
    if not obj:
        return None
    for field, value in payload.items():
        if value is not None and hasattr(obj, field):
            setattr(obj, field, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_shot(db: Session, shot_id: int) -> bool:
    obj = db.query(Shot).filter(Shot.id == shot_id).first()
    if not obj:
        return False
    db.delete(obj)
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
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        return 0
    source_scenes: List[dict[str, Any]] = list(script.scenes or [])  # type: ignore
    if not source_scenes:
        return 0

    existing = db.query(Scene).filter(Scene.script_id == script_id).all()
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
