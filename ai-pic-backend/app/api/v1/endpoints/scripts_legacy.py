import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.script import Episode, Script, Story
from app.models.story_structure import Scene
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
from app.schemas.generation_requests import ScriptGenerationRequest
from app.schemas.script import (
    ScriptCreate,
    ScriptListItemResponse,
    ScriptResponse,
    ScriptUpdate,
)
from app.schemas.story_structure import SceneCreate, ShotCreate
from app.services import story_structure_service as story_structure_svc
from app.services.ai.script_text import build_script_text
from app.services.ai_service import ai_service
from app.services.narrative_quality_gate import (
    NarrativeQualityGateError,
    attach_quality_gate_failure_to_task,
    enforce_script_quality_gate_with_repair,
)
from app.services.task_worker import script_generate_task, script_regenerate_task
from app.utils.json_utils import extract_json_block
from app.utils.marketing_meta import apply_marketing_overrides, merge_marketing_meta
from app.utils.script_parser import extract_script_structure
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, load_only


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _to_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_uuid(value: Any) -> str:
    if not value:
        return str(uuid4())
    try:
        return str(UUID(str(value)))
    except Exception:
        return str(uuid4())


def _ensure_iso_datetime(value: Any, fallback: str) -> str:
    if value is None:
        return fallback
    if isinstance(value, datetime):
        return value.isoformat()
    try:
        return datetime.fromisoformat(str(value)).isoformat()
    except Exception:
        return fallback


def _abs_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("http"):
        # 将 localhost/127.0.0.1 替换为 INTERNAL_BACKEND_URL，便于容器内访问
        parsed = urlparse(url)
        if parsed.hostname in {"localhost", "127.0.0.1"}:
            base = (
                getattr(settings, "INTERNAL_BACKEND_URL", None)
                or "http://localhost:8000"
            ).rstrip("/")
            base_parsed = urlparse(base)
            rebuilt = parsed._replace(
                netloc=base_parsed.netloc, scheme=base_parsed.scheme
            )
            return urlunparse(rebuilt)
        return url
    if not url.startswith("/"):
        url = "/" + url
    base = (
        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
    ).rstrip("/")
    return f"{base}{url}"


def _friendly_task_title(
    prefix: str, script: Script, episode: Episode | None, story: Story | None
) -> str:
    story_label = ""
    if story and story.title:
        story_label = str(story.title)
    elif story:
        story_label = f"故事{story.id}"

    episode_label = ""
    if episode:
        ep_num = (
            f"第{episode.episode_number}集"
            if episode.episode_number is not None
            else f"剧集{episode.id}"
        )
        ep_title = f" {episode.title}" if episode.title else ""
        episode_label = f"{ep_num}{ep_title}"

    parts = [prefix]
    if story_label and episode_label:
        parts.append(f"{story_label} / {episode_label}")
    elif story_label:
        parts.append(story_label)
    elif episode_label:
        parts.append(episode_label)
    else:
        parts.append(f"剧本{script.id}")
    return " - ".join(parts)


