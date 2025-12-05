from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import story_structure_service as svc
from app.schemas.story_structure import (
    StoryTreatmentCreate,
    StoryTreatmentResponse,
    StoryStepOutlineCreate,
    StoryStepOutlineResponse,
    ScriptStructureResponse,
    SceneWithChildren,
    SceneResponse,
    SceneCreate,
    SceneUpdate,
    SceneBeatCreate,
    SceneBeatResponse,
    SceneBeatUpdate,
    ShotResponse,
    ShotCreate,
    ShotUpdate,
)


router = APIRouter()


@router.get("/scripts/{script_id}/scenes", response_model=List[SceneResponse])
async def list_scenes_for_script(
    script_id: int,
    db: Session = Depends(get_db),
):
    return [
        SceneResponse.model_validate(s)
        for s in svc.list_scenes_by_script(db, script_id)
    ]


@router.get("/scenes/{scene_id}/beats", response_model=List[SceneBeatResponse])
async def list_beats_for_scene(
    scene_id: int,
    db: Session = Depends(get_db),
):
    return [
        SceneBeatResponse.model_validate(b)
        for b in svc.list_beats_by_scene(db, scene_id)
    ]

@router.post("/scenes/{scene_id}/beats", response_model=SceneBeatResponse)
async def create_beat_for_scene(
    scene_id: int,
    body: SceneBeatCreate,
    db: Session = Depends(get_db),
):
    if body.scene_id != scene_id:
        raise HTTPException(status_code=400, detail="scene_id mismatch")
    obj = svc.create_scene_beat(db, body)
    return SceneBeatResponse.model_validate(obj)


@router.get("/scenes/{scene_id}/shots", response_model=List[ShotResponse])
async def list_shots_for_scene(
    scene_id: int,
    db: Session = Depends(get_db),
):
    return [
        ShotResponse.model_validate(sh) for sh in svc.list_shots_by_scene(db, scene_id)
    ]


@router.get("/scripts/{script_id}/structure", response_model=ScriptStructureResponse)
async def get_script_structure(
    script_id: int,
    db: Session = Depends(get_db),
):
    aggregated = svc.get_script_structure(db, script_id)
    if aggregated is None:
        raise HTTPException(status_code=404, detail="script not found")

    scenes_payload = []
    for item in aggregated:
        scene_dict = SceneResponse.model_validate(item["scene"]).model_dump()
        scene_dict["beats"] = [
            SceneBeatResponse.model_validate(b).model_dump()
            for b in item.get("beats", [])
        ]
        scene_dict["shots"] = [
            ShotResponse.model_validate(sh).model_dump() for sh in item.get("shots", [])
        ]
        scenes_payload.append(SceneWithChildren.model_validate(scene_dict))

    return ScriptStructureResponse(script_id=script_id, scenes=scenes_payload)


@router.post("/scripts/{script_id}/scenes", response_model=SceneResponse)
async def create_scene_for_script(
    script_id: int,
    body: SceneCreate,
    db: Session = Depends(get_db),
):
    if body.script_id != script_id:
        raise HTTPException(status_code=400, detail="script_id mismatch")
    obj = svc.create_scene(db, body)
    return SceneResponse.model_validate(obj)


@router.put("/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: int,
    body: SceneUpdate,
    db: Session = Depends(get_db),
):
    obj = svc.update_scene(db, scene_id, body.model_dump(exclude_none=True))
    if not obj:
        raise HTTPException(status_code=404, detail="scene not found")
    return SceneResponse.model_validate(obj)


@router.delete("/scenes/{scene_id}", status_code=204)
async def delete_scene(scene_id: int, db: Session = Depends(get_db)):
    ok = svc.delete_scene(db, scene_id)
    if not ok:
        raise HTTPException(status_code=404, detail="scene not found")
    return None


@router.post("/scenes/{scene_id}/shots", response_model=ShotResponse)
async def create_shot_for_scene(
    scene_id: int,
    body: ShotCreate,
    db: Session = Depends(get_db),
):
    if body.scene_id != scene_id:
        raise HTTPException(status_code=400, detail="scene_id mismatch")
    obj = svc.create_shot(db, body)
    return ShotResponse.model_validate(obj)


