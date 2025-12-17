from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks
from pydantic import ValidationError

from app.core.database import get_db
from app.models.user import User
from app.core.middleware import get_current_active_user
from app.models.script import Story, Episode
from app.models.virtual_ip import VirtualIP
from app.schemas.script import (
    EpisodeCreate,
    EpisodeUpdate,
    EpisodeResponse,
    EpisodeGenerationRequest,
)
from app.services.ai_service import ai_service
from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
import json
from app.utils.json_utils import extract_json_block
from app.models.task import Task, TaskStatus
from app.services.task_worker import episode_generate_task
from app.services.episode_agent import EpisodeGenerationCallbacks
from app.schemas.story_structure import StoryStepOutlineCreate
from app.services import story_structure_service
from app.schemas.generation import EpisodePlanItem, EpisodeStepOutlineModel

router = APIRouter()


def _not_deleted(query, model):
    """Filter out soft-deleted rows."""
    return query.filter(model.is_deleted.is_(False))


def _is_episode_payload_valid(episode_data: Dict[str, Any]) -> bool:
    """Ensure minimal episode payload validity before persisting."""
    summary = (episode_data.get("summary") or "").strip()
    conflicts = episode_data.get("conflicts")
    if not summary:
        return False
    if not conflicts or not isinstance(conflicts, list):
        return False
    return any(isinstance(c, dict) for c in conflicts)


def _parse_step_outlines(
    raw_step_outlines: Any, episode_count: int
) -> Optional[Dict[str, Any]]:
    parsed = (
        extract_json_block(raw_step_outlines)
        if isinstance(raw_step_outlines, str)
        else (raw_step_outlines if isinstance(raw_step_outlines, dict) else None)
    )
    if not parsed:
        return None
    try:
        validated = EpisodeStepOutlineModel.model_validate(parsed)
    except ValidationError:
        return None

    outlines = validated.model_dump()
    episodes = []
    for ep in sorted(
        outlines.get("episodes", []),
        key=lambda item: item.get("episode_number") or 0,
    ):
        logline = (ep.get("logline") or "").strip()
        if not logline:
            continue
        item = {
            "episode_number": ep.get("episode_number"),
            "title": ep.get("title"),
            "logline": logline,
        }
        if ep.get("beats"):
            item["beats"] = ep["beats"]
        episodes.append(item)
    if not episodes:
        return None
    outlines["episodes"] = episodes[:episode_count]
    return outlines