def _collect_previous_episode_summaries(
    db: Session,
    story_id: int,
    current_episode_number: int,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """收集前情提要信息，默认回溯最近几集。"""
    if current_episode_number <= 1:
        return []

    previous_episodes = (
        db.query(Episode)
        .filter(
            Episode.story_id == story_id,
            Episode.episode_number < current_episode_number,
        )
        .order_by(Episode.episode_number.desc())
        .limit(limit)
        .all()
    )

    summaries: List[Dict[str, Any]] = []
    for ep in reversed(previous_episodes):
        summaries.append(
            {
                "episode_number": ep.episode_number,
                "title": ep.title,
                "summary": ep.summary or "",
                "plot_points": ep.plot_points or [],
                "conflicts": ep.conflicts or [],
            }
        )
    return summaries


def _build_character_profiles(story: Story) -> List[Dict[str, Any]]:
    """汇总故事角色设定，为提示词提供丰富的角色介绍。"""

    profiles: Dict[str, Dict[str, Any]] = {}

    def _ensure_profile(name: str) -> Dict[str, Any]:
        profile = profiles.setdefault(name, {"name": name})
        return profile

    main_chars = (
        story.main_characters if isinstance(story.main_characters, list) else []
    )
    for raw in main_chars:
        if isinstance(raw, dict):
            name = raw.get("name") or raw.get("character_name") or raw.get("id")
            if not name:
                continue
            profile = _ensure_profile(str(name))
            profile.setdefault(
                "role", raw.get("role") or raw.get("type") or raw.get("role_type")
            )
            profile.setdefault(
                "description", raw.get("description") or raw.get("summary")
            )
            profile.setdefault(
                "personality", raw.get("personality") or raw.get("traits")
            )
            profile.setdefault("motivation", raw.get("motivation") or raw.get("goal"))
            profile.setdefault("arc", raw.get("arc") or raw.get("character_arc"))
        elif isinstance(raw, str):
            profile = _ensure_profile(raw)
            profile.setdefault("description", "主要角色")

    story_characters = getattr(story, "story_characters", []) or []
    for sc in story_characters:
        name = getattr(sc, "character_name", None)
        if not name and getattr(sc, "virtual_ip", None):
            name = getattr(sc.virtual_ip, "name", None)
        if not name:
            continue
        profile = _ensure_profile(str(name))
        profile.setdefault("role", getattr(sc, "role_type", None))
        profile.setdefault("description", getattr(sc, "background", None))
        profile.setdefault("personality", getattr(sc, "personality", None))
        profile.setdefault("motivation", getattr(sc, "motivation", None))
        profile.setdefault("arc", getattr(sc, "character_arc", None))
        relationships = getattr(sc, "relationships", None)
        if relationships and not profile.get("relationships"):
            profile["relationships"] = relationships
        if getattr(sc, "virtual_ip", None):
            vip_desc = getattr(sc.virtual_ip, "description", None)
            if vip_desc and not profile.get("description"):
                profile["description"] = vip_desc

    cleaned_profiles: List[Dict[str, Any]] = []
    for profile in profiles.values():
        cleaned_profiles.append(
            {k: v for k, v in profile.items() if v not in (None, "", [], {}, set())}
        )

    return cleaned_profiles


def _build_episode_data(episode: Episode) -> Dict[str, Any]:
    scenes = _extract_episode_scenes(episode)
    scene_count = episode.scene_count or (len(scenes) if scenes else None)
    marketing_meta = merge_marketing_meta(
        episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {},
        (
            episode.generation_params
            if isinstance(episode.generation_params, dict)
            else {}
        ),
    )
    return {
        "episode_number": episode.episode_number,
        "title": episode.title,
        "story_format": getattr(getattr(episode, "story", None), "story_format", None),
        "summary": episode.summary,
        "plot_points": episode.plot_points,
        "character_arcs": episode.character_arcs,
        "conflicts": episode.conflicts,
        "duration_minutes": episode.duration_minutes,
        "scene_count": scene_count,
        "scenes": scenes,
        **marketing_meta,
    }


def _extract_episode_scenes(episode: Episode) -> List[Dict[str, Any]]:
    """从剧集元数据中提取场景列表，保证基础字段齐全。"""
    if not episode:
        return []

    meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    scenes_src = meta.get("scenes") if isinstance(meta, dict) else []
    if not isinstance(scenes_src, list):
        return []

    cleaned: List[Dict[str, Any]] = []
    for idx, raw in enumerate(scenes_src, start=1):
        if not isinstance(raw, dict):
            continue
        base = dict(raw)
        scene_no = _to_int(base.get("scene_number")) or idx
        base["scene_number"] = scene_no
        summary = (
            base.get("summary") or base.get("description") or base.get("beat_summary")
        )
        location = base.get("location") or base.get("place") or base.get("setting")
        time_of_day = base.get("time_of_day") or base.get("time")
        if summary:
            base.setdefault("summary", summary)
            base.setdefault("description", summary)
        if location:
            base.setdefault("location", location)
        if time_of_day:
            base.setdefault("time_of_day", time_of_day)
        if not base.get("slug_line"):
            if location and time_of_day:
                base["slug_line"] = f"{location} - {time_of_day}"
            elif summary:
                base["slug_line"] = str(summary)[:80]
            else:
                base["slug_line"] = f"Scene {scene_no}"
        cleaned.append(base)

    return cleaned


def _build_story_data(
    story: Story,
    *,
    previous_episode_summaries: List[Dict[str, Any]],
    character_profiles: List[Dict[str, Any]],
) -> Dict[str, Any]:
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
        "previous_episode_summaries": previous_episode_summaries,
        "character_profiles": character_profiles,
        **marketing_meta,
    }


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
    """确保场景/对白/舞台指示结构化并符合前端期望字段。"""
    normalized = dict(ai_content or {})
    fallback_scenes = default_scenes or []

    def _safe_int(value: Any) -> Optional[int]:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    raw_scenes = normalized.get("scenes")
    if not isinstance(raw_scenes, list) or len(raw_scenes) == 0:
        raw_scenes = fallback_scenes
    scenes: List[Dict[str, Any]] = []
    for idx, scene in enumerate(raw_scenes, start=1):
        base = (
            dict(scene)
            if isinstance(scene, dict)
            else {"description": str(scene) if scene is not None else ""}
        )
        scene_no = _safe_int(base.get("scene_number")) or idx
        desc = (
            base.get("description")
            or base.get("summary")
            or base.get("slug_line")
            or base.get("story_beat")
            or base.get("title")
        )
        base["scene_number"] = scene_no
        if desc:
            base.setdefault("description", desc)
            base.setdefault("summary", desc)
        if not base.get("slug_line"):
            location = base.get("location") or base.get("place")
            time_of_day = base.get("time_of_day") or base.get("time")
            if location and time_of_day:
                base["slug_line"] = f"{location} - {time_of_day}"
            elif desc:
                base["slug_line"] = desc[:80]
        scenes.append(base)

    metadata = normalized.get("metadata") or {}
    if scenes and not metadata.get("total_scenes"):
        metadata["total_scenes"] = len(scenes)
    normalized["metadata"] = metadata
    normalized["scenes"] = scenes

    raw_dialogues = normalized.get("dialogues") or []
    dialogues: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw_dialogues, start=1):
        if isinstance(item, str):
            dialogues.append(
                {
                    "scene_number": (
                        scenes[idx - 1]["scene_number"]
                        if idx - 1 < len(scenes)
                        else idx
                    ),
                    "content": item,
                }
            )
            continue
        if not isinstance(item, dict):
            continue
        dialog = dict(item)
        content = (
            dialog.get("content")
            or dialog.get("line")
            or dialog.get("text")
            or dialog.get("dialogue")
        )
        if not content:
            continue
        dialog["content"] = content
        sn = _safe_int(dialog.get("scene_number"))
        if sn is None:
            dialog["scene_number"] = (
                scenes[idx - 1]["scene_number"] if idx - 1 < len(scenes) else idx
            )
        dialogues.append(dialog)

    raw_stage = normalized.get("stage_directions") or []
    stage_directions: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw_stage, start=1):
        if isinstance(item, str):
            stage_directions.append(
                {
                    "scene_number": (
                        scenes[idx - 1]["scene_number"]
                        if idx - 1 < len(scenes)
                        else idx
                    ),
                    "content": item,
                }
            )
            continue
        if not isinstance(item, dict):
            continue
        direction = dict(item)
        content = (
            direction.get("content")
            or direction.get("direction")
            or direction.get("description")
        )
        if not content:
            continue
        direction["content"] = content
        sn = _safe_int(direction.get("scene_number"))
        if sn is None:
            direction["scene_number"] = (
                scenes[idx - 1]["scene_number"] if idx - 1 < len(scenes) else idx
            )
        stage_directions.append(direction)

    # 若未提供场景但对白/舞台指示包含 scene_number，则补充占位场景
    if not scenes:
        scene_numbers = {
            item.get("scene_number")
            for item in dialogues
            if isinstance(item, dict) and item.get("scene_number")
        }
        scene_numbers |= {
            item.get("scene_number")
            for item in stage_directions
            if isinstance(item, dict) and item.get("scene_number")
        }
        scene_numbers = {sn for sn in scene_numbers if sn is not None}
        for idx, sn in enumerate(sorted(scene_numbers)):
            scenes.append(
                {
                    "scene_number": _safe_int(sn) or idx + 1,
                    "slug_line": f"Scene {sn}",
                    "summary": "",
                    "description": "",
                }
            )

    normalized["scenes"] = scenes
    normalized["dialogues"] = dialogues
    normalized["stage_directions"] = stage_directions

    content_value = normalized.get("content")
    if isinstance(content_value, dict):
        content_text = content_value.get("content") or ""
    else:
        content_text = content_value or ""
    if not content_text:
        content_text = build_script_text(
            scenes,
            dialogues,
            stage_directions,
            format_type=format_type,
            language=language,
            episode_number=episode_number,
            template_style=template_style,
            target_chars_per_episode=target_chars_per_episode,
            title=title,
        )
    normalized["content"] = content_text
    return normalized