@router.put("/shots/{shot_id}", response_model=ShotResponse)
async def update_shot(
    shot_id: int,
    body: ShotUpdate,
    db: Session = Depends(get_db),
):
    obj = svc.update_shot(db, shot_id, body.model_dump(exclude_none=True))
    if not obj:
        raise HTTPException(status_code=404, detail="shot not found")
    return ShotResponse.model_validate(obj)


@router.delete("/shots/{shot_id}", status_code=204)
async def delete_shot(shot_id: int, db: Session = Depends(get_db)):
    ok = svc.delete_shot(db, shot_id)
    if not ok:
        raise HTTPException(status_code=404, detail="shot not found")
    return None


@router.put("/scene-beats/{beat_id}", response_model=SceneBeatResponse)
async def update_scene_beat(
    beat_id: int,
    body: SceneBeatUpdate,
    db: Session = Depends(get_db),
):
    obj = svc.update_scene_beat(db, beat_id, body.model_dump(exclude_none=True))
    if not obj:
        raise HTTPException(status_code=404, detail="beat not found")
    return SceneBeatResponse.model_validate(obj)


@router.delete("/scene-beats/{beat_id}", status_code=204)
async def delete_scene_beat(beat_id: int, db: Session = Depends(get_db)):
    ok = svc.delete_scene_beat(db, beat_id)
    if not ok:
        raise HTTPException(status_code=404, detail="beat not found")
    return None


@router.post("/scripts/{script_id}/seed-from-json")
async def seed_scenes_from_json(
    script_id: int,
    dry_run: bool = Query(False, description="Do not write inserts when true"),
    db: Session = Depends(get_db),
):
    count = svc.seed_scenes_from_script_json(db, script_id, dry_run=dry_run)
    return {
        "script_id": script_id,
        "prepared": count,
        "inserted": 0 if dry_run else count,
    }


@router.get(
    "/stories/{story_id}/treatments", response_model=List[StoryTreatmentResponse]
)
async def list_treatments(
    story_id: int,
    latest_only: bool = Query(False, description="仅返回最新一条修订"),
    db: Session = Depends(get_db),
):
    items = svc.list_treatments_by_story(db, story_id)
    if latest_only:
        return [StoryTreatmentResponse.model_validate(items[0])] if items else []
    return [StoryTreatmentResponse.model_validate(it) for it in items]


@router.post("/stories/{story_id}/treatments", response_model=StoryTreatmentResponse)
async def create_treatment(
    story_id: int,
    body: StoryTreatmentCreate,
    db: Session = Depends(get_db),
):
    if body.story_id != story_id:
        raise HTTPException(status_code=400, detail="story_id mismatch")
    obj = svc.create_treatment(db, body)
    return StoryTreatmentResponse.model_validate(obj)


@router.get(
    "/treatments/{treatment_id}/step-outlines",
    response_model=List[StoryStepOutlineResponse],
)
async def list_step_outlines_for_treatment(
    treatment_id: int,
    db: Session = Depends(get_db),
):
    outlines = svc.list_step_outlines(db, treatment_id)
    return [StoryStepOutlineResponse.model_validate(it) for it in outlines]


@router.post(
    "/treatments/{treatment_id}/step-outlines", response_model=StoryStepOutlineResponse
)
async def create_step_outline_for_treatment(
    treatment_id: int,
    body: StoryStepOutlineCreate,
    db: Session = Depends(get_db),
):
    if body.story_treatment_id != treatment_id:
        raise HTTPException(status_code=400, detail="story_treatment_id mismatch")
    treatment = svc.get_treatment(db, treatment_id)
    if not treatment:
        raise HTTPException(status_code=404, detail="treatment not found")
    if body.story_id != treatment.story_id:
        raise HTTPException(status_code=400, detail="story_id does not match treatment")
    obj = svc.create_step_outline(db, body)
    return StoryStepOutlineResponse.model_validate(obj)
