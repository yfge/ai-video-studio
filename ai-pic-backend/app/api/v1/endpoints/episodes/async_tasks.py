"""
Episode async generation endpoints and background tasks.

Handles asynchronous episode generation via Celery workers.
"""

import json
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.script import Story, Episode
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.virtual_ip import VirtualIP
from app.prompts.templates import PromptTemplate
from app.schemas.generation import EpisodePlanItem
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services.ai_service import ai_service
from app.services.episode_agent import EpisodeGenerationCallbacks
from app.services.task_worker import episode_generate_task
from app.services import story_structure_service
from app.utils.marketing_meta import apply_marketing_overrides, merge_marketing_meta
from app.utils.json_utils import extract_json_block
from .helpers import (
    is_episode_payload_valid,
    parse_step_outlines,
    persist_story_outlines,
    build_outline_rows,
    build_stub_episodes_from_outlines,
    update_task_progress,
    ensure_scenes,
)

router = APIRouter()


def _build_story_data(story: Story) -> Dict[str, Any]:
    """Build story data dict for AI generation."""
    marketing_meta = merge_marketing_meta(
        story.extra_metadata if isinstance(story.extra_metadata, dict) else {},
        story.generation_params if isinstance(story.generation_params, dict) else {},
    )
    return {
        "title": story.title,
        "story_format": getattr(story, "story_format", None),
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
        **marketing_meta,
    }


def _coerce_episode_payload(
    episode_data: Dict[str, Any], outline: Dict[str, Any] | None
) -> Dict[str, Any]:
    """Coerce episode payload to ensure required fields exist."""
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