def _build_scene_payload_from_script_data(
    scene_raw: Any,
    idx: int,
    script_id: int,
) -> Optional[SceneCreate]:
    """将剧本中的场景数据转换为 SceneCreate."""
    if isinstance(scene_raw, dict):
        base = dict(scene_raw)
    elif isinstance(scene_raw, str):
        base = {"summary": scene_raw, "description": scene_raw}
    else:
        return None

    scene_no = _to_int(base.get("scene_number")) or idx
    summary = base.get("summary") or base.get("description")
    location = base.get("location") or base.get("place")
    time_of_day = base.get("time_of_day") or base.get("time")

    slug_line = base.get("slug_line")
    if not slug_line:
        if location and time_of_day:
            slug_line = f"{location} - {time_of_day}"
        elif summary:
            slug_line = str(summary)[:80]
        else:
            slug_line = f"Scene {scene_no}"

    # 提取预估时长（秒），支持多种字段名
    estimated_duration = _to_int(
        base.get("estimated_duration_seconds")
        or base.get("duration_seconds")
        or base.get("estimated_duration")
    )

    return SceneCreate(
        script_id=script_id,
        scene_number=str(scene_no),
        slug_line=str(slug_line),
        location=location,
        time_of_day=time_of_day,
        summary=summary,
        estimated_duration_seconds=estimated_duration,
        status="draft",
    )


