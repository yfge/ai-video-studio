from app.api.v1.endpoints.stories.novel_task_queue import queue_story_seed_structure
from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.user import User
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.schemas.script import StoryResponse
from app.schemas.story_seed import StorySeedModel, StorySeedStructuredUpdateRequest
from app.services.story.story_novel_revision_service import StoryNovelRevisionService
from app.services.story.story_seed_service import StorySeedService
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()


@router.put("/business/{story_business_id}/story-seed", response_model=StoryResponse)
def save_structured_story_seed(
    story_business_id: str,
    request: StorySeedStructuredUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    story = StoryNovelRevisionService(db, current_user).story(story_business_id)
    if not story.story_seed:
        raise HTTPException(status_code=409, detail="StorySeed 尚未创建")
    seed = StorySeedModel.model_validate(
        {
            **dict(story.story_seed),
            "schema": "story_seed_v2",
            "outline_text": request.outline_text,
            "structured_outline": request.structured_outline.model_dump(),
        }
    )
    StorySeedService(NarrativeMemoryRepository(db)).apply_local_update(
        story,
        seed,
        requested_status=request.story_seed_status,
        expected_version=request.story_seed_version,
    )
    db.commit()
    db.refresh(story)
    return story


@router.post("/business/{story_business_id}/story-seed/structure-async")
def structure_story_seed_async(
    story_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    story = StoryNovelRevisionService(db, current_user).story(story_business_id)
    if not story.story_seed:
        raise HTTPException(status_code=409, detail="StorySeed 尚未创建")
    return queue_story_seed_structure(db, current_user, story)
