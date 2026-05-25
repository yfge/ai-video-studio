from typing import Any, Dict, List, Optional

from app.api.v1.endpoints.scripts_catalog import router as catalog_router
from app.api.v1.endpoints.scripts_create import router as create_router
from app.api.v1.endpoints.scripts_generation_queue import (
    router as generation_queue_router,
)
from app.api.v1.endpoints.scripts_lists import get_scripts as _get_scripts
from app.api.v1.endpoints.scripts_lists import router as lists_router
from app.api.v1.endpoints.scripts_prompt import router as prompt_router
from app.api.v1.endpoints.scripts_records import router as records_router
from app.api.v1.endpoints.scripts_regeneration import router as regeneration_router
from app.api.v1.endpoints.scripts_route_utils import not_deleted as _not_deleted
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.script import Episode, Script, Story
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.generation_requests import ScriptGenerationRequest
from app.schemas.script import ScriptListItemResponse, ScriptResponse
from app.services.ai.script_text import build_script_text
from app.services.ai_service import ai_service
from app.services.narrative_quality_gate import (
    NarrativeQualityGateError,
    attach_quality_gate_failure_to_task,
    enforce_script_quality_gate_with_repair,
)
from app.services.script.content_normalization import (
    normalize_script_content as _normalize_script_content_impl,
)
from app.services.script.context_payloads import (
    build_character_profiles as _build_character_profiles_impl,
)
from app.services.script.context_payloads import (
    build_episode_data as _build_episode_data_impl,
)
from app.services.script.context_payloads import (
    build_story_data as _build_story_data_impl,
)
from app.services.script.context_payloads import (
    collect_previous_episode_summaries as _collect_previous_episode_summaries_impl,
)
from app.services.script.production_metadata import (
    merge_production_pipeline_metadata as _merge_production_pipeline_metadata_impl,
)
from app.services.script.production_pipeline import (
    run_auto_timeline_placeholders,
    run_production_script_generation,
)
from app.services.script.scene_utils import (
    extract_episode_scenes as _extract_episode_scenes_impl,
)
from app.services.script.story_structure_sync import (
    build_scene_payload_from_script_data as _build_scene_payload_from_script_data_impl,
)
from app.services.script.story_structure_sync import (
    sync_script_scenes_to_story_structure as _sync_script_scenes_to_story_structure_impl,
)
from app.utils.json_utils import extract_json_block
from app.utils.marketing_meta import apply_marketing_overrides, merge_marketing_meta
from app.utils.script_parser import extract_script_structure
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session