def _sync_script_scenes_to_story_structure(
    db: Session,
    script: Script,
    *,
    allow_overwrite: bool = False,
) -> Dict[str, int]:
    """
    将 Script.scenes 写入规范化 story_structure，若已有场景且未允许覆盖则跳过。
    返回创建统计，内部吞掉异常以避免打断主流程。
    """
    logger = get_logger()
    if not script or not script.id:
        return {"created": 0, "shots_created": 0, "skipped": 0}

    existing = story_structure_svc.list_scenes_by_script(db, script.id)
    if existing and not allow_overwrite:
        return {"created": 0, "shots_created": 0, "skipped": len(existing)}

    if allow_overwrite and existing:
        for sc in existing:
            try:
                story_structure_svc.delete_scene(db, sc.id)
            except Exception as exc:  # pragma: no cover - protective
                logger.warning("删除旧规范化场景失败: %s", exc)

    scenes_src = script.scenes or []
    if not scenes_src and isinstance(script.extra_metadata, dict):
        scenes_src = script.extra_metadata.get("scenes") or []

    created_scenes: List[Scene] = []
    seen_numbers: set[str] = set()
    for idx, raw in enumerate(scenes_src, start=1):
        payload = _build_scene_payload_from_script_data(raw, idx, script.id)
        if not payload:
            continue
        scene_key = payload.scene_number
        if scene_key in seen_numbers:
            continue
        seen_numbers.add(scene_key)
        try:
            created = story_structure_svc.create_scene(db, payload)
            created_scenes.append(created)
        except Exception as exc:  # pragma: no cover - protective
            logger.warning("写入规范化场景失败 scene=%s: %s", scene_key, exc)

    shots_created = 0
    for sc in created_scenes:
        try:
            story_structure_svc.create_shot(
                db,
                ShotCreate(
                    scene_id=sc.id,
                    shot_number="1",
                    status="planned",
                ),
            )
            shots_created += 1
        except Exception as exc:  # pragma: no cover - protective
            logger.warning("为场景创建占位镜头失败 scene_id=%s: %s", sc.id, exc)

    return {
        "created": len(created_scenes),
        "shots_created": shots_created,
        "skipped": len(existing) if existing and not allow_overwrite else 0,
    }


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


def _not_deleted(query, model):
    return query.filter(model.is_deleted.is_(False))


def _get_script_by_identifier(
    db: Session,
    script_id: Optional[int],
    script_business_id: Optional[str],
    current_user: User,
) -> Script:
    """按主键或 business_id 获取剧本，校验归属与软删状态。"""
    query = (
        _not_deleted(db.query(Script), Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Episode.is_deleted.is_(False))
        .filter(Story.is_deleted.is_(False))
    )
    if script_business_id:
        query = query.filter(Script.business_id == script_business_id)
    elif script_id:
        query = query.filter(Script.id == script_id)
    else:
        raise HTTPException(status_code=400, detail="script identifier missing")

    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)

    script = query.first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    return script


@router.get("/formats")
async def get_script_formats():
    """获取剧本格式列表"""
    return [
        {"value": "screenplay", "label": "影视剧本"},
        {"value": "stage_play", "label": "舞台剧本"},
        {"value": "radio_drama", "label": "广播剧本"},
        {"value": "short_video", "label": "短视频脚本"},
        {"value": "live_stream", "label": "直播脚本"},
        {"value": "animation", "label": "动画脚本"},
    ]


@router.get("/languages")
async def get_script_languages():
    """获取剧本语言列表"""
    return [
        {"value": "zh-CN", "label": "简体中文"},
        {"value": "zh-TW", "label": "繁体中文"},
        {"value": "en-US", "label": "英语"},
        {"value": "ja-JP", "label": "日语"},
        {"value": "ko-KR", "label": "韩语"},
    ]


