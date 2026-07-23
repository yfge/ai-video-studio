from __future__ import annotations

from typing import List, Optional

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.script import Story, StoryCharacter
from app.models.user import User
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.repositories.narrative_promotion_repository import NarrativePromotionRepository
from app.repositories.story_crud_repository import StoryCrudRepository
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.schemas.script import StoryCreate, StoryResponse, StoryUpdate
from app.services.narrative_memory.baseline_service import BaselineService
from app.services.story.story_seed_service import StorySeedService
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .helpers import get_story_by_identifier

router = APIRouter()


@router.post("/", response_model=StoryResponse, status_code=201)
async def create_story(
    story: StoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """创建故事"""
    story_data = story.model_dump(exclude={"characters"})
    story_data["memory_mode"] = (
        "story_scoped_memory_v1"
        if story.workflow_mode == "novel_adaptation_v1"
        else "off"
    )
    story_data["canon_branch_id"] = "main"
    db_story = Story(user_id=current_user.id, **story_data)
    db.add(db_story)
    db.commit()
    db.refresh(db_story)

    if story.characters:
        for char_data in story.characters:
            virtual_ip = VirtualIPRepository(db).find_accessible_by_id(
                char_data.virtual_ip_id, user=current_user
            )
            if not virtual_ip:
                raise HTTPException(
                    status_code=404, detail=f"虚拟IP {char_data.virtual_ip_id} 不存在"
                )

            db_char = StoryCharacter(
                story_id=db_story.id,
                story_business_id=db_story.business_id,
                virtual_ip_business_id=virtual_ip.business_id,
                character_name=char_data.character_name or virtual_ip.name,
                **char_data.model_dump(exclude={"character_name"}),
            )
            db.add(db_char)

    db.commit()
    db.refresh(db_story)
    if db_story.memory_mode == "story_scoped_memory_v1":
        BaselineService(
            NarrativeMemoryRepository(db), NarrativePromotionRepository(db)
        ).freeze(db_story)

    return StoryResponse.from_orm(db_story)


@router.get("/", response_model=List[StoryResponse])
async def get_stories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    genre: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取故事列表"""
    stories = StoryCrudRepository(db).list_accessible(
        current_user, genre=genre, status=status, skip=skip, limit=limit
    )
    return [StoryResponse.from_orm(story) for story in stories]


@router.get("", include_in_schema=False)
async def get_stories_no_slash(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    genre: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    兼容无尾斜杠的 /api/v1/stories 请求，避免 307 重定向。

    内部直接复用 get_stories 的过滤与分页逻辑。
    """
    return await get_stories(
        skip=skip,
        limit=limit,
        genre=genre,
        status=status,
        current_user=current_user,
        db=db,
    )


@router.get("/{story_id}")
async def get_story(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取故事详情（支持业务ID）"""
    story = get_story_by_identifier(db, story_id, None, current_user)
    return StoryResponse.from_orm(story)


@router.get("/business/{story_business_id}")
async def get_story_by_business_id(
    story_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 获取故事详情"""
    story = get_story_by_identifier(db, None, story_business_id, current_user)
    return StoryResponse.from_orm(story)


@router.put("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: int,
    story_update: StoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新故事"""
    story = get_story_by_identifier(db, story_id, None, current_user)

    updates = story_update.model_dump(exclude_unset=True)
    seed = updates.pop("story_seed", None)
    seed_status = updates.pop("story_seed_status", None)
    if seed is not None:
        StorySeedService(NarrativeMemoryRepository(db)).apply_local_update(
            story, seed, requested_status=seed_status
        )
    for field, value in updates.items():
        setattr(story, field, value)

    db.commit()
    db.refresh(story)

    return StoryResponse.from_orm(story)


@router.put("/business/{story_business_id}", response_model=StoryResponse)
async def update_story_by_business_id(
    story_business_id: str,
    story_update: StoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 更新故事"""
    story = get_story_by_identifier(db, None, story_business_id, current_user)

    updates = story_update.model_dump(exclude_unset=True)
    seed = updates.pop("story_seed", None)
    seed_status = updates.pop("story_seed_status", None)
    if seed is not None:
        StorySeedService(NarrativeMemoryRepository(db)).apply_local_update(
            story, seed, requested_status=seed_status
        )
    for field, value in updates.items():
        setattr(story, field, value)

    db.commit()
    db.refresh(story)

    return StoryResponse.from_orm(story)


@router.delete("/{story_id}", status_code=204)
async def delete_story(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """删除故事"""
    story = get_story_by_identifier(db, story_id, None, current_user)
    story.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()

    return None


@router.delete("/business/{story_business_id}", status_code=204)
async def delete_story_by_business_id(
    story_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 删除故事"""
    story = get_story_by_identifier(db, None, story_business_id, current_user)
    story.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()

    return None