def _collect_previous_episode_summaries(
    db: Session,
    story_id: int,
    current_episode_number: int,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    return _collect_previous_episode_summaries_impl(
        db,
        story_id,
        current_episode_number,
        limit=limit,
    )


def _build_character_profiles(story: Story) -> List[Dict[str, Any]]:
    return _build_character_profiles_impl(story)


def _build_episode_data(episode: Episode) -> Dict[str, Any]:
    return _build_episode_data_impl(episode)


def _extract_episode_scenes(episode: Episode) -> List[Dict[str, Any]]:
    return _extract_episode_scenes_impl(episode)


def _build_story_data(
    story: Story,
    *,
    previous_episode_summaries: List[Dict[str, Any]],
    character_profiles: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return _build_story_data_impl(
        story,
        previous_episode_summaries=previous_episode_summaries,
        character_profiles=character_profiles,
    )


def _normalize_script_content(
    ai_content: Dict[str, Any],
    *,
    format_type: str,
    language: str,
    default_scenes: Optional[List[Dict[str, Any]]] = None,
    episode_number: Optional[int] = None,
    template_style: Optional[str] = None,
    target_chars_per_episode: Optional[int] = None,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    return _normalize_script_content_impl(
        ai_content,
        format_type=format_type,
        language=language,
        default_scenes=default_scenes,
        episode_number=episode_number,
        template_style=template_style,
        target_chars_per_episode=target_chars_per_episode,
        title=title,
    )


def _build_scene_payload_from_script_data(
    scene_raw: Any,
    idx: int,
    script_id: int,
) -> Any:
    return _build_scene_payload_from_script_data_impl(
        scene_raw,
        idx,
        script_id,
    )


def _sync_script_scenes_to_story_structure(
    db: Session,
    script: Script,
    *,
    allow_overwrite: bool = False,
) -> Dict[str, int]:
    return _sync_script_scenes_to_story_structure_impl(
        db,
        script,
        allow_overwrite=allow_overwrite,
    )


def _merge_production_pipeline_metadata(
    db: Session,
    script: Script,
    *,
    production_meta: Dict[str, Any],
    scoring_artifacts: Optional[Dict[str, Any]],
) -> None:
    _merge_production_pipeline_metadata_impl(
        db,
        script,
        production_meta=production_meta,
        scoring_artifacts=scoring_artifacts,
    )


def _populate_dialogues_and_stage_if_missing(
    scenes: List[Dict[str, Any]],
    dialogues: List[Dict[str, Any]],
    stage_directions: List[Dict[str, Any]],
    *,
    story: Story | None = None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Fill missing dialogues/stage_directions without misleading "fake" lines.

    Note: Real dialogue completion should be done at generation time (ScriptLangGraphAgent).
    This function is only a last-resort safeguard to keep downstream pipelines running.
    """
    from app.services.script_missing_parts import (
        populate_dialogues_and_stage_if_missing,
    )

    return populate_dialogues_and_stage_if_missing(
        scenes,
        dialogues,
        stage_directions,
        story=story,
    )


router = APIRouter()
router.include_router(catalog_router)
router.include_router(prompt_router)
router.include_router(generation_queue_router)
router.include_router(create_router)


@router.post("/generate", response_model=ScriptResponse)
async def generate_script(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """使用AI生成剧本"""
    # 获取剧集信息（按用户隔离）
    episode_query = _not_deleted(db.query(Episode), Episode).join(
        Story, Episode.story_id == Story.id
    )
    if not current_user.is_admin and not current_user.is_superuser:
        episode_query = episode_query.filter(Story.user_id == current_user.id)
    episode = episode_query.filter(Episode.id == request.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    # 获取故事信息（确保与当前用户匹配）
    story = db.query(Story).filter(Story.id == episode.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

    previous_episode_summaries = _collect_previous_episode_summaries(
        db, story.id, episode.episode_number
    )
    character_profiles = _build_character_profiles(story)

    # 构建剧集数据
    episode_data = _build_episode_data(episode)

    # 构建故事数据
    story_data = _build_story_data(
        story,
        previous_episode_summaries=previous_episode_summaries,
        character_profiles=character_profiles,
    )
    hook_plan_payload = request.hook_plan.model_dump() if request.hook_plan else None
    ad_snippets_payload = (
        [snippet.model_dump() for snippet in request.ad_snippets]
        if request.ad_snippets
        else None
    )
    marketing_overrides = {
        "market_region": request.market_region,
        "micro_genre": request.micro_genre,
        "hook_plan": hook_plan_payload,
        "twist_density": request.twist_density,
        "cliffhanger_plan": request.cliffhanger_plan,
        "ad_snippets": ad_snippets_payload,
    }
    apply_marketing_overrides(story_data, marketing_overrides)
    apply_marketing_overrides(episode_data, marketing_overrides)

    # 调用AI服务生成剧本
    # 解析模型与提供商
    prefer_provider = None
    model_id = request.model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    result = await ai_service.generate_script(
        episode=episode_data,
        story=story_data,
        format_type=request.format_type,
        language=request.language,
        dialogue_style=request.dialogue_style,
        scene_detail_level=request.scene_detail_level,
        template_style=request.template_style,
        target_chars_per_episode=request.target_chars_per_episode,
        quality_threshold=request.quality_threshold,
        additional_requirements=request.additional_requirements,
        style_preferences=request.style_preferences,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=request.temperature or 0.7,
    )

    if not result:
        raise HTTPException(status_code=500, detail="AI剧本生成失败")

    # 结构化 agent 运行信息，便于落库与排查
    agent_run: Dict[str, Any] = {}
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
    raw_content = result.get("content")
    if isinstance(raw_content, dict):
        ai_content = raw_content
    else:
        parsed = extract_json_block(raw_content)
        if parsed:
            ai_content = parsed
        else:
            source_text = raw_content or ""
            extracted = extract_script_structure(source_text)
            ai_content = {
                "content": extracted.get("content", source_text),
                "scenes": extracted.get("scenes", []),
                "dialogues": extracted.get("dialogues", []),
                "stage_directions": extracted.get("stage_directions", []),
                "metadata": extracted.get("metadata", {}),
            }

    ai_content = _normalize_script_content(
        ai_content,
        format_type=request.format_type,
        language=request.language,
        default_scenes=episode_data.get("scenes"),
        episode_number=episode.episode_number,
        template_style=request.template_style,
        target_chars_per_episode=request.target_chars_per_episode,
        title=episode.title,
    )

    # 提取剧本内容
    script_content = ai_content.get("content", "")
    scenes = ai_content.get("scenes", [])
    dialogues_raw = ai_content.get("dialogues", [])
    stage_directions_raw = ai_content.get("stage_directions", [])
    dialogues, stage_directions = _populate_dialogues_and_stage_if_missing(
        scenes, dialogues_raw, stage_directions_raw, story=story
    )
    if not dialogues_raw or not stage_directions_raw:
        script_content = build_script_text(
            scenes,
            dialogues,
            stage_directions,
            format_type=request.format_type,
            language=request.language,
            episode_number=episode.episode_number,
            template_style=request.template_style,
            target_chars_per_episode=request.target_chars_per_episode,
            title=episode.title,
        )
        ai_content["content"] = script_content
    try:
        result, ai_content, _quality_gate = (
            await enforce_script_quality_gate_with_repair(
                ai_manager=getattr(ai_service, "ai_manager", None),
                result=result,
                content={
                    **ai_content,
                    "content": script_content,
                    "scenes": scenes,
                    "dialogues": dialogues,
                    "stage_directions": stage_directions,
                },
                story=story_data,
                story_model=story,
                episode_id=episode.id,
                db=db,
                model=model_id,
                prefer_provider=prefer_provider,
                temperature=request.temperature or 0.7,
                lint_threshold=request.quality_threshold,
                target_chars_per_episode=request.target_chars_per_episode,
            )
        )
    except NarrativeQualityGateError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"剧本质量校验失败: {exc}",
        ) from exc
    script_content = ai_content.get("content", "")
    scenes = ai_content.get("scenes", [])
    dialogues = ai_content.get("dialogues", [])
    stage_directions = ai_content.get("stage_directions", [])
    if agent_run:
        agent_run = {**agent_run, "quality_gate": result.get("quality_gate")}

    # 计算统计信息
    word_count = len(script_content.split()) if script_content else 0
    character_count = len(script_content) if script_content else 0
    page_count = max(1, character_count // 2000)  # 估算页数

    # 创建剧本记录
    # 额外元数据
    extra_meta = {
        k: v
        for k, v in ai_content.items()
        if k not in {"content", "scenes", "dialogues", "stage_directions", "metadata"}
    }
    marketing_defaults = merge_marketing_meta(
        story_data,
        episode_data,
        marketing_overrides,
    )
    if marketing_defaults:
        extra_meta = {**extra_meta, **marketing_defaults}
    if agent_run:
        extra_meta = {
            **(extra_meta or {}),
            "agent_run": agent_run,
        }

    db_script = Script(
        episode_id=request.episode_id,
        title=f"{episode.title} - 剧本",
        content=script_content,
        scenes=scenes,
        dialogues=dialogues,
        stage_directions=stage_directions,
        format_type=request.format_type,
        language=request.language,
        page_count=page_count,
        word_count=word_count,
        character_count=character_count,
        generation_prompt=result.get("prompt"),
        ai_model=result.get("generation_method"),
        generation_params={
            "generation_mode": request.generation_mode,
            "auto_timeline_pipeline": request.auto_timeline_pipeline,
            "dialogue_style": request.dialogue_style,
            "scene_detail_level": request.scene_detail_level,
            "template_style": request.template_style,
            "target_chars_per_episode": request.target_chars_per_episode,
            "quality_threshold": request.quality_threshold,
            "market_region": request.market_region,
            "micro_genre": request.micro_genre,
            "hook_plan": hook_plan_payload,
            "twist_density": request.twist_density,
            "cliffhanger_plan": request.cliffhanger_plan,
            "ad_snippets": ad_snippets_payload,
            "additional_requirements": request.additional_requirements,
            "style_preferences": request.style_preferences,
            "model": request.model,
            "temperature": request.temperature or 0.7,
        },
        extra_metadata=extra_meta or None,
        status="draft",
    )

    db.add(db_script)
    db.commit()
    db.refresh(db_script)

    try:
        _sync_script_scenes_to_story_structure(db, db_script)
    except Exception:
        logger = get_logger()
        logger.warning("同步规范化场景失败（generate）", exc_info=True)

    return ScriptResponse.from_orm(db_script)


def _process_script_generation_task(task_id: int, request_dict: dict, user_id: int):
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        logger = get_logger("storyboard_image_task")
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        episode = (
            db.query(Episode)
            .join(Story, Episode.story_id == Story.id)
            .filter(
                Episode.id == request_dict.get("episode_id"),
                Story.user_id == user_id,
            )
            .first()
        )
        if not episode:
            raise RuntimeError("剧集不存在")
        story = db.query(Story).filter(Story.id == episode.story_id).first()
        if not story:
            raise RuntimeError("故事不存在")

        previous_episode_summaries = _collect_previous_episode_summaries(
            db, story.id, episode.episode_number
        )
        character_profiles = _build_character_profiles(story)

        episode_data = _build_episode_data(episode)
        story_data = _build_story_data(
            story,
            previous_episode_summaries=previous_episode_summaries,
            character_profiles=character_profiles,
        )
        marketing_overrides = {
            "market_region": request_dict.get("market_region"),
            "micro_genre": request_dict.get("micro_genre"),
            "hook_plan": request_dict.get("hook_plan"),
            "twist_density": request_dict.get("twist_density"),
            "cliffhanger_plan": request_dict.get("cliffhanger_plan"),
            "ad_snippets": request_dict.get("ad_snippets"),
        }
        apply_marketing_overrides(story_data, marketing_overrides)
        apply_marketing_overrides(episode_data, marketing_overrides)

        import anyio

        prefer_provider = None
        model_id = request_dict.get("model")
        if model_id and ":" in model_id:
            prefer_provider, model_id = model_id.split(":", 1)

        generation_mode = request_dict.get("generation_mode") or "production"
        auto_timeline_pipeline = request_dict.get("auto_timeline_pipeline")
        if auto_timeline_pipeline is None:
            auto_timeline_pipeline = generation_mode == "production"

        async def _generate_prepared_attempt(
            attempt_no: int, additional_requirements: str
        ) -> Dict[str, Any]:
            result = await ai_service.generate_script(
                episode=episode_data,
                story=story_data,
                format_type=request_dict.get("format_type", "screenplay"),
                language=request_dict.get("language", "zh-CN"),
                dialogue_style=request_dict.get("dialogue_style", "natural"),
                scene_detail_level=request_dict.get("scene_detail_level", "medium"),
                template_style=request_dict.get(
                    "template_style", "commercial_vertical_drama"
                ),
                target_chars_per_episode=request_dict.get(
                    "target_chars_per_episode", 1300
                ),
                quality_threshold=request_dict.get("quality_threshold", 9.0),
                additional_requirements=additional_requirements,
                style_preferences=request_dict.get("style_preferences"),
                model=model_id,
                prefer_provider=prefer_provider,
                temperature=request_dict.get("temperature", 0.7),
            )
            if not result:
                raise RuntimeError("AI剧本生成失败")

            agent_run: Dict[str, Any] = {}
            if isinstance(result, dict):
                agent_run = {
                    "generation_method": result.get("generation_method"),
                    "template_used": result.get("template_used"),
                    "provider_used": result.get("provider_used"),
                    "model_used": result.get("model_used"),
                    "usage": result.get("usage"),
                    "reasoning": result.get("reasoning"),
                    "attempt": attempt_no,
                }

            raw_content = result.get("content")
            if isinstance(raw_content, dict):
                ai_content = raw_content
            else:
                parsed = extract_json_block(raw_content)
                if parsed:
                    ai_content = parsed
                else:
                    source_text = raw_content or ""
                    extracted = extract_script_structure(source_text)
                    ai_content = {
                        "content": extracted.get("content", source_text),
                        "scenes": extracted.get("scenes", []),
                        "dialogues": extracted.get("dialogues", []),
                        "stage_directions": extracted.get("stage_directions", []),
                        "metadata": extracted.get("metadata", {}),
                    }

            ai_content = _normalize_script_content(
                ai_content,
                format_type=request_dict.get("format_type", "screenplay"),
                language=request_dict.get("language", "zh-CN"),
                default_scenes=episode_data.get("scenes"),
                episode_number=episode.episode_number,
                template_style=request_dict.get(
                    "template_style", "commercial_vertical_drama"
                ),
                target_chars_per_episode=request_dict.get(
                    "target_chars_per_episode", 1300
                ),
                title=episode.title,
            )

            script_content = ai_content.get("content", "")
            scenes = ai_content.get("scenes", [])
            dialogues_raw = ai_content.get("dialogues", [])
            stage_directions_raw = ai_content.get("stage_directions", [])
            dialogues, stage_directions = _populate_dialogues_and_stage_if_missing(
                scenes, dialogues_raw, stage_directions_raw, story=story
            )
            if not dialogues_raw or not stage_directions_raw:
                script_content = build_script_text(
                    scenes,
                    dialogues,
                    stage_directions,
                    format_type=request_dict.get("format_type", "screenplay"),
                    language=request_dict.get("language", "zh-CN"),
                    episode_number=episode.episode_number,
                    template_style=request_dict.get(
                        "template_style", "commercial_vertical_drama"
                    ),
                    target_chars_per_episode=request_dict.get(
                        "target_chars_per_episode", 1300
                    ),
                    title=episode.title,
                )
                ai_content["content"] = script_content

            result, ai_content, _quality_gate = (
                await enforce_script_quality_gate_with_repair(
                    ai_manager=getattr(ai_service, "ai_manager", None),
                    result=result,
                    content={
                        **ai_content,
                        "content": script_content,
                        "scenes": scenes,
                        "dialogues": dialogues,
                        "stage_directions": stage_directions,
                    },
                    story=story_data,
                    story_model=story,
                    episode_id=episode.id,
                    db=db,
                    model=model_id,
                    prefer_provider=prefer_provider,
                    temperature=request_dict.get("temperature", 0.7),
                    lint_threshold=request_dict.get("quality_threshold", 9.0),
                    target_chars_per_episode=request_dict.get(
                        "target_chars_per_episode", 1300
                    ),
                )
            )
            if agent_run:
                agent_run = {**agent_run, "quality_gate": result.get("quality_gate")}
            return {
                "result": result,
                "agent_run": agent_run,
                "ai_content": ai_content,
                "script_content": ai_content.get("content", ""),
                "scenes": ai_content.get("scenes", []),
                "dialogues": ai_content.get("dialogues", []),
                "stage_directions": ai_content.get("stage_directions", []),
            }

        async def _score_prepared_attempt(generated: Dict[str, Any]) -> Dict[str, Any]:
            from app.services.scoring.artifacts import generate_scoring_artifacts

            episode_ctx = dict(episode_data or {})
            episode_ctx.setdefault("episode_number", episode.episode_number)
            episode_ctx.setdefault("title", episode.title)
            episode_ctx.setdefault("summary", episode.summary)
            marketing_defaults = merge_marketing_meta(
                story_data,
                episode_data,
                marketing_overrides,
            )
            return await generate_scoring_artifacts(
                ai_service=ai_service,
                script_content=generated.get("script_content") or "",
                story=story_data,
                episode=episode_ctx,
                scenes=generated.get("scenes") or [],
                dialogues=generated.get("dialogues") or [],
                hook_plan=marketing_defaults.get("hook_plan"),
                prefer_provider=prefer_provider,
                prefer_model=model_id,
            )

        production_meta: Dict[str, Any] = {}
        scoring_artifacts: Optional[Dict[str, Any]] = None
        if generation_mode == "production":

            async def _run_production():
                return await run_production_script_generation(
                    story=story_data,
                    episode=episode_data,
                    marketing_overrides=marketing_overrides,
                    base_additional_requirements=request_dict.get(
                        "additional_requirements"
                    ),
                    generate_attempt=_generate_prepared_attempt,
                    score_attempt=_score_prepared_attempt,
                )

            production_result = anyio.run(_run_production)
            selected = production_result.selected
            production_meta = production_result.metadata()
            scoring_artifacts = selected.get("scoring")
            result = selected["result"]
            ai_content = selected["ai_content"]
            script_content = selected["script_content"]
            scenes = selected["scenes"]
            dialogues = selected["dialogues"]
            stage_directions = selected["stage_directions"]
            agent_run = {
                **(selected.get("agent_run") or {}),
                "generation_mode": "production",
                "scoring": scoring_artifacts,
                "production_pipeline": production_meta,
            }
        else:
            prepared = anyio.run(
                _generate_prepared_attempt(
                    1, request_dict.get("additional_requirements") or ""
                )
            )
            result = prepared["result"]
            ai_content = prepared["ai_content"]
            script_content = prepared["script_content"]
            scenes = prepared["scenes"]
            dialogues = prepared["dialogues"]
            stage_directions = prepared["stage_directions"]
            agent_run = prepared.get("agent_run") or {}

        extra_meta = {
            k: v
            for k, v in ai_content.items()
            if k
            not in {"content", "scenes", "dialogues", "stage_directions", "metadata"}
        }
        marketing_defaults = merge_marketing_meta(
            story_data,
            episode_data,
            marketing_overrides,
        )
        if marketing_defaults:
            extra_meta = {**extra_meta, **marketing_defaults}

        if generation_mode != "production" and marketing_defaults:
            try:

                async def _run_standard_scoring():
                    return await _score_prepared_attempt(
                        {
                            "script_content": script_content,
                            "scenes": scenes,
                            "dialogues": dialogues,
                        }
                    )

                scoring_artifacts = anyio.run(_run_standard_scoring)
                extra_meta = {**(extra_meta or {}), "scoring": scoring_artifacts}
                if agent_run:
                    agent_run = {**agent_run, "scoring": scoring_artifacts}
            except Exception:
                logger.warning("生成评分/投流表失败（generate-async）", exc_info=True)
                if agent_run is not None:
                    agent_run = {**agent_run, "scoring_error": "failed_to_generate"}
        if generation_mode == "production":
            production_meta["auto_timeline_pipeline"] = {
                "enabled": bool(auto_timeline_pipeline),
                "status": "pending" if auto_timeline_pipeline else "skipped",
            }
            extra_meta = {
                **(extra_meta or {}),
                "production_pipeline": production_meta,
                "scoring": scoring_artifacts,
            }
            if agent_run is not None:
                agent_run = {
                    **agent_run,
                    "production_pipeline": production_meta,
                    "scoring": scoring_artifacts,
                }
        if agent_run:
            extra_meta = {
                **(extra_meta or {}),
                "agent_run": agent_run,
            }

        word_count = len(script_content.split()) if script_content else 0
        character_count = len(script_content) if script_content else 0
        page_count = max(1, character_count // 2000)

        sc = Script(
            episode_id=request_dict.get("episode_id"),
            title=f"{episode.title} - 剧本",
            content=script_content,
            scenes=scenes,
            dialogues=dialogues,
            stage_directions=stage_directions,
            format_type=request_dict.get("format_type", "screenplay"),
            language=request_dict.get("language", "zh-CN"),
            page_count=page_count,
            word_count=word_count,
            character_count=character_count,
            generation_prompt=result.get("prompt"),
            ai_model=result.get("generation_method"),
            generation_params={
                k: request_dict.get(k)
                for k in [
                    "generation_mode",
                    "auto_timeline_pipeline",
                    "dialogue_style",
                    "scene_detail_level",
                    "template_style",
                    "target_chars_per_episode",
                    "quality_threshold",
                    "market_region",
                    "micro_genre",
                    "hook_plan",
                    "twist_density",
                    "cliffhanger_plan",
                    "ad_snippets",
                    "additional_requirements",
                    "style_preferences",
                    "model",
                    "temperature",
                ]
            },
            extra_metadata=extra_meta or None,
            status="draft",
        )
        db.add(sc)
        db.commit()
        db.refresh(sc)

        try:
            _sync_script_scenes_to_story_structure(db, sc)
        except Exception:
            logger = get_logger()
            logger.warning("同步规范化场景失败（generate-async）", exc_info=True)

        if generation_mode == "production" and production_meta:
            if auto_timeline_pipeline:
                try:

                    async def _run_auto_timeline():
                        return await run_auto_timeline_placeholders(
                            db,
                            story=story,
                            episode=episode,
                            script=sc,
                            hook_schedule=production_meta.get("hook_schedule") or {},
                            scoring=scoring_artifacts,
                            user_id=user_id,
                        )

                    auto_result = anyio.run(_run_auto_timeline)
                    production_meta["auto_timeline_pipeline"] = {
                        "enabled": True,
                        **auto_result,
                    }
                except Exception as exc:
                    logger.warning(
                        "生产级自动时间轴/分镜占位失败（generate-async）",
                        exc_info=True,
                    )
                    production_meta["auto_timeline_pipeline"] = {
                        "enabled": True,
                        "status": "failed",
                        "error": str(exc),
                    }
            _merge_production_pipeline_metadata(
                db,
                sc,
                production_meta=production_meta,
                scoring_artifacts=scoring_artifacts,
            )

        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{sc.id}"
            db.commit()
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            if isinstance(e, NarrativeQualityGateError):
                attach_quality_gate_failure_to_task(task, e.quality_gate)
            db.commit()
    finally:
        db.close()


def _process_script_regeneration_task(task_id: int, request_dict: dict, user_id: int):
    """异步剧本重新生成任务处理函数。

    与 _process_script_generation_task 类似，但更新现有剧本而非创建新剧本。
    """
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        logger = get_logger("script_regenerate_task")
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = request_dict.get("script_id")
        script = (
            db.query(Script)
            .join(Episode, Script.episode_id == Episode.id)
            .join(Story, Episode.story_id == Story.id)
            .filter(
                Script.id == script_id,
                Story.user_id == user_id,
            )
            .first()
        )
        if not script:
            raise RuntimeError("剧本不存在")

        episode = script.episode
        if not episode or getattr(episode, "is_deleted", False):
            raise RuntimeError("剧集不存在")

        story = episode.story
        if not story or getattr(story, "is_deleted", False):
            raise RuntimeError("故事不存在")

        previous_episode_summaries = _collect_previous_episode_summaries(
            db, story.id, episode.episode_number
        )
        character_profiles = _build_character_profiles(story)

        episode_data = _build_episode_data(episode)
        story_data = _build_story_data(
            story,
            previous_episode_summaries=previous_episode_summaries,
            character_profiles=character_profiles,
        )

        marketing_overrides = {
            "market_region": request_dict.get("market_region"),
            "micro_genre": request_dict.get("micro_genre"),
            "hook_plan": request_dict.get("hook_plan"),
            "twist_density": request_dict.get("twist_density"),
            "cliffhanger_plan": request_dict.get("cliffhanger_plan"),
            "ad_snippets": request_dict.get("ad_snippets"),
        }
        apply_marketing_overrides(story_data, marketing_overrides)
        apply_marketing_overrides(episode_data, marketing_overrides)

        # 计算场景预算（如果有 duration_minutes）
        scene_budgets = None
        duration_minutes = request_dict.get("duration_minutes")
        if duration_minutes and duration_minutes > 0:
            scenes = episode_data.get("scenes", [])
            if scenes:
                from app.services.duration_orchestrator.utils import (
                    allocate_scene_budgets,
                )

                try:
                    scene_budgets, _ = allocate_scene_budgets(
                        total_duration_minutes=duration_minutes,
                        scenes=scenes,
                    )
                    logger.info(
                        "剧本重新生成: 分配场景预算",
                        extra={
                            "script_id": script_id,
                            "duration_minutes": duration_minutes,
                            "scene_count": len(scene_budgets),
                        },
                    )
                except Exception as e:
                    logger.warning(f"分配场景预算失败: {e}")

        import anyio

        prefer_provider = None
        model_id = request_dict.get("model")
        if model_id and ":" in model_id:
            prefer_provider, model_id = model_id.split(":", 1)

        async def _run():
            return await ai_service.generate_script(
                episode=episode_data,
                story=story_data,
                format_type=request_dict.get("format_type") or script.format_type,
                language=request_dict.get("language") or script.language,
                dialogue_style=request_dict.get("dialogue_style", "natural"),
                scene_detail_level=request_dict.get("scene_detail_level", "medium"),
                template_style=request_dict.get(
                    "template_style", "commercial_vertical_drama"
                ),
                target_chars_per_episode=request_dict.get(
                    "target_chars_per_episode", 1300
                ),
                quality_threshold=request_dict.get("quality_threshold", 9.0),
                additional_requirements=request_dict.get("additional_requirements"),
                style_preferences=request_dict.get("style_preferences"),
                model=model_id,
                prefer_provider=prefer_provider,
                temperature=request_dict.get("temperature", 0.7),
                scene_budgets=scene_budgets,
            )

        result = anyio.run(_run)
        if not result:
            raise RuntimeError("AI剧本重新生成失败")

        agent_run: Dict[str, Any] = {}
        if isinstance(result, dict):
            agent_run = {
                "generation_method": result.get("generation_method"),
                "template_used": result.get("template_used"),
                "provider_used": result.get("provider_used"),
                "model_used": result.get("model_used"),
                "usage": result.get("usage"),
                "reasoning": result.get("reasoning"),
            }

        raw_content = result.get("content")
        if isinstance(raw_content, dict):
            ai_content = raw_content
        else:
            parsed = extract_json_block(raw_content)
            if parsed:
                ai_content = parsed
            else:
                source_text = raw_content or ""
                extracted = extract_script_structure(source_text)
                ai_content = {
                    "content": extracted.get("content", source_text),
                    "scenes": extracted.get("scenes", []),
                    "dialogues": extracted.get("dialogues", []),
                    "stage_directions": extracted.get("stage_directions", []),
                    "metadata": extracted.get("metadata", {}),
                }

        ai_content = _normalize_script_content(
            ai_content,
            format_type=request_dict.get("format_type") or script.format_type,
            language=request_dict.get("language") or script.language,
            default_scenes=episode_data.get("scenes"),
            episode_number=episode.episode_number,
            template_style=request_dict.get(
                "template_style", "commercial_vertical_drama"
            ),
            target_chars_per_episode=request_dict.get("target_chars_per_episode", 1300),
            title=episode.title,
        )

        script_content = ai_content.get("content", "")
        scenes = ai_content.get("scenes", [])
        dialogues_raw = ai_content.get("dialogues", [])
        stage_directions_raw = ai_content.get("stage_directions", [])
        dialogues, stage_directions = _populate_dialogues_and_stage_if_missing(
            scenes, dialogues_raw, stage_directions_raw, story=story
        )
        if not dialogues_raw or not stage_directions_raw:
            script_content = build_script_text(
                scenes,
                dialogues,
                stage_directions,
                format_type=request_dict.get("format_type") or script.format_type,
                language=request_dict.get("language") or script.language,
                episode_number=episode.episode_number,
                template_style=request_dict.get(
                    "template_style", "commercial_vertical_drama"
                ),
                target_chars_per_episode=request_dict.get(
                    "target_chars_per_episode", 1300
                ),
                title=episode.title,
            )
            ai_content["content"] = script_content

        async def _run_quality_gate():
            return await enforce_script_quality_gate_with_repair(
                ai_manager=getattr(ai_service, "ai_manager", None),
                result=result,
                content={
                    **ai_content,
                    "content": script_content,
                    "scenes": scenes,
                    "dialogues": dialogues,
                    "stage_directions": stage_directions,
                },
                story=story_data,
                story_model=story,
                episode_id=episode.id,
                db=db,
                model=model_id,
                prefer_provider=prefer_provider,
                temperature=request_dict.get("temperature", 0.7),
                lint_threshold=request_dict.get("quality_threshold", 9.0),
                target_chars_per_episode=request_dict.get(
                    "target_chars_per_episode", 1300
                ),
            )

        result, ai_content, _quality_gate = anyio.run(_run_quality_gate)
        script_content = ai_content.get("content", "")
        scenes = ai_content.get("scenes", [])
        dialogues = ai_content.get("dialogues", [])
        stage_directions = ai_content.get("stage_directions", [])
        if agent_run:
            agent_run = {**agent_run, "quality_gate": result.get("quality_gate")}

        # 创建新剧本而非覆盖原有剧本
        # 解析原版本号并递增
        old_version = script.version or "1.0"
        try:
            major, minor = old_version.split(".")
            new_version = f"{major}.{int(minor) + 1}"
        except (ValueError, AttributeError):
            new_version = "1.1"

        # 构建新剧本的元数据，保留原剧本ID作为父级
        new_meta = dict(script.extra_metadata or {})
        new_meta["parent_script_id"] = script.id
        new_meta["parent_script_business_id"] = script.business_id
        new_meta["regenerated_from_version"] = old_version
        marketing_defaults = merge_marketing_meta(
            story_data,
            episode_data,
            marketing_overrides,
        )
        if marketing_defaults:
            new_meta = {**new_meta, **marketing_defaults}

        if marketing_defaults:
            try:
                from app.services.scoring.artifacts import generate_scoring_artifacts

                async def _run_scoring():
                    episode_ctx = dict(episode_data or {})
                    episode_ctx.setdefault("episode_number", episode.episode_number)
                    episode_ctx.setdefault("title", episode.title)
                    episode_ctx.setdefault("summary", episode.summary)
                    return await generate_scoring_artifacts(
                        ai_service=ai_service,
                        script_content=script_content,
                        story=story_data,
                        episode=episode_ctx,
                        scenes=scenes,
                        dialogues=dialogues,
                        hook_plan=marketing_defaults.get("hook_plan"),
                        prefer_provider=prefer_provider,
                        prefer_model=model_id,
                    )

                scoring_artifacts = anyio.run(_run_scoring)
                new_meta = {**new_meta, "scoring": scoring_artifacts}
                if agent_run:
                    agent_run = {**agent_run, "scoring": scoring_artifacts}
            except Exception:
                logger.warning("生成评分/投流表失败（regenerate-async）", exc_info=True)
                if agent_run is not None:
                    agent_run = {**agent_run, "scoring_error": "failed_to_generate"}
        if agent_run:
            new_meta["agent_run"] = agent_run

        # 生成新标题
        base_title = script.title or f"剧本 - {episode.title}"
        # 移除之前的版本后缀（如果有）
        import re

        base_title = re.sub(r"\s*\(v[\d.]+\)$", "", base_title)
        new_title = f"{base_title} (v{new_version})"

        new_script = Script(
            episode_id=script.episode_id,
            episode_business_id=script.episode_business_id,
            title=new_title,
            content=script_content,
            scenes=scenes,
            dialogues=dialogues,
            stage_directions=stage_directions,
            format_type=request_dict.get("format_type") or script.format_type,
            language=request_dict.get("language") or script.language,
            generation_prompt=result.get("prompt"),
            ai_model=result.get("generation_method"),
            generation_params=request_dict,
            status="draft",
            version=new_version,
            tags=script.tags,
            extra_metadata=new_meta,
            word_count=len(script_content.split()) if script_content else 0,
            character_count=len(script_content) if script_content else 0,
            page_count=max(1, len(script_content) // 2000) if script_content else 1,
        )
        db.add(new_script)
        db.commit()
        db.refresh(new_script)

        # 软删除旧剧本，保留历史记录但从列表隐藏
        script.soft_delete(
            user_id=user_id,
            reason=f"regenerated_to_script_{new_script.id}",
        )
        db.commit()

        logger.info(
            "剧本重新生成: 创建新版本并软删除旧版本",
            extra={
                "old_script_id": script.id,
                "new_script_id": new_script.id,
                "old_version": old_version,
                "new_version": new_version,
            },
        )

        try:
            _sync_script_scenes_to_story_structure(db, new_script)
        except Exception:
            logger.warning("同步规范化场景失败（regenerate-async）", exc_info=True)

        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{new_script.id}"
            db.commit()
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            if isinstance(e, NarrativeQualityGateError):
                attach_quality_gate_failure_to_task(task, e.quality_gate)
            db.commit()
    finally:
        db.close()


router.include_router(lists_router)
router.include_router(records_router)
router.include_router(regeneration_router)


@router.get("", response_model=List[ScriptListItemResponse], include_in_schema=False)
async def get_scripts_no_slash(
    episode_id: Optional[int] = Query(None),
    episode_business_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    format_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """兼容无尾斜杠的 /api/v1/scripts 请求，避免 307 重定向。"""
    return await _get_scripts(
        episode_id=episode_id,
        episode_business_id=episode_business_id,
        skip=skip,
        limit=limit,
        status=status,
        format_type=format_type,
        current_user=current_user,
        db=db,
    )