@router.post("/", response_model=ScriptResponse)
async def create_script(
    script: ScriptCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """创建剧本"""
    # 检查剧集是否存在且归属当前用户（或管理员）
    episode_query = _not_deleted(db.query(Episode), Episode).join(
        Story, Episode.story_id == Story.id
    )
    if not current_user.is_admin and not current_user.is_superuser:
        episode_query = episode_query.filter(Story.user_id == current_user.id)
    episode = episode_query.filter(Episode.id == script.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    # 计算字数和字符数
    word_count = len(script.content.split()) if script.content else 0
    character_count = len(script.content) if script.content else 0

    db_script = Script(
        **script.dict(), word_count=word_count, character_count=character_count
    )
    db.add(db_script)
    db.commit()
    db.refresh(db_script)

    try:
        _sync_script_scenes_to_story_structure(db, db_script)
    except Exception:
        logger = get_logger()
        logger.warning("同步规范化场景失败（create）", exc_info=True)

    return ScriptResponse.from_orm(db_script)


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


@router.post("/prompt/preview")
async def preview_script_prompt(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    episode_query = db.query(Episode).join(Story, Episode.story_id == Story.id)
    if not current_user.is_admin and not current_user.is_superuser:
        episode_query = episode_query.filter(Story.user_id == current_user.id)
    episode = episode_query.filter(Episode.id == request.episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")
    story = db.query(Story).filter(Story.id == episode.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="故事不存在")

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
    variables = {
        "story": story_data,
        "episode": episode_data,
        "format_type": request.format_type,
        "language": request.language,
        "dialogue_style": request.dialogue_style,
        "scene_detail_level": request.scene_detail_level,
        "template_style": request.template_style,
        "target_chars_per_episode": request.target_chars_per_episode,
        "quality_threshold": request.quality_threshold,
        "additional_requirements": request.additional_requirements,
        "style_preferences": request.style_preferences or [],
    }
    prompt = PromptManager().render_prompt(
        PromptTemplate.SCRIPT_GENERATION.value, variables
    )
    return {"success": True, "data": {"prompt": prompt}}


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

        async def _run():
            return await ai_service.generate_script(
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
                additional_requirements=request_dict.get("additional_requirements"),
                style_preferences=request_dict.get("style_preferences"),
                model=model_id,
                prefer_provider=prefer_provider,
                temperature=request_dict.get("temperature", 0.7),
            )

        result = anyio.run(_run)
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
                extra_meta = {**(extra_meta or {}), "scoring": scoring_artifacts}
                if agent_run:
                    agent_run = {**agent_run, "scoring": scoring_artifacts}
            except Exception:
                logger.warning("生成评分/投流表失败（generate-async）", exc_info=True)
                if agent_run is not None:
                    agent_run = {**agent_run, "scoring_error": "failed_to_generate"}
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


@router.post("/generate-async")
async def generate_script_async(
    request: ScriptGenerationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    t = Task(
        title=f"生成剧本 - 剧集{request.episode_id}",
        description="异步剧本生成",
        task_type=TaskType.SCRIPT_GENERATION,
        prompt=f"Script for episode {request.episode_id}",
        parameters=json.dumps(request.dict(), ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    # 交给 Celery worker 处理
    script_generate_task.delay(t.id, request.dict(), current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


@router.get("/", response_model=List[ScriptListItemResponse])
async def get_scripts(
    episode_id: Optional[int] = Query(None),
    episode_business_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    format_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取剧本列表"""
    list_columns = (
        Script.id,
        Script.business_id,
        Script.episode_id,
        Script.episode_business_id,
        Script.title,
        Script.format_type,
        Script.language,
        Script.status,
        Script.version,
        Script.tags,
        Script.page_count,
        Script.word_count,
        Script.character_count,
        Script.ai_model,
        Script.created_at,
        Script.updated_at,
    )
    base_query = (
        _not_deleted(db.query(Script), Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Episode.is_deleted.is_(False))
        .filter(Story.is_deleted.is_(False))
    )

    if episode_id:
        base_query = base_query.filter(Script.episode_id == episode_id)
    if episode_business_id:
        base_query = base_query.filter(Episode.business_id == episode_business_id)

    if status:
        base_query = base_query.filter(Script.status == status)

    if format_type:
        base_query = base_query.filter(Script.format_type == format_type)

    # 只允许访问当前用户故事下的剧本
    if not current_user.is_admin and not current_user.is_superuser:
        base_query = base_query.filter(Story.user_id == current_user.id)

    # Avoid MySQL sort buffer exhaustion by ordering on indexed primary key.
    id_subquery = (
        base_query.with_entities(Script.id)
        .order_by(Script.id.desc())
        .offset(skip)
        .limit(limit)
        .subquery()
    )
    scripts = (
        _not_deleted(db.query(Script), Script)
        .options(load_only(*list_columns))
        .join(id_subquery, Script.id == id_subquery.c.id)
        .order_by(Script.id.desc())
        .all()
    )
    return [ScriptListItemResponse.from_orm(script) for script in scripts]


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
    """
    兼容无尾斜杠的 /api/v1/scripts 请求，避免 307 重定向。

    内部直接复用 get_scripts 的过滤与分页逻辑。
    """
    return await get_scripts(
        episode_id=episode_id,
        episode_business_id=episode_business_id,
        skip=skip,
        limit=limit,
        status=status,
        format_type=format_type,
        current_user=current_user,
        db=db,
    )


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取剧本详情"""
    script = _get_script_by_identifier(db, script_id, None, current_user)
    return ScriptResponse.from_orm(script)


@router.get("/business/{script_business_id}", response_model=ScriptResponse)
async def get_script_by_business_id(
    script_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 获取剧本详情"""
    script = _get_script_by_identifier(db, None, script_business_id, current_user)
    return ScriptResponse.from_orm(script)


@router.put("/{script_id}", response_model=ScriptResponse)
async def update_script(
    script_id: int,
    script_update: ScriptUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """更新剧本"""
    script = _get_script_by_identifier(db, script_id, None, current_user)

    # 更新剧本信息
    for field, value in script_update.dict(exclude_unset=True).items():
        setattr(script, field, value)

    # 重新计算统计信息
    if script_update.content:
        script.word_count = len(script_update.content.split())
        script.character_count = len(script_update.content)
        script.page_count = max(1, script.character_count // 2000)

    db.commit()
    db.refresh(script)

    try:
        _sync_script_scenes_to_story_structure(db, script)
    except Exception:
        logger = get_logger()
        logger.warning("同步规范化场景失败（update）", exc_info=True)

    return ScriptResponse.from_orm(script)


@router.put("/business/{script_business_id}", response_model=ScriptResponse)
async def update_script_by_business_id(
    script_business_id: str,
    script_update: ScriptUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 更新剧本"""
    script = _get_script_by_identifier(db, None, script_business_id, current_user)

    for field, value in script_update.dict(exclude_unset=True).items():
        setattr(script, field, value)

    if script_update.content:
        script.word_count = len(script_update.content.split())
        script.character_count = len(script_update.content)
        script.page_count = max(1, script.character_count // 2000)

    db.commit()
    db.refresh(script)

    try:
        _sync_script_scenes_to_story_structure(db, script)
    except Exception:
        logger = get_logger()
        logger.warning("同步规范化场景失败（update）", exc_info=True)

    return ScriptResponse.from_orm(script)


@router.delete("/{script_id}")
async def delete_script(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """删除剧本"""
    script = _get_script_by_identifier(db, script_id, None, current_user)
    script.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()

    return {"message": "剧本删除成功"}


@router.delete("/business/{script_business_id}")
async def delete_script_by_business_id(
    script_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 删除剧本"""
    script = _get_script_by_identifier(db, None, script_business_id, current_user)
    script.soft_delete(user_id=current_user.id, reason="user delete")
    db.commit()

    return {"message": "剧本删除成功"}


@router.get("/episode/{episode_id}", response_model=List[ScriptListItemResponse])
async def get_episode_scripts(
    episode_id: int,
    episode_business_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """获取剧集的所有剧本"""
    episode_query = _not_deleted(db.query(Episode), Episode).join(
        Story, Episode.story_id == Story.id
    )
    if not current_user.is_admin and not current_user.is_superuser:
        episode_query = episode_query.filter(Story.user_id == current_user.id)
    if episode_business_id:
        episode_query = episode_query.filter(Episode.business_id == episode_business_id)
    episode = episode_query.filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    # 为避免在 MySQL 中对大文本结果做排序耗尽 sort buffer，
    # 这里不在 SQL 层做 ORDER BY；改为拉取后在 Python 内按 id 倒序排序，
    # 让前端默认使用最新一条。
    scripts = (
        _not_deleted(db.query(Script), Script)
        .options(
            load_only(
                Script.id,
                Script.business_id,
                Script.episode_id,
                Script.episode_business_id,
                Script.title,
                Script.format_type,
                Script.language,
                Script.status,
                Script.version,
                Script.tags,
                Script.page_count,
                Script.word_count,
                Script.character_count,
                Script.ai_model,
                Script.created_at,
                Script.updated_at,
            )
        )
        .filter(Script.episode_id == episode_id)
        .limit(50)
        .all()
    )
    scripts_sorted = sorted(
        scripts, key=lambda s: int(getattr(s, "id", 0)), reverse=True
    )
    return [ScriptListItemResponse.from_orm(script) for script in scripts_sorted]


@router.get(
    "/episode/business/{episode_business_id}",
    response_model=List[ScriptListItemResponse],
)
async def get_episode_scripts_by_business_id(
    episode_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 episode business_id 获取剧本列表"""
    episode_query = _not_deleted(db.query(Episode), Episode).join(
        Story, Episode.story_id == Story.id
    )
    if not current_user.is_admin and not current_user.is_superuser:
        episode_query = episode_query.filter(Story.user_id == current_user.id)
    episode = episode_query.filter(Episode.business_id == episode_business_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="剧集不存在")

    scripts = (
        _not_deleted(db.query(Script), Script)
        .options(
            load_only(
                Script.id,
                Script.business_id,
                Script.episode_id,
                Script.episode_business_id,
                Script.title,
                Script.format_type,
                Script.language,
                Script.status,
                Script.version,
                Script.tags,
                Script.page_count,
                Script.word_count,
                Script.character_count,
                Script.ai_model,
                Script.created_at,
                Script.updated_at,
            )
        )
        .filter(Script.episode_id == episode.id)
        .limit(50)
        .all()
    )
    scripts_sorted = sorted(
        scripts, key=lambda s: int(getattr(s, "id", 0)), reverse=True
    )
    return [ScriptListItemResponse.from_orm(script) for script in scripts_sorted]


async def _regenerate_script_instance(
    *,
    db: Session,
    script: Script,
    episode: Episode,
    story: Story,
    override_model: Optional[str] = None,
) -> Script:
    """复用的剧本重新生成逻辑，供业务ID/主键路由调用。

    Args:
        override_model: 可选，覆盖原有模型设置，格式为 "provider:model_id" 或 "model_id"
    """
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

    original_params = script.generation_params or {}
    marketing_overrides = {
        "market_region": original_params.get("market_region"),
        "micro_genre": original_params.get("micro_genre"),
        "hook_plan": original_params.get("hook_plan"),
        "twist_density": original_params.get("twist_density"),
        "cliffhanger_plan": original_params.get("cliffhanger_plan"),
        "ad_snippets": original_params.get("ad_snippets"),
    }
    apply_marketing_overrides(story_data, marketing_overrides)
    apply_marketing_overrides(episode_data, marketing_overrides)
    prefer_provider = None
    # 如果提供了 override_model，使用它；否则使用原有模型
    model_id = override_model if override_model else original_params.get("model")
    if isinstance(model_id, str) and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    result = await ai_service.generate_script(
        episode=episode_data,
        story=story_data,
        format_type=script.format_type,
        language=script.language,
        dialogue_style=original_params.get("dialogue_style", "natural"),
        scene_detail_level=original_params.get("scene_detail_level", "medium"),
        template_style=original_params.get(
            "template_style", "commercial_vertical_drama"
        ),
        target_chars_per_episode=original_params.get("target_chars_per_episode", 1300),
        quality_threshold=original_params.get("quality_threshold", 9.0),
        additional_requirements=f"重新生成第{episode.episode_number}集的剧本内容",
        style_preferences=original_params.get("style_preferences"),
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=original_params.get("temperature", 0.7),
    )

    if not result:
        raise HTTPException(status_code=500, detail="AI剧本重新生成失败")

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
        format_type=script.format_type,
        language=script.language,
        default_scenes=episode_data.get("scenes"),
        episode_number=episode.episode_number,
        template_style=original_params.get(
            "template_style", "commercial_vertical_drama"
        ),
        target_chars_per_episode=original_params.get("target_chars_per_episode", 1300),
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
            format_type=script.format_type,
            language=script.language,
            episode_number=episode.episode_number,
            template_style=original_params.get(
                "template_style", "commercial_vertical_drama"
            ),
            target_chars_per_episode=original_params.get(
                "target_chars_per_episode", 1300
            ),
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
                temperature=original_params.get("temperature", 0.7),
                lint_threshold=original_params.get("quality_threshold", 9.0),
                target_chars_per_episode=original_params.get(
                    "target_chars_per_episode", 1300
                ),
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
    script.content = script_content
    script.scenes = scenes
    script.dialogues = dialogues
    script.stage_directions = stage_directions
    script.generation_prompt = result.get("prompt")
    script.ai_model = result.get("generation_method")

    if agent_run:
        meta = dict(script.extra_metadata or {})
        marketing_defaults = merge_marketing_meta(
            story_data,
            episode_data,
            marketing_overrides,
        )
        if marketing_defaults:
            meta.update(marketing_defaults)
        meta["agent_run"] = agent_run
        script.extra_metadata = meta

    script.word_count = len(script_content.split()) if script_content else 0
    script.character_count = len(script_content) if script_content else 0
    script.page_count = max(1, script.character_count // 2000)

    db.commit()
    db.refresh(script)

    try:
        _sync_script_scenes_to_story_structure(db, script)
    except Exception:
        logger = get_logger()
        logger.warning("同步规范化场景失败（regenerate）", exc_info=True)

    return script


class ScriptRegenerateRequest(BaseModel):
    """剧本重新生成请求参数"""

    model: Optional[str] = Field(None, description="模型ID，格式为 provider:model_id")


def _build_script_regenerate_request(
    script: Script, episode: Episode, override_model: Optional[str] = None
) -> Dict[str, Any]:
    """构建剧本重新生成的请求参数字典。"""
    original_params = script.generation_params or {}
    # 获取剧集目标时长（分钟）
    duration_minutes = getattr(episode, "duration_minutes", None)
    return {
        "script_id": script.id,
        "format_type": script.format_type,
        "language": script.language,
        "dialogue_style": original_params.get("dialogue_style", "natural"),
        "scene_detail_level": original_params.get("scene_detail_level", "medium"),
        "market_region": original_params.get("market_region"),
        "micro_genre": original_params.get("micro_genre"),
        "hook_plan": original_params.get("hook_plan"),
        "twist_density": original_params.get("twist_density"),
        "cliffhanger_plan": original_params.get("cliffhanger_plan"),
        "ad_snippets": original_params.get("ad_snippets"),
        "additional_requirements": f"重新生成第{episode.episode_number}集的剧本内容",
        "style_preferences": original_params.get("style_preferences"),
        "model": override_model or original_params.get("model"),
        "temperature": original_params.get("temperature", 0.7),
        "duration_minutes": duration_minutes,
    }


@router.post("/{script_id}/regenerate")
async def regenerate_script_async(
    script_id: int,
    request: Optional[ScriptRegenerateRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步重新生成剧本内容

    返回 task_id 用于跟踪进度。

    可选参数:
    - model: 指定使用的模型，格式为 "provider:model_id"，不传则使用原有模型
    """
    script = _get_script_by_identifier(db, script_id, None, current_user)

    episode = script.episode
    if not episode or getattr(episode, "is_deleted", False):
        raise HTTPException(status_code=404, detail="剧集不存在")

    story = episode.story
    if not story or getattr(story, "is_deleted", False):
        raise HTTPException(status_code=404, detail="故事不存在")

    override_model = request.model if request else None
    request_dict = _build_script_regenerate_request(script, episode, override_model)

    t = Task(
        title=_friendly_task_title("剧本重新生成", script, episode, story),
        description=f"重新生成剧本 {script.id}（第{episode.episode_number}集）",
        task_type=TaskType.SCRIPT_GENERATION,
        prompt=f"Script regeneration for script {script.id}",
        parameters=json.dumps(request_dict, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    script_regenerate_task.delay(t.id, request_dict, current_user.id)
    return {
        "success": True,
        "data": {
            "task_id": t.id,
            "status": t.status,
            "message": "剧本重新生成任务已提交",
        },
    }


@router.post("/business/{script_business_id}/regenerate")
async def regenerate_script_by_business_id_async(
    script_business_id: str,
    request: Optional[ScriptRegenerateRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 异步重新生成剧本内容

    返回 task_id 用于跟踪进度。

    可选参数:
    - model: 指定使用的模型，格式为 "provider:model_id"，不传则使用原有模型
    """
    script = _get_script_by_identifier(db, None, script_business_id, current_user)
    episode = script.episode
    if not episode or getattr(episode, "is_deleted", False):
        raise HTTPException(status_code=404, detail="剧集不存在")
    story = episode.story
    if not story or getattr(story, "is_deleted", False):
        raise HTTPException(status_code=404, detail="故事不存在")

    override_model = request.model if request else None
    request_dict = _build_script_regenerate_request(script, episode, override_model)

    t = Task(
        title=_friendly_task_title("剧本重新生成", script, episode, story),
        description=f"重新生成剧本 {script.id}（第{episode.episode_number}集）",
        task_type=TaskType.SCRIPT_GENERATION,
        prompt=f"Script regeneration for script {script.id}",
        parameters=json.dumps(request_dict, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    script_regenerate_task.delay(t.id, request_dict, current_user.id)
    return {
        "success": True,
        "data": {
            "task_id": t.id,
            "status": t.status,
            "message": "剧本重新生成任务已提交",
        },
    }


@router.post("/{script_id}/export")
async def export_script(
    script_id: int,
    format: str = Query("txt", description="导出格式：txt, pdf, docx"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """导出剧本"""
    script = (
        db.query(Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Script.id == script_id)
        .filter(
            True
            if current_user.is_admin or current_user.is_superuser
            else Story.user_id == current_user.id
        )
        .first()
    )
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    # 这里可以实现不同格式的导出逻辑
    # 目前返回基本信息
    return {
        "script_id": script_id,
        "title": script.title,
        "format": format,
        "content": script.content,
        "export_time": "2024-01-01T00:00:00Z",
    }