def _persist_story_outlines(
    story: Story,
    outlines: Dict[str, Any],
    *,
    prompt: Optional[str],
    agent_run: Dict[str, Any],
) -> None:
    existing_meta = (
        dict(story.extra_metadata) if isinstance(story.extra_metadata, dict) else {}
    )
    outline_payload = {
        "episodes": outlines.get("episodes", []),
        "prompt": prompt,
        "agent_run": agent_run or None,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    existing_meta["episode_step_outlines"] = outline_payload
    story.extra_metadata = existing_meta


def _build_outline_rows(
    *,
    outlines: Dict[str, Any],
    treatment,
    story: Story,
    episode_id_map: Dict[int, int],
    agent_run: Dict[str, Any],
) -> List[StoryStepOutlineCreate]:
    outline_rows: list[StoryStepOutlineCreate] = []
    for outline in outlines.get("episodes", []):
        ep_number = outline.get("episode_number")
        episode_id = episode_id_map.get(ep_number)
        if not episode_id:
            continue
        beats = outline.get("beats") or []
        for beat_idx, beat in enumerate(beats, start=1):
            if not isinstance(beat, dict):
                continue
            outline_rows.append(
                StoryStepOutlineCreate(
                    story_id=story.id,
                    story_treatment_id=treatment.id,
                    episode_id=episode_id,
                    sequence_number=beat.get("sequence_number") or beat_idx,
                    act_label=beat.get("act_label"),
                    beat_title=beat.get("beat_title") or f"Beat {beat_idx}",
                    beat_summary=beat.get("beat_summary")
                    or beat.get("description")
                    or f"情节点 {beat_idx}",
                    dramatic_question=beat.get("dramatic_question"),
                    characters_involved=beat.get("characters_involved"),
                    location_hint=beat.get("location_hint"),
                    duration_estimate_minutes=beat.get("duration_estimate_minutes"),
                    status="draft",
                    metadata={
                        "source": agent_run.get("generation_method"),
                        "agent_reasoning": agent_run.get("reasoning"),
                    },
                )
            )
    return outline_rows


def _build_stub_episodes_from_outlines(
    outlines: Optional[Dict[str, Any]], episode_count: int
) -> list[Dict[str, Any]]:
    """当模型返回无法解析的内容时，基于大纲兜底生成可落库的剧集草稿。"""
    if not outlines:
        return []
    episodes: list[Dict[str, Any]] = []
    for idx, outline in enumerate(
        outlines.get("episodes", [])[:episode_count], start=1
    ):
        logline = (outline.get("logline") or "").strip()
        if not logline:
            continue
        ep_number = outline.get("episode_number") or idx
        title = outline.get("title") or f"第{ep_number}集"
        episodes.append(
            {
                "episode_number": ep_number,
                "title": title,
                "summary": logline,
                "plot_points": [],
                "character_arcs": None,
                "conflicts": [
                    {
                        "description": logline,
                        "intensity": "medium",
                    }
                ],
                "scene_count": None,
            }
        )
    return episodes


def _update_task_progress(db: Session, task: Optional[Task], description: str) -> None:
    """Utility to keep task progress detail in sync."""
    if not task:
        return
    task.description = description
    db.commit()


@router.post("/", response_model=EpisodeResponse)
async def create_episode(
    episode: EpisodeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """创建剧集"""
    # 检查故事是否存在
    story_query = _not_deleted(db.query(Story), Story).filter(Story.id == episode.story_id)
    if not current_user.is_admin and not current_user.is_superuser:
        story_query = story_query.filter(Story.user_id == current_user.id)
    story = story_query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    # 检查集数是否重复
    existing_episode = (
        _not_deleted(db.query(Episode), Episode)
        .filter(
            Episode.story_id == episode.story_id,
            Episode.episode_number == episode.episode_number,
        )
        .first()
    )
    if existing_episode:
        raise HTTPException(status_code=400, detail="该集数已存在")

    db_episode = Episode(**episode.dict())
    db.add(db_episode)
    db.commit()
    db.refresh(db_episode)

    return EpisodeResponse.from_orm(db_episode)


@router.post("/generate", response_model=List[EpisodeResponse])
async def generate_episodes(
    request: EpisodeGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """使用AI生成剧集"""
    # 获取故事信息
    story_query = _not_deleted(db.query(Story), Story).filter(Story.id == request.story_id)
    if not current_user.is_admin and not current_user.is_superuser:
        story_query = story_query.filter(Story.user_id == current_user.id)
    story = story_query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    # 获取重点角色信息
    focus_characters = []
    if request.focus_characters:
        for char_id in request.focus_characters:
            vip_query = db.query(VirtualIP).filter(VirtualIP.id == char_id)
            if not current_user.is_admin and not current_user.is_superuser:
                vip_query = vip_query.filter(VirtualIP.user_id == current_user.id)
            virtual_ip = vip_query.first()
            if virtual_ip:
                focus_characters.append(
                    {
                        "id": virtual_ip.id,
                        "name": virtual_ip.name,
                        "description": virtual_ip.description,
                    }
                )

    # 构建故事数据
    story_data = {
        "title": story.title,
        "genre": story.genre,
        "theme": story.theme,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
    }

    # 调用AI服务生成剧集
    # 解析模型与提供商
    prefer_provider = None
    model_id = request.model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    result = await ai_service.generate_episodes(
        story=story_data,
        episode_count=request.episode_count,
        episode_duration=request.episode_duration,
        focus_characters=focus_characters,
        plot_complexity=request.plot_complexity,
        pacing=request.pacing,
        additional_requirements=request.additional_requirements,
        style_preferences=request.style_preferences,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=request.temperature or 0.7,
    )

    if not result:
        raise HTTPException(status_code=500, detail="AI剧集生成失败")

    # 结构化 agent 运行信息，便于落库与排查
    agent_run = {}
    if isinstance(result, dict):
        agent_run = {
            "generation_method": result.get("generation_method"),
            "template_used": result.get("template_used"),
            "provider_used": result.get("provider_used"),
            "model_used": result.get("model_used"),
            "usage": result.get("usage"),
            "reasoning": result.get("reasoning"),
        }

    # 可选的 step outline（用于写入 story_step_outlines / story.extra_metadata）
    raw_step_outlines = None
    if isinstance(result, dict):
        raw_step_outlines = result.get("step_outlines") or result.get(
            "step_outlines_raw"
        )
    step_outlines = (
        _parse_step_outlines(raw_step_outlines, request.episode_count)
        if raw_step_outlines
        else None
    )
    if step_outlines:
        _persist_story_outlines(
            story,
            step_outlines,
            prompt=(
                result.get("step_outline_prompt") if isinstance(result, dict) else None
            ),
            agent_run=agent_run,
        )

    # 解析AI生成的内容；若失败则使用大纲兜底
    normalized = result.get("normalized") if isinstance(result, dict) else None
    ai_content = normalized or extract_json_block(
        result.get("content") if isinstance(result, dict) else None
    )
    episodes_data = ai_content.get("episodes", []) if ai_content else []
    if not episodes_data and step_outlines:
        episodes_data = _build_stub_episodes_from_outlines(
            step_outlines, request.episode_count
        )
        agent_run = {**agent_run, "fallback_from_outline": True}
    if not episodes_data:
        raise HTTPException(status_code=500, detail="AI生成内容格式错误")

    # 创建剧集记录
    created_episodes = []
    for i, episode_data in enumerate(episodes_data[: request.episode_count]):
        # 检查集数是否重复
        episode_number = episode_data.get("episode_number", i + 1)
        existing_episode = (
            db.query(Episode)
            .filter(
                Episode.story_id == request.story_id,
                Episode.episode_number == episode_number,
            )
            .first()
        )

        if existing_episode:
            continue  # 跳过已存在的集数

        try:
            EpisodePlanItem.model_validate(episode_data)
        except ValidationError:
            ai_service.logger.warning(
                "Episode schema validation failed; skip persisting",
                extra={"story_id": story.id, "episode_number": episode_number},
            )
            continue

        if not _is_episode_payload_valid(episode_data):
            ai_service.logger.warning(
                "Episode validation failed; skip persisting",
                extra={"story_id": story.id, "episode_number": episode_number},
            )
            continue

        # 提取额外元数据
        known_keys = {
            "episode_number",
            "title",
            "summary",
            "plot_points",
            "character_arcs",
            "conflicts",
            "scene_count",
        }
        extra_meta = {k: v for k, v in episode_data.items() if k not in known_keys}
        extra_metadata = extra_meta or None
        if agent_run:
            extra_metadata = {
                **(extra_metadata or {}),
                "agent_run": agent_run,
            }

        db_episode = Episode(
            story_id=request.story_id,
            episode_number=episode_number,
            title=episode_data.get("title", f"第{episode_number}集"),
            summary=episode_data.get("summary"),
            plot_points=episode_data.get("plot_points"),
            character_arcs=episode_data.get("character_arcs"),
            conflicts=episode_data.get("conflicts"),
            duration_minutes=request.episode_duration,
            scene_count=episode_data.get("scene_count"),
            generation_prompt=(
                result.get("prompt") if isinstance(result, dict) else None
            )
            or (
                result.get("step_outline_prompt") if isinstance(result, dict) else None
            ),
            ai_model=(
                result.get("generation_method") if isinstance(result, dict) else None
            )
            or (result.get("model_used") if isinstance(result, dict) else None),
            generation_params={
                "focus_characters": request.focus_characters,
                "plot_complexity": request.plot_complexity,
                "pacing": request.pacing,
                "additional_requirements": request.additional_requirements,
                "style_preferences": request.style_preferences,
            },
            extra_metadata=extra_metadata,
            status="draft",
        )

        db.add(db_episode)
        created_episodes.append(db_episode)

    db.commit()

    # 将 Step Outline beats 落库到 story_step_outlines
    if step_outlines and created_episodes:
        try:
            treatment = story_structure_service.ensure_auto_treatment(
                db,
                story,
                prompt_snapshot={
                    "outline_prompt": (
                        result.get("step_outline_prompt")
                        if isinstance(result, dict)
                        else None
                    ),
                    "step_outlines_raw": (
                        result.get("step_outlines_raw")
                        if isinstance(result, dict)
                        else None
                    ),
                    "agent_generation_method": agent_run.get("generation_method"),
                },
            )
            episode_id_map = {ep.episode_number: ep.id for ep in created_episodes}
            outline_rows: list[StoryStepOutlineCreate] = []
            for outline in step_outlines.get("episodes", []):
                ep_number = outline.get("episode_number")
                episode_id = episode_id_map.get(ep_number)
                if not episode_id:
                    continue
                beats = outline.get("beats") or []
                # beats 可能为空；仅在存在时落库
                for beat_idx, beat in enumerate(beats, start=1):
                    if not isinstance(beat, dict):
                        continue
                    outline_rows.append(
                        StoryStepOutlineCreate(
                            story_id=story.id,
                            story_treatment_id=treatment.id,
                            episode_id=episode_id,
                            sequence_number=beat.get("sequence_number") or beat_idx,
                            act_label=beat.get("act_label"),
                            beat_title=beat.get("beat_title") or f"Beat {beat_idx}",
                            beat_summary=beat.get("beat_summary")
                            or beat.get("description")
                            or f"情节点 {beat_idx}",
                            dramatic_question=beat.get("dramatic_question"),
                            characters_involved=beat.get("characters_involved"),
                            location_hint=beat.get("location_hint"),
                            duration_estimate_minutes=beat.get(
                                "duration_estimate_minutes"
                            ),
                            status="draft",
                            metadata={
                                "source": agent_run.get("generation_method"),
                                "agent_reasoning": agent_run.get("reasoning"),
                            },
                        )
                    )
            if outline_rows:
                story_structure_service.bulk_create_step_outlines(db, outline_rows)
        except Exception as exc:
            # 不阻断主流程，记录日志方便排查
            ai_service.logger.warning(
                "Failed to persist step outlines",
                extra={"error": str(exc), "story_id": story.id},
            )

    # 刷新所有创建的剧集
    for episode in created_episodes:
        db.refresh(episode)

    return [EpisodeResponse.from_orm(episode) for episode in created_episodes]


@router.post("/prompt/preview")
async def preview_episode_prompt(
    request: EpisodeGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """返回剧集生成的最终提示词（不调用模型）"""
    story_query = db.query(Story).filter(Story.id == request.story_id)
    if not current_user.is_admin and not current_user.is_superuser:
        story_query = story_query.filter(Story.user_id == current_user.id)
    story = story_query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    story_data = {
        "title": story.title,
        "genre": story.genre,
        "theme": story.theme,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
    }

    focus_characters = []
    if request.focus_characters:
        for cid in request.focus_characters:
            vip = db.query(VirtualIP).filter(VirtualIP.id == cid).first()
            if vip:
                focus_characters.append(
                    {"id": vip.id, "name": vip.name, "description": vip.description}
                )

    variables = {
        "story": story_data,
        "episode_count": request.episode_count,
        "episode_duration": request.episode_duration,
        "focus_characters": focus_characters,
        "plot_complexity": request.plot_complexity,
        "pacing": request.pacing,
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences or [],
    }
    prompt = PromptManager().render_prompt(
        PromptTemplate.EPISODE_GENERATION.value, variables
    )
    return {"success": True, "data": {"prompt": prompt}}


@router.get("/", response_model=List[EpisodeResponse])
async def get_episodes(
    story_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取剧集列表"""
    query = db.query(Episode).join(Story, Episode.story_id == Story.id)

    # 普通用户只能查看自己的故事下的剧集
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)

    if story_id:
        query = query.filter(Episode.story_id == story_id)

    if status:
        query = query.filter(Episode.status == status)

    episodes = (
        query.order_by(Episode.story_id, Episode.episode_number)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [EpisodeResponse.from_orm(episode) for episode in episodes]


@router.get("", response_model=List[EpisodeResponse], include_in_schema=False)
async def get_episodes_no_slash(
    story_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    兼容无尾斜杠的 /api/v1/episodes 请求，避免 307 重定向。

    内部直接复用 get_episodes 的过滤与分页逻辑。
    """
    return await get_episodes(
        story_id=story_id,
        skip=skip,
        limit=limit,
        status=status,
        current_user=current_user,
        db=db,
    )


@router.get("/{episode_id}", response_model=EpisodeResponse)
async def get_episode(
    episode_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取剧集详情"""
    episode = (
        db.query(Episode)
        .join(Story, Episode.story_id == Story.id)
        .filter(Episode.id == episode_id)
        .filter(
            True
            if current_user.is_admin or current_user.is_superuser
            else Story.user_id == current_user.id
        )
        .first()
    )
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    return EpisodeResponse.from_orm(episode)


@router.put("/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: int,
    episode_update: EpisodeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新剧集"""
    episode = (
        db.query(Episode)
        .join(Story, Episode.story_id == Story.id)
        .filter(Episode.id == episode_id)
        .filter(
            True
            if current_user.is_admin or current_user.is_superuser
            else Story.user_id == current_user.id
        )
        .first()
    )
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    # 如果更新集数，检查是否重复
    if (
        episode_update.episode_number
        and episode_update.episode_number != episode.episode_number
    ):
        existing_episode = (
            db.query(Episode)
            .filter(
                Episode.story_id == episode.story_id,
                Episode.episode_number == episode_update.episode_number,
                Episode.id != episode_id,
            )
            .first()
        )
        if existing_episode:
            raise HTTPException(status_code=400, detail="该集数已存在")

    # 更新剧集信息
    for field, value in episode_update.dict(exclude_unset=True).items():
        setattr(episode, field, value)

    db.commit()
    db.refresh(episode)

    return EpisodeResponse.from_orm(episode)


@router.delete("/{episode_id}")
async def delete_episode(
    episode_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """删除剧集"""
    episode = (
        db.query(Episode)
        .join(Story, Episode.story_id == Story.id)
        .filter(Episode.id == episode_id)
        .filter(
            True
            if current_user.is_admin or current_user.is_superuser
            else Story.user_id == current_user.id
        )
        .first()
    )
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    db.delete(episode)
    db.commit()

    return {"message": "剧集删除成功"}


@router.get("/story/{story_id}")
async def get_story_episodes(
    story_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取故事的所有剧集"""
    # 检查故事是否存在
    story_query = db.query(Story).filter(Story.id == story_id)
    if not current_user.is_admin and not current_user.is_superuser:
        story_query = story_query.filter(Story.user_id == current_user.id)
    story = story_query.first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    episodes = (
        _not_deleted(db.query(Episode), Episode)
        .filter(Episode.story_id == story_id)
        .order_by(Episode.episode_number)
        .all()
    )
    return {
        "success": True,
        "data": (
            [EpisodeResponse.from_orm(episode) for episode in episodes]
            if episodes
            else []
        ),
    }


@router.post("/{episode_id}/regenerate", response_model=EpisodeResponse)
async def regenerate_episode(
    episode_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """重新生成剧集内容"""
    episode_query = (
        _not_deleted(db.query(Episode), Episode)
        .join(Story, Episode.story_id == Story.id)
        .filter(Episode.id == episode_id)
    )
    if not (current_user.is_admin or current_user.is_superuser):
        episode_query = episode_query.filter(Story.user_id == current_user.id)
    episode = episode_query.first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    story = (
        _not_deleted(db.query(Story), Story).filter(Story.id == episode.story_id).first()
    )
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    # 构建故事数据
    story_data = {
        "title": story.title,
        "genre": story.genre,
        "theme": story.theme,
        "synopsis": story.synopsis,
        "main_conflict": story.main_conflict,
        "resolution": story.resolution,
        "main_characters": story.main_characters,
        "character_relationships": story.character_relationships,
        "world_building": story.world_building,
        "setting_time": story.setting_time,
        "setting_location": story.setting_location,
    }

    # 使用原有的生成参数
    original_params = episode.generation_params or {}

    # 调用AI服务重新生成单集内容
    result = await ai_service.generate_episodes(
        story=story_data,
        episode_count=1,
        episode_duration=episode.duration_minutes,
        focus_characters=None,
        plot_complexity=original_params.get("plot_complexity", "medium"),
        pacing=original_params.get("pacing", "medium"),
        additional_requirements=f"重新生成第{episode.episode_number}集的内容",
        style_preferences=original_params.get("style_preferences"),
    )

    if not result:
        raise HTTPException(status_code=500, detail="AI剧集重新生成失败")

    agent_run = {}
    if isinstance(result, dict):
        agent_run = {
            "generation_method": result.get("generation_method"),
            "template_used": result.get("template_used"),
            "provider_used": result.get("provider_used"),
            "model_used": result.get("model_used"),
            "usage": result.get("usage"),
            "reasoning": result.get("reasoning"),
        }

    # 解析AI生成的内容
    ai_content = (
        result.get("normalized") if isinstance(result, dict) else None
    ) or extract_json_block(result.get("content") if isinstance(result, dict) else None)
    if ai_content:
        episodes_data = ai_content.get("episodes", [])
        if episodes_data:
            episode_data = episodes_data[0]
            scenes, scene_count = _ensure_scenes(episode_data)

            new_episode = Episode(
                story_id=episode.story_id,
                story_business_id=getattr(story, "business_id", None),
                episode_number=episode.episode_number,
                title=episode_data.get("title") or episode.title,
                summary=episode_data.get("summary"),
                plot_points=episode_data.get("plot_points"),
                character_arcs=episode_data.get("character_arcs"),
                conflicts=episode_data.get("conflicts"),
                scene_count=scene_count,
                duration_minutes=episode.duration_minutes,
                generation_params=episode.generation_params,
                status=episode.status,
                tags=episode.tags,
                extra_metadata=None,
                generation_prompt=result.get("prompt"),
                ai_model=result.get("generation_method"),
            )

            known_keys = {
                "episode_number",
                "title",
                "summary",
                "plot_points",
                "character_arcs",
                "conflicts",
                "scene_count",
            }
            extra_meta = {
                k: v for k, v in episode_data.items() if k not in known_keys
            } or {}
            if scenes and "scenes" not in extra_meta:
                extra_meta["scenes"] = scenes
            if agent_run:
                extra_meta = {
                    **(extra_meta or {}),
                    "agent_run": agent_run,
                }
            new_episode.extra_metadata = extra_meta or None

            db.add(new_episode)
            db.commit()
            db.refresh(new_episode)

            # Soft delete old episode
            episode.soft_delete(user_id=current_user.id, reason="regenerate superseded")
            db.commit()

            return EpisodeResponse.from_orm(new_episode)

    raise HTTPException(status_code=500, detail="AI生成内容格式错误")


def _process_episode_generation_task(task_id: int, request_dict: dict, user_id: int):
    from app.core.database import SessionLocal

    db = SessionLocal()
    created_ids: list[int] = []
    try:
        task: Task | None = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            _update_task_progress(db, task, "剧集生成：准备调用模型")

        story: Story | None = (
            db.query(Story)
            .filter(
                Story.id == request_dict.get("story_id"),
                Story.user_id == user_id,
            )
            .first()
        )
        if not story:
            raise RuntimeError("故事不存在")

        step_outlines: dict[str, Any] | None = None
        outline_agent_run: dict[str, Any] = {}
        treatment = None
        used_callbacks = False

        story_data = {
            "title": story.title,
            "genre": story.genre,
            "theme": story.theme,
            "synopsis": story.synopsis,
            "main_conflict": story.main_conflict,
            "resolution": story.resolution,
            "main_characters": story.main_characters,
            "character_relationships": story.character_relationships,
            "world_building": story.world_building,
            "setting_time": story.setting_time,
            "setting_location": story.setting_location,
        }

        focus_characters = []
        for cid in request_dict.get("focus_characters") or []:
            vip = (
                db.query(VirtualIP)
                .filter(VirtualIP.id == cid, VirtualIP.user_id == user_id)
                .first()
            )
            if vip:
                focus_characters.append(
                    {"id": vip.id, "name": vip.name, "description": vip.description}
                )

        import anyio

        def _progress(message: str) -> None:
            if task:
                _update_task_progress(db, task, message)

        def _coerce_episode_payload(
            episode_data: dict[str, Any], outline: dict[str, Any] | None
        ) -> dict[str, Any]:
            coerced = dict(episode_data or {})
            ep_num = coerced.get("episode_number") or (
                outline.get("episode_number") if isinstance(outline, dict) else None
            )
            if ep_num:
                coerced["episode_number"] = ep_num
            if not (coerced.get("title") or "").strip():
                coerced["title"] = f"第{coerced.get('episode_number') or 1}集"
            summary = (coerced.get("summary") or "").strip()
            if not summary:
                logline = (outline.get("logline") or "").strip() if outline else ""
                coerced["summary"] = logline or "本集推进主线冲突，并留下钩子。"
            conflicts = coerced.get("conflicts")
            if (
                not conflicts
                or not isinstance(conflicts, list)
                or not any(isinstance(c, dict) for c in conflicts)
            ):
                coerced["conflicts"] = [
                    {"description": coerced["summary"], "intensity": "medium"}
                ]
            return coerced

        def _on_outline(outlines: dict[str, Any], meta: dict[str, Any]) -> None:
            nonlocal step_outlines, outline_agent_run, treatment, used_callbacks
            used_callbacks = True
            step_outlines = outlines
            outline_agent_run = {
                "generation_method": meta.get("generation_method"),
                "template_used": PromptTemplate.EPISODE_STEP_OUTLINE.value,
                "provider_used": meta.get("provider"),
                "model_used": meta.get("model"),
                "usage": meta.get("usage"),
                "reasoning": meta.get("reasoning"),
            }
            _persist_story_outlines(
                story,
                outlines,
                prompt=meta.get("prompt"),
                agent_run=outline_agent_run,
            )
            _progress("剧集生成：大纲校验通过，写入故事信息")

            # 若大纲包含 beats，则提前创建 treatment，后续按集落库 beats
            try:
                has_beats = any(
                    isinstance(item, dict) and item.get("beats")
                    for item in (outlines.get("episodes") or [])
                )
                if has_beats:
                    treatment = story_structure_service.ensure_auto_treatment(
                        db,
                        story,
                        prompt_snapshot={
                            "outline_prompt": meta.get("prompt"),
                            "step_outlines_raw": meta.get("raw"),
                            "agent_generation_method": meta.get("generation_method"),
                        },
                    )
            except (
                Exception
            ) as exc:  # pragma: no cover - defensive logging for async path
                ai_service.logger.warning(
                    "Failed to create treatment for step outlines",
                    extra={"error": str(exc), "story_id": story.id},
                )

        def _on_episode(episode_data: dict[str, Any], meta: dict[str, Any]) -> None:
            nonlocal created_ids, used_callbacks
            used_callbacks = True

            outline = meta.get("outline") if isinstance(meta, dict) else None
            outline_dict = outline if isinstance(outline, dict) else None
            coerced = _coerce_episode_payload(episode_data, outline_dict)
            episode_number = coerced.get("episode_number")
            if not episode_number:
                return

            exists = (
                db.query(Episode)
                .filter(
                    Episode.story_id == story.id,
                    Episode.episode_number == episode_number,
                )
                .first()
            )
            if exists:
                _progress(f"生成第{episode_number}集：已存在，跳过")
                return

            try:
                EpisodePlanItem.model_validate(coerced)
            except ValidationError:
                # schema 不通过也尽量兜底落库，避免任务跑完却没有可见产物
                _progress(f"生成第{episode_number}集：schema异常，兜底写入")

            scenes, scene_count = _ensure_scenes(coerced)
            known_keys = {
                "episode_number",
                "title",
                "summary",
                "plot_points",
                "character_arcs",
                "conflicts",
                "scene_count",
            }
            extra_meta = {k: v for k, v in coerced.items() if k not in known_keys} or {}
            if scenes and "scenes" not in extra_meta:
                extra_meta["scenes"] = scenes

            episode_agent_run = {
                "generation_method": meta.get("generation_method")
                or "langgraph_episode_step_outline",
                "provider_used": meta.get("provider"),
                "model_used": meta.get("model"),
                "usage": meta.get("usage"),
                "fallback_from_outline": meta.get("fallback_from_outline"),
            }
            ep = Episode(
                story_id=story.id,
                episode_number=episode_number,
                title=coerced.get("title", f"第{episode_number}集"),
                summary=coerced.get("summary"),
                plot_points=coerced.get("plot_points"),
                character_arcs=coerced.get("character_arcs"),
                conflicts=coerced.get("conflicts"),
                duration_minutes=request_dict.get("episode_duration"),
                scene_count=scene_count,
                generation_prompt=meta.get("prompt"),
                ai_model=meta.get("model")
                or meta.get("provider")
                or episode_agent_run.get("generation_method"),
                generation_params={
                    k: request_dict.get(k)
                    for k in [
                        "focus_characters",
                        "plot_complexity",
                        "pacing",
                        "additional_requirements",
                        "style_preferences",
                        "model",
                        "temperature",
                    ]
                },
                extra_metadata={
                    **(extra_meta or {}),
                    "agent_run": episode_agent_run,
                },
                status="draft",
            )
            db.add(ep)
            db.commit()
            db.refresh(ep)
            created_ids.append(ep.id)
            _progress(f"生成第{episode_number}集：已落库")

            if treatment and step_outlines:
                try:
                    outline_rows = _build_outline_rows(
                        outlines=step_outlines,
                        treatment=treatment,
                        story=story,
                        episode_id_map={episode_number: ep.id},
                        agent_run=outline_agent_run or episode_agent_run,
                    )
                    if outline_rows:
                        story_structure_service.bulk_create_step_outlines(
                            db, outline_rows
                        )
                except (
                    Exception
                ) as exc:  # pragma: no cover - defensive logging for async path
                    ai_service.logger.warning(
                        "Failed to persist step outlines in async task",
                        extra={"error": str(exc), "story_id": story.id},
                    )

        async def _run():
            prefer_provider = None
            model_id = request_dict.get("model")
            if model_id and ":" in model_id:
                prefer_provider, model_id = model_id.split(":", 1)
            return await ai_service.generate_episodes(
                story=story_data,
                episode_count=request_dict.get("episode_count"),
                episode_duration=request_dict.get("episode_duration"),
                focus_characters=focus_characters,
                plot_complexity=request_dict.get("plot_complexity", "medium"),
                pacing=request_dict.get("pacing", "medium"),
                additional_requirements=request_dict.get("additional_requirements"),
                style_preferences=request_dict.get("style_preferences"),
                model=model_id,
                prefer_provider=prefer_provider,
                temperature=request_dict.get("temperature", 0.7),
                callbacks=EpisodeGenerationCallbacks(
                    on_progress=_progress,
                    on_outline=_on_outline,
                    on_episode=_on_episode,
                ),
            )

        result = anyio.run(_run)
        if not result:
            raise RuntimeError("AI剧集生成失败")

        if not used_callbacks:
            _progress("剧集生成：模型返回结果解析中")

            content = (
                result.get("normalized") if isinstance(result, dict) else None
            ) or extract_json_block(
                result.get("content") if isinstance(result, dict) else None
            )
            episodes_data = content.get("episodes", []) if content else []

            agent_run: dict[str, Any] = {}
            if isinstance(result, dict):
                agent_run = {
                    "generation_method": result.get("generation_method"),
                    "template_used": result.get("template_used"),
                    "provider_used": result.get("provider_used"),
                    "model_used": result.get("model_used"),
                    "usage": result.get("usage"),
                    "reasoning": result.get("reasoning"),
                }

            raw_step_outlines = None
            if isinstance(result, dict):
                raw_step_outlines = result.get("step_outlines") or result.get(
                    "step_outlines_raw"
                )
            episode_count = request_dict.get("episode_count") or len(episodes_data) or 1
            parsed_outlines = (
                _parse_step_outlines(raw_step_outlines, episode_count)
                if raw_step_outlines
                else None
            )
            if parsed_outlines:
                _persist_story_outlines(
                    story,
                    parsed_outlines,
                    prompt=(
                        result.get("step_outline_prompt")
                        if isinstance(result, dict)
                        else None
                    ),
                    agent_run=agent_run,
                )
                _progress("剧集生成：大纲校验通过，写入故事信息")
                db.refresh(story)

            if not episodes_data and parsed_outlines:
                episodes_data = _build_stub_episodes_from_outlines(
                    parsed_outlines, episode_count
                )
                agent_run = {**agent_run, "fallback_from_outline": True}
                _progress("模型输出无效，使用大纲兜底生成")
            if not episodes_data:
                raise RuntimeError("AI生成内容格式错误")

            created_episodes: list[Episode] = []
            for i, ep_data in enumerate(episodes_data[:episode_count]):
                episode_number = ep_data.get("episode_number", i + 1)
                _progress(f"生成第{episode_number}集：校验中")
                exists = (
                    db.query(Episode)
                    .filter(
                        Episode.story_id == story.id,
                        Episode.episode_number == episode_number,
                    )
                    .first()
                )
                if exists:
                    continue

                try:
                    EpisodePlanItem.model_validate(ep_data)
                except ValidationError:
                    _progress(f"生成第{episode_number}集：schema校验失败")
                    continue
                if not _is_episode_payload_valid(ep_data):
                    _progress(f"生成第{episode_number}集：内容校验失败")
                    continue

                scenes, scene_count = _ensure_scenes(ep_data)
                known_keys = {
                    "episode_number",
                    "title",
                    "summary",
                    "plot_points",
                    "character_arcs",
                    "conflicts",
                    "scene_count",
                }
                extra_meta = {
                    k: v for k, v in ep_data.items() if k not in known_keys
                } or {}
                if scenes and "scenes" not in extra_meta:
                    extra_meta["scenes"] = scenes

                ep = Episode(
                    story_id=story.id,
                    episode_number=episode_number,
                    title=ep_data.get("title", f"第{episode_number}集"),
                    summary=ep_data.get("summary"),
                    plot_points=ep_data.get("plot_points"),
                    character_arcs=ep_data.get("character_arcs"),
                    conflicts=ep_data.get("conflicts"),
                    duration_minutes=request_dict.get("episode_duration"),
                    scene_count=scene_count,
                    generation_prompt=(
                        result.get("prompt") if isinstance(result, dict) else None
                    ),
                    ai_model=(
                        result.get("generation_method")
                        if isinstance(result, dict)
                        else None
                    ),
                    generation_params={
                        k: request_dict.get(k)
                        for k in [
                            "focus_characters",
                            "plot_complexity",
                            "pacing",
                            "additional_requirements",
                            "style_preferences",
                            "model",
                            "temperature",
                        ]
                    },
                    extra_metadata={
                        **(extra_meta or {}),
                        "agent_run": agent_run,
                    },
                    status="draft",
                )
                db.add(ep)
                db.commit()
                db.refresh(ep)
                created_episodes.append(ep)
                created_ids.append(ep.id)
                _progress(f"生成第{episode_number}集：已落库")

            if parsed_outlines and created_episodes:
                try:
                    treatment = story_structure_service.ensure_auto_treatment(
                        db,
                        story,
                        prompt_snapshot={
                            "outline_prompt": (
                                result.get("step_outline_prompt")
                                if isinstance(result, dict)
                                else None
                            ),
                            "step_outlines_raw": (
                                result.get("step_outlines_raw")
                                if isinstance(result, dict)
                                else None
                            ),
                            "agent_generation_method": agent_run.get(
                                "generation_method"
                            ),
                        },
                    )
                    episode_id_map = {
                        ep.episode_number: ep.id for ep in created_episodes
                    }
                    outline_rows = _build_outline_rows(
                        outlines=parsed_outlines,
                        treatment=treatment,
                        story=story,
                        episode_id_map=episode_id_map,
                        agent_run=agent_run,
                    )
                    if outline_rows:
                        story_structure_service.bulk_create_step_outlines(
                            db, outline_rows
                        )
                except (
                    Exception
                ) as exc:  # pragma: no cover - defensive logging for async path
                    ai_service.logger.warning(
                        "Failed to persist step outlines in async task",
                        extra={"error": str(exc), "story_id": story.id},
                    )

        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"episodes:{','.join(map(str, created_ids))}"
            final_desc = (
                f"剧集生成完成：共写入 {len(created_ids)} 集"
                if created_ids
                else "剧集生成完成但无新剧集写入"
            )
            _update_task_progress(db, task, final_desc)
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            _update_task_progress(db, task, f"剧集生成失败：{e}")
    finally:
        db.close()


@router.post("/generate-async")
async def generate_episodes_async(
    request: EpisodeGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    t = Task(
        title=f"生成剧集 - 故事{request.story_id}",
        description="异步剧集生成",
        task_type="image_generation",
        prompt=f"Episode plan for story {request.story_id}",
        parameters=json.dumps(request.dict(), ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    # 交给 Celery worker 处理
    episode_generate_task.delay(t.id, request.dict(), current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


def _ensure_scenes(ep_data: dict) -> tuple[list[dict], int | None]:
    """确保剧集数据包含可用的 scenes。

    备注：部分模型/Schema 可能会返回 scenes=[{}, {}, ...]，此时需要过滤空对象并自动补全占位场景，
    避免前端出现“场景列表存在但内容为空”的不稳定情况。
    """

    def _as_nonempty_str(value: object | None) -> str | None:
        if not isinstance(value, str):
            return None
        text = value.strip()
        return text or None

    def _to_int(value: object | None) -> int | None:
        try:
            return int(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    raw_scene_count = _to_int(ep_data.get("scene_count"))
    target_scene_count = (
        raw_scene_count if raw_scene_count and raw_scene_count > 0 else None
    )

    raw_scenes = ep_data.get("scenes")
    scenes: list[dict] = []
    if isinstance(raw_scenes, list):
        for idx, raw in enumerate(raw_scenes, start=1):
            if not isinstance(raw, dict):
                continue

            slug_line = _as_nonempty_str(raw.get("slug_line")) or _as_nonempty_str(
                raw.get("title")
            )
            summary = (
                _as_nonempty_str(raw.get("summary"))
                or _as_nonempty_str(raw.get("description"))
                or _as_nonempty_str(raw.get("beat_summary"))
            )
            location = (
                _as_nonempty_str(raw.get("location"))
                or _as_nonempty_str(raw.get("environment"))
                or _as_nonempty_str(raw.get("setting"))
            )
            time_of_day = (
                _as_nonempty_str(raw.get("time_of_day"))
                or _as_nonempty_str(raw.get("time"))
                or _as_nonempty_str(raw.get("period"))
            )

            # 空对象/无任何有效字段 => 视为无效场景，触发后续自动补全
            if not (slug_line or summary or location or time_of_day):
                continue

            scene_number = _to_int(raw.get("scene_number")) or idx
            scenes.append(
                {
                    **raw,
                    "scene_number": scene_number,
                    "slug_line": slug_line or f"SCENE {scene_number} - beat",
                    "summary": summary or "本场景推进剧情。",
                    "time_of_day": time_of_day or "unspecified",
                    "location": location or "unspecified",
                }
            )

    if not scenes:
        plot_points = ep_data.get("plot_points") or []
        if isinstance(plot_points, list) and plot_points:
            for idx, pp in enumerate(plot_points, start=1):
                desc = None
                timing = None
                if isinstance(pp, dict):
                    desc = _as_nonempty_str(pp.get("description"))
                    timing = _as_nonempty_str(pp.get("timing"))
                scenes.append(
                    {
                        "scene_number": idx,
                        "slug_line": f"SCENE {idx} - {timing or 'beat'}",
                        "summary": desc or "本场景推进剧情。",
                        "time_of_day": "unspecified",
                        "location": "unspecified",
                    }
                )
        else:
            scenes.append(
                {
                    "scene_number": 1,
                    "slug_line": "SCENE 1 - beat",
                    "summary": _as_nonempty_str(ep_data.get("summary"))
                    or "本集开篇场景。",
                    "time_of_day": "unspecified",
                    "location": "unspecified",
                }
            )

    # 若模型给了 scene_count，则尽量对齐数量（不足补齐，超出截断）
    if target_scene_count:
        scenes = scenes[:target_scene_count]
        while len(scenes) < target_scene_count:
            idx = len(scenes) + 1
            scenes.append(
                {
                    "scene_number": idx,
                    "slug_line": f"SCENE {idx} - beat",
                    "summary": "本场景推进剧情。",
                    "time_of_day": "unspecified",
                    "location": "unspecified",
                }
            )

    # 统一场景编号，避免缺失/重复导致前端展示不稳定
    for idx, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            continue
        if _to_int(scene.get("scene_number")) is None:
            scene["scene_number"] = idx
        scene.setdefault("slug_line", f"SCENE {idx} - beat")
        scene.setdefault("summary", "本场景推进剧情。")
        scene.setdefault("time_of_day", "unspecified")
        scene.setdefault("location", "unspecified")

    scene_count = target_scene_count or (len(scenes) if scenes else None)
    # 写回，确保后续落库使用的是清洗/补全后的 scenes（避免原始 payload 含空对象导致写入无效场景）
    ep_data["scenes"] = scenes
    if scene_count is not None:
        ep_data["scene_count"] = scene_count
    return scenes, scene_count