def process_episode_generation_task(task_id: int, request_dict: dict, user_id: int):
    """Background task to generate episodes asynchronously.

    This function is called by Celery workers. It handles the full episode
    generation flow including outline creation and episode persistence.
    """
    from app.core.database import SessionLocal

    db = SessionLocal()
    created_ids: list[int] = []
    try:
        task: Task | None = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            update_task_progress(db, task, "剧集生成：准备调用模型")

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

        step_outlines: Dict[str, Any] | None = None
        outline_agent_run: Dict[str, Any] = {}
        treatment = None
        used_callbacks = False

        story_data = _build_story_data(story)
        marketing_overrides = {
            "market_region": request_dict.get("market_region"),
            "micro_genre": request_dict.get("micro_genre"),
            "hook_plan": request_dict.get("hook_plan"),
            "twist_density": request_dict.get("twist_density"),
            "cliffhanger_plan": request_dict.get("cliffhanger_plan"),
            "ad_snippets": request_dict.get("ad_snippets"),
        }
        apply_marketing_overrides(story_data, marketing_overrides)

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
                update_task_progress(db, task, message)

        def _on_outline(outlines: Dict[str, Any], meta: Dict[str, Any]) -> None:
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
            persist_story_outlines(
                story,
                outlines,
                prompt=meta.get("prompt"),
                agent_run=outline_agent_run,
            )
            _progress("剧集生成：大纲校验通过，写入故事信息")

            # Create treatment if outlines contain beats
            try:
                has_beats = any(
                    isinstance(item, dict) and item.get("beats")
                    for item in (outlines.get("episodes") or [])
                )
                if has_beats:
                    nonlocal treatment
                    treatment = story_structure_service.ensure_auto_treatment(
                        db,
                        story,
                        prompt_snapshot={
                            "outline_prompt": meta.get("prompt"),
                            "step_outlines_raw": meta.get("raw"),
                            "agent_generation_method": meta.get("generation_method"),
                        },
                    )
            except Exception as exc:
                ai_service.logger.warning(
                    "Failed to create treatment for step outlines",
                    extra={"error": str(exc), "story_id": story.id},
                )

        def _on_episode(episode_data: Dict[str, Any], meta: Dict[str, Any]) -> None:
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
                _progress(f"生成第{episode_number}集：schema异常，兜底写入")

            scenes, scene_count = ensure_scenes(coerced)
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
            marketing_defaults = merge_marketing_meta(story_data, marketing_overrides)
            if marketing_defaults:
                extra_meta = {**extra_meta, **marketing_defaults}

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
                    outline_rows = build_outline_rows(
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
                except Exception as exc:
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

        # Fallback path if callbacks were not used
        if not used_callbacks:
            _process_fallback_result(
                db=db,
                result=result,
                story=story,
                request_dict=request_dict,
                created_ids=created_ids,
                progress_fn=_progress,
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
            update_task_progress(db, task, final_desc)
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            update_task_progress(db, task, f"剧集生成失败：{e}")
    finally:
        db.close()


def _process_fallback_result(
    *,
    db: Session,
    result: Dict[str, Any],
    story: Story,
    request_dict: Dict[str, Any],
    created_ids: list[int],
    progress_fn,
) -> None:
    """Process AI result when callbacks were not used."""
    progress_fn("剧集生成：模型返回结果解析中")

    story_data = _build_story_data(story)
    marketing_overrides = {
        "market_region": request_dict.get("market_region"),
        "micro_genre": request_dict.get("micro_genre"),
        "hook_plan": request_dict.get("hook_plan"),
        "twist_density": request_dict.get("twist_density"),
        "cliffhanger_plan": request_dict.get("cliffhanger_plan"),
        "ad_snippets": request_dict.get("ad_snippets"),
    }
    apply_marketing_overrides(story_data, marketing_overrides)

    content = (
        result.get("normalized") if isinstance(result, dict) else None
    ) or extract_json_block(
        result.get("content") if isinstance(result, dict) else None
    )
    episodes_data = content.get("episodes", []) if content else []

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
    raw_step_outlines = None
    if isinstance(result, dict):
        raw_step_outlines = result.get("step_outlines") or result.get(
            "step_outlines_raw"
        )
    episode_count = request_dict.get("episode_count") or len(episodes_data) or 1
    parsed_outlines = (
        parse_step_outlines(raw_step_outlines, episode_count)
        if raw_step_outlines
        else None
    )
    if parsed_outlines:
        persist_story_outlines(
            story,
            parsed_outlines,
            prompt=(
                result.get("step_outline_prompt")
                if isinstance(result, dict)
                else None
            ),
            agent_run=agent_run,
        )
        progress_fn("剧集生成：大纲校验通过，写入故事信息")
        db.refresh(story)

    if not episodes_data and parsed_outlines:
        episodes_data = build_stub_episodes_from_outlines(
            parsed_outlines, episode_count
        )
        agent_run = {**agent_run, "fallback_from_outline": True}
        progress_fn("模型输出无效，使用大纲兜底生成")
    if not episodes_data:
        raise RuntimeError("AI生成内容格式错误")

    created_episodes: list[Episode] = []
    for i, ep_data in enumerate(episodes_data[:episode_count]):
        episode_number = ep_data.get("episode_number", i + 1)
        progress_fn(f"生成第{episode_number}集：校验中")
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
            progress_fn(f"生成第{episode_number}集：schema校验失败")
            continue
        if not is_episode_payload_valid(ep_data):
            progress_fn(f"生成第{episode_number}集：内容校验失败")
            continue

        scenes, scene_count = ensure_scenes(ep_data)
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
        marketing_defaults = merge_marketing_meta(story_data, marketing_overrides)
        if marketing_defaults:
            extra_meta = {**extra_meta, **marketing_defaults}

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
        progress_fn(f"生成第{episode_number}集：已落库")

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
            outline_rows = build_outline_rows(
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
        except Exception as exc:
            ai_service.logger.warning(
                "Failed to persist step outlines in async task",
                extra={"error": str(exc), "story_id": story.id},
            )


@router.post("/generate-async")
async def generate_episodes_async(
    request: EpisodeGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Generate episodes asynchronously via Celery worker."""
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

    # Delegate to Celery worker
    episode_generate_task.delay(t.id, request.dict(), current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}
