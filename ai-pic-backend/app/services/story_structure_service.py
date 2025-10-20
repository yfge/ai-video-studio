from __future__ import annotations

from typing import List, Optional, Any

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
        .filter(StoryTreatment.story_id == story_id, StoryTreatment.is_deleted == False)  # noqa: E712
        .order_by(StoryTreatment.revision_number.desc())
        .all()
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


def seed_scenes_from_script_json(db: Session, script_id: int, *, dry_run: bool = False) -> int:
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
