"""Script scene intent and subtext endpoints."""

import json

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.task import Task, TaskType
from app.models.user import User
from app.repositories.script_repository import ScriptRepository
from app.schemas.dramatic_state import (
    DramaticStateResponse,
    DramaticStateSuggestRequest,
    DramaticStateUpdate,
)
from app.services.narrative_memory.dramatic_state_service import DramaticStateService
from app.services.task_worker import dramatic_state_suggest_task
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get(
    "/business/{script_business_id}/scenes/{scene_business_id}/dramatic-state",
    response_model=DramaticStateResponse,
)
def get_dramatic_state(
    script_business_id: str,
    scene_business_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = DramaticStateService(ScriptRepository(db))
    return service.get(script_business_id, scene_business_id, user)


@router.put(
    "/business/{script_business_id}/scenes/{scene_business_id}/dramatic-state",
    response_model=DramaticStateResponse,
)
def update_dramatic_state(
    script_business_id: str,
    scene_business_id: str,
    payload: DramaticStateUpdate,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    service = DramaticStateService(ScriptRepository(db))
    return service.update(
        script_business_id,
        scene_business_id,
        expected_version=payload.expected_version,
        state=payload.dramatic_state,
        user=user,
    )


@router.post(
    "/business/{script_business_id}/scenes/{scene_business_id}/dramatic-state/suggest-async",
    status_code=202,
)
def suggest_dramatic_state_async(
    script_business_id: str,
    scene_business_id: str,
    payload: DramaticStateSuggestRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    DramaticStateService(ScriptRepository(db)).get(
        script_business_id, scene_business_id, user
    )
    values = payload.model_dump()
    task = Task(
        title="AI 建议场景潜台词",
        description="显式模型任务：建议只保存为草稿，不覆盖人工内容",
        task_type=TaskType.TEXT_GENERATION,
        target_business_id=script_business_id,
        parameters=json.dumps(
            {"operation": "dramatic_state_suggest", "scene": scene_business_id},
            ensure_ascii=False,
        ),
        user_id=user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    dramatic_state_suggest_task.delay(
        task.id, script_business_id, scene_business_id, values, user.id
    )
    return {"success": True, "data": {"task_id": task.id, "status": task.status}}
