import json
import re
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse, urlunparse
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.script import Episode, Script, Story
from app.models.story_structure import Environment, Scene, SceneBeat, Shot
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.prompts.manager import PromptManager, prompt_manager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import StoryboardModel
from app.schemas.generation_requests import ScriptGenerationRequest
from app.schemas.script import (
    ScriptCreate,
    ScriptListItemResponse,
    ScriptResponse,
    ScriptUpdate,
)
from app.schemas.story_structure import SceneCreate, ShotCreate
from app.schemas.style import StyleSpec
from app.services import story_structure_service as story_structure_svc
from app.services.ai.storyboard_utils import build_storyboard_context
from app.services.ai_service import ai_service
from app.services.dialogue_audio_service import (
    generate_episode_audio_timeline,
    generate_scene_dialogue_audio,
    generate_storyboard_from_episode_audio_timeline,
)
from app.services.duration_controlled_dialogue_service import (
    generate_dialogue_with_duration_control,
)
from app.services.storage.oss_service import oss_service
from app.services.storyboard.storyboard_prompt_utils import (
    apply_storyboard_prompt_optimizations,
    render_keyframe_prompt,
)
from app.services.task_worker import (
    script_audio_storyboard_generate_task,
    script_audio_timeline_generate_task,
    script_dialogue_audio_generate_task,
    script_generate_task,
    script_regenerate_task,
    storyboard_generate_task,
    storyboard_image_generate_task,
    storyboard_video_generate_task,
    timeline_pipeline_generate_task,
)
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


def _normalize_reference_images(refs: list[str]) -> list[str]:
    """仅保留看起来像图片 URL 的参考图，避免将描述性文案当作 URL。"""
    allowed_ext = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg")
    normalized: list[str] = []
    for raw in refs:
        if not isinstance(raw, str):
            continue
        ref = raw.strip()
        if not ref:
            continue
        lower = ref.lower()
        base_path = lower.split("?", 1)[0]
        if lower.startswith(
            ("http://", "https://", "data:image/")
        ) or base_path.endswith(allowed_ext):
            normalized.append(_abs_url(ref))
    # 去重保持顺序
    seen = set()
    deduped: list[str] = []
    for u in normalized:
        if u and u not in seen:
            seen.add(u)
            deduped.append(u)
    return deduped


def _serialize_frame(frame: Dict[str, Any]) -> Dict[str, Any]:
    serialized: Dict[str, Any] = {}
    for key, val in frame.items():
        if isinstance(val, UUID):
            serialized[key] = str(val)
        elif isinstance(val, datetime):
            serialized[key] = val.isoformat()
        else:
            serialized[key] = val
    return serialized


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


def _load_existing_frames(script: Script) -> List[Dict[str, Any]]:
    storyboard = (
        (script.extra_metadata or {}).get("storyboard")
        if script.extra_metadata
        else None
    )
    frames = storyboard.get("frames") if isinstance(storyboard, dict) else None
    if not isinstance(frames, list):
        return []
    return [deepcopy(frame) for frame in frames if isinstance(frame, dict)]


def _augment_frames(
    frames: List[Dict[str, Any]],
    *,
    scene_map: Dict[int, Dict[str, Any]],
    generation_source: str,
    generation_method: str,
    generation_model: Optional[str],
) -> List[Dict[str, Any]]:
    now_iso = _now_iso()
    augmented: List[Dict[str, Any]] = []
    for raw in frames:
        frame = dict(raw or {})
        frame_id = _coerce_uuid(frame.get("frame_id"))
        frame["frame_id"] = frame_id
        scene_number = _to_int(frame.get("scene_number"))
        if scene_number is None:
            scene_number = _to_int(frame.get("scene_index"))
        if scene_number is not None:
            frame["scene_number"] = scene_number
            if scene_number in scene_map:
                frame.setdefault("scene_index", scene_number)
            elif scene_map:
                # 若超出范围，使用最接近的键
                closest = min(scene_map.keys(), key=lambda k: abs(k - scene_number))
                frame.setdefault("scene_index", closest)
        else:
            frame_index = frame.get("scene_index")
            if frame_index is None and scene_map:
                first_key = next(iter(scene_map.keys()), None)
                if first_key is not None:
                    frame["scene_number"] = first_key
                    frame["scene_index"] = first_key
            else:
                frame["scene_index"] = frame_index
        frame["generation_source"] = frame.get("generation_source") or generation_source
        frame["generation_method"] = frame.get("generation_method") or generation_method
        if generation_model:
            frame["generation_model"] = (
                frame.get("generation_model") or generation_model
            )
        frame["generated_at"] = _ensure_iso_datetime(frame.get("generated_at"), now_iso)
        frame["updated_at"] = now_iso
        if not isinstance(frame.get("reference_images"), list):
            frame["reference_images"] = []
        augmented.append(frame)
    return augmented


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
        content_text = ai_service._build_script_text(
            scenes,
            dialogues,
            stage_directions,
            format_type=format_type,
            language=language,
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


def _merge_frames(
    existing_frames: List[Dict[str, Any]],
    new_frames: List[Dict[str, Any]],
    selected_scenes: Optional[List[int]],
) -> List[Dict[str, Any]]:
    has_selection = selected_scenes is not None
    selected_set = (
        {s for s in (selected_scenes or []) if s is not None} if has_selection else None
    )
    merged: List[Dict[str, Any]] = []
    if existing_frames and selected_set:
        for frame in existing_frames:
            scene_number = _to_int(frame.get("scene_number"))
            if scene_number in selected_set:
                continue
            merged.append(deepcopy(frame))
    elif not has_selection:
        # 全量生成，旧分镜不保留
        merged = []
    else:
        merged = [deepcopy(frame) for frame in existing_frames]

    merged.extend(new_frames)
    merged.sort(
        key=lambda fr: (
            _to_int(fr.get("scene_number")) or 0,
            fr.get("frame_number") or 0,
        )
    )
    for idx, frame in enumerate(merged, start=1):
        frame["frame_number"] = idx
        if frame.get("scene_number") is not None and frame.get("scene_index") is None:
            frame["scene_index"] = _to_int(frame.get("scene_number"))
    return merged


def _enforce_storyboard_variety(frames: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    shot_cycle = ["远景", "中景", "近景", "特写"]
    movement_cycle = ["固定", "推", "拉", "摇", "移", "跟", "变焦"]
    composition_cycle = ["三分法", "对称", "前后景", "对角线", "中心对称"]
    seen: Dict[tuple[Any, str], int] = {}
    for frame in frames:
        desc = (frame.get("description") or "").strip()
        scene_no = _to_int(frame.get("scene_number"))
        key = (scene_no, desc)
        count = seen.get(key, -1) + 1
        seen[key] = count
        if count > 0:
            frame["shot_type"] = shot_cycle[(count + (scene_no or 0)) % len(shot_cycle)]
            frame["camera_movement"] = movement_cycle[
                (count + (scene_no or 0)) % len(movement_cycle)
            ]
            frame["composition"] = composition_cycle[
                (count + (scene_no or 0)) % len(composition_cycle)
            ]
            base_desc = desc or f"场景{scene_no or ''}"
            frame["description"] = (
                f"{base_desc}（变体{count + 1}，强调{frame['camera_movement']}）"
            )
            old_prompt = frame.get("ai_prompt")
            if isinstance(old_prompt, str) and old_prompt.strip():
                frame["ai_prompt"] = f"{frame['description']}\n{old_prompt}"
            else:
                frame["ai_prompt"] = frame["description"]
            frame["duration_seconds"] = max(
                2, min(12, (frame.get("duration_seconds") or 3) + ((count % 3) - 1))
            )
    return frames


def _trim_local(value: Any, limit: int = 120) -> str:
    if value is None:
        return ""
    text = str(value).replace("\n", " ").strip()
    return text[:limit] + ("…" if len(text) > limit else "")


def _collect_dialogues_for_scene(
    script_obj: Script, scene_number: Optional[int], limit: int = 2
) -> List[str]:
    results: List[str] = []
    for item in script_obj.dialogues or []:
        if isinstance(item, dict):
            sn = _to_int(item.get("scene_number"))
            content = item.get("content") or item.get("text")
        else:
            sn = None
            content = str(item)
        if scene_number is not None and sn != scene_number:
            continue
        if not content:
            continue
        results.append(_trim_local(content, 80))
        if len(results) >= limit:
            break
    return results


def _collect_stage_for_scene(
    script_obj: Script, scene_number: Optional[int], limit: int = 2
) -> List[str]:
    results: List[str] = []
    for item in script_obj.stage_directions or []:
        if isinstance(item, dict):
            sn = _to_int(item.get("scene_number"))
            content = item.get("content") or item.get("direction")
        else:
            sn = None
            content = str(item)
        if scene_number is not None and sn != scene_number:
            continue
        if not content:
            continue
        results.append(_trim_local(content, 80))
        if len(results) >= limit:
            break
    return results


def _compose_fallback_text(
    scene_payload: Any,
    scene_number: Optional[int],
    *,
    script_obj: Script,
    base_text: str,
    shot: str,
    movement: str,
    composition: str,
) -> tuple[str, str]:
    details: List[str] = []
    if isinstance(scene_payload, dict):
        location = scene_payload.get("location") or scene_payload.get("place")
        time_info = scene_payload.get("time") or scene_payload.get("period")
        characters = scene_payload.get("characters") or scene_payload.get("cast")
        notes = scene_payload.get("notes")
        if location:
            details.append(f"地点:{_trim_local(location, 50)}")
        if time_info:
            details.append(f"时间:{_trim_local(time_info, 40)}")
        if characters:
            if isinstance(characters, list):
                details.append(
                    f"角色:{_trim_local(', '.join(map(str, characters)), 80)}"
                )
            else:
                details.append(f"角色:{_trim_local(characters, 80)}")
        if notes:
            details.append(f"备注:{_trim_local(notes, 80)}")
    dialogues = _collect_dialogues_for_scene(script_obj, scene_number)
    if dialogues:
        details.append("对白:" + " / ".join(dialogues))
    stage = _collect_stage_for_scene(script_obj, scene_number)
    if stage:
        details.append("舞台:" + " / ".join(stage))
    details.append("内容:" + _trim_local(base_text, 140))

    description = "；".join(details)[:200] if details else _trim_local(base_text, 200)
    return description, description


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
    )

    # 提取剧本内容
    script_content = ai_content.get("content", "")
    scenes = ai_content.get("scenes", [])
    dialogues_raw = ai_content.get("dialogues", [])
    stage_directions_raw = ai_content.get("stage_directions", [])
    dialogues, stage_directions = _populate_dialogues_and_stage_if_missing(
        scenes, dialogues_raw, stage_directions_raw, story=story
    )

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
        )

        script_content = ai_content.get("content", "")
        scenes = ai_content.get("scenes", [])
        dialogues_raw = ai_content.get("dialogues", [])
        stage_directions_raw = ai_content.get("stage_directions", [])
        dialogues, stage_directions = _populate_dialogues_and_stage_if_missing(
            scenes, dialogues_raw, stage_directions_raw, story=story
        )
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
        )

        script_content = ai_content.get("content", "")
        scenes = ai_content.get("scenes", [])
        dialogues_raw = ai_content.get("dialogues", [])
        stage_directions_raw = ai_content.get("stage_directions", [])
        dialogues, stage_directions = _populate_dialogues_and_stage_if_missing(
            scenes, dialogues_raw, stage_directions_raw, story=story
        )

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
            db.commit()
    finally:
        db.close()


class ScriptAudioStoryboardGenerateRequest(BaseModel):
    overwrite_existing: bool = Field(
        False, description="是否覆盖已有分镜结构（若已有图像/视频资产默认拒绝覆盖）"
    )
    min_pause_seconds: float = Field(
        1.5,
        ge=0.0,
        le=10.0,
        description="pause beat 生成帧的阈值（秒，默认 1.5s）",
    )


@router.post("/{script_id}/storyboard/from-audio-timeline/generate-async")
async def generate_storyboard_from_audio_timeline_async(
    script_id: int,
    body: ScriptAudioStoryboardGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步从 episode audio_timeline 生成分镜帧占位（写入 scripts.extra_metadata.storyboard）。"""
    script_query = (
        _not_deleted(db.query(Script), Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Script.id == script_id)
    )
    if not (current_user.is_admin or current_user.is_superuser):
        script_query = script_query.filter(Story.user_id == current_user.id)
    script = script_query.first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    story = script.episode.story if script.episode else None
    episode = script.episode if script.episode else None

    params = body.model_dump()
    params["script_id"] = script_id
    t = Task(
        title=_friendly_task_title("分镜占位生成", script, episode, story),
        description="根据对白时间轴生成分镜帧占位（audio_timeline）",
        task_type=TaskType.STORYBOARD_GENERATION,
        prompt=f"Storyboard placeholder generation from audio timeline for script {script_id}",
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    script_audio_storyboard_generate_task.delay(t.id, params, current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


def _process_script_audio_storyboard_task(
    task_id: int, payload: dict, user_id: int
) -> None:
    """后台处理从 audio_timeline 生成分镜帧占位任务（供 Celery 调用）。"""
    import anyio
    from app.core.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = int(payload.get("script_id"))
        overwrite_existing = bool(payload.get("overwrite_existing"))
        min_pause_seconds = float(payload.get("min_pause_seconds") or 1.5)
        min_pause_ms = max(0, int(round(min_pause_seconds * 1000)))

        async def _run() -> None:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise RuntimeError("user_not_found")

            script = (
                db.query(Script)
                .join(Episode, Script.episode_id == Episode.id)
                .join(Story, Episode.story_id == Story.id)
                .filter(Script.id == script_id)
                .filter(
                    True
                    if user.is_admin or user.is_superuser
                    else Story.user_id == user.id
                )
                .first()
            )
            if not script:
                raise RuntimeError("script_not_found")
            episode = script.episode
            if not episode:
                raise RuntimeError("episode_not_found")

            _update_task_progress(db, task, "根据时间轴生成分镜帧占位中…")
            generate_storyboard_from_episode_audio_timeline(
                db,
                script=script,
                episode=episode,
                overwrite_existing=overwrite_existing,
                min_pause_duration_ms=min_pause_ms,
            )

        anyio.run(_run)

        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{script_id}:storyboard_from_audio_timeline"
            _update_task_progress(db, task, "分镜帧占位生成完成")
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            _update_task_progress(db, task, f"分镜帧占位生成失败：{e}")
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


# 分镜（Storyboard）相关
@router.get("/{script_id}/storyboard")
async def get_storyboard(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.core.logging import get_logger

    logger = get_logger()
    script_query = (
        _not_deleted(db.query(Script), Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Script.id == script_id)
    )
    if not (current_user.is_admin or current_user.is_superuser):
        script_query = script_query.filter(Story.user_id == current_user.id)
    script = script_query.first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    storyboard = (
        (script.extra_metadata or {}).get("storyboard")
        if script.extra_metadata
        else None
    )
    try:
        frames = (storyboard or {}).get("frames") or []
        first_url = None
        if isinstance(frames, list) and frames:
            first = frames[0] or {}
            if isinstance(first, dict):
                first_url = first.get("image_url")
        logger.info(
            f"Storyboard GET | script_id={script_id} frames={len(frames)} first_image={bool(first_url)}"
        )
    except Exception:
        pass
    data = dict(storyboard or {"frames": []})
    meta = dict(data.get("meta") or {})
    if script.storyboard_version is not None:
        meta.setdefault("version", script.storyboard_version)
    if script.storyboard_updated_at:
        meta.setdefault("updated_at", script.storyboard_updated_at.isoformat())
    data["meta"] = meta
    if script.storyboard_plan:
        data["plan"] = script.storyboard_plan
    return {"success": True, "data": data}


@router.post("/{script_id}/storyboard/preview")
async def preview_storyboard_prompt(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    episode = script.episode
    story = episode.story if episode else None
    story_marketing = merge_marketing_meta(
        (
            story.extra_metadata
            if story and isinstance(story.extra_metadata, dict)
            else {}
        ),
        (
            story.generation_params
            if story and isinstance(story.generation_params, dict)
            else {}
        ),
    )
    episode_marketing = merge_marketing_meta(
        (
            episode.extra_metadata
            if episode and isinstance(episode.extra_metadata, dict)
            else {}
        ),
        (
            episode.generation_params
            if episode and isinstance(episode.generation_params, dict)
            else {}
        ),
    )
    scenes = script.scenes or []
    scene_indices = list(range(1, len(scenes) + 1))
    script_data = {
        "content": script.content,
        "scenes": scenes,
        "dialogues": script.dialogues,
        "stage_directions": script.stage_directions,
        "scene_indices": scene_indices,
        "episode": (
            {
                "episode_number": episode.episode_number if episode else None,
                "title": episode.title if episode else None,
                "summary": episode.summary if episode else None,
                "duration_minutes": episode.duration_minutes if episode else None,
                "scene_count": episode.scene_count if episode else None,
                **episode_marketing,
            }
            if episode
            else None
        ),
        "story": (
            {
                "title": story.title if story else None,
                "genre": story.genre if story else None,
                "theme": story.theme if story else None,
                "setting_time": story.setting_time if story else None,
                "setting_location": story.setting_location if story else None,
                "world_building": story.world_building if story else None,
                "main_characters": story.main_characters if story else None,
                **story_marketing,
            }
            if story
            else None
        ),
    }
    context_text = build_storyboard_context(script_data)
    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_GENERATION.value,
        {
            "frames_per_scene": 7,
            "max_frames": None,
            "context_text": context_text,
            "style_preferences": [],
            "additional_requirements": None,
        },
    )
    return {"success": True, "data": {"prompt": prompt}}


@router.post("/{script_id}/storyboard/generate")
async def generate_storyboard(
    script_id: int,
    model: str | None = None,
    temperature: float = Query(0.7, ge=0.0, le=1.5, description="创造性温度"),
    frames_per_scene: int = Query(7, ge=1, le=10, description="每场景建议分镜数"),
    max_frames: int | None = Query(None, ge=1, le=500, description="最大分镜帧数上限"),
    scene_numbers: str | None = Query(
        None, description="逗号分隔的场景编号列表，如 1,3,4"
    ),
    use_plan: bool = Query(True, description="是否先使用分镜规划，再逐场景生成"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    logger = get_logger()
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    # 解析选择的场景
    selected_scenes: list[int] | None = None
    if scene_numbers:
        try:
            selected_scenes = [
                int(x.strip()) for x in scene_numbers.split(",") if x.strip()
            ]
        except Exception:
            raise HTTPException(status_code=400, detail="scene_numbers 格式不正确")

    # 以剧本结构为输入（可按选择的场景过滤），并补充故事/剧集上下文
    all_scenes = script.scenes or []
    scenes_filtered: List[Dict[str, Any]] = []
    scene_order: List[int] = []
    if selected_scenes:
        selected_set = {s for s in selected_scenes}
        for idx, sc in enumerate(all_scenes, start=1):
            if idx in selected_set:
                scenes_filtered.append(sc)
                scene_order.append(idx)
    else:
        scenes_filtered = all_scenes
        scene_order = list(range(1, len(all_scenes) + 1))

    # 获取剧集与故事元信息
    episode = db.query(Episode).filter(Episode.id == script.episode_id).first()
    story = (
        db.query(Story).filter(Story.id == episode.story_id).first()
        if episode
        else None
    )

    story_marketing = merge_marketing_meta(
        story.extra_metadata if isinstance(story.extra_metadata, dict) else {},
        story.generation_params if isinstance(story.generation_params, dict) else {},
    )
    episode_marketing = merge_marketing_meta(
        episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {},
        (
            episode.generation_params
            if isinstance(episode.generation_params, dict)
            else {}
        ),
    )
    script_data = {
        "content": script.content,
        "scenes": scenes_filtered,
        "dialogues": script.dialogues,
        "stage_directions": script.stage_directions,
        "scene_indices": scene_order,
        "episode": (
            {
                "episode_number": episode.episode_number if episode else None,
                "title": episode.title if episode else None,
                "summary": episode.summary if episode else None,
                "duration_minutes": episode.duration_minutes if episode else None,
                "scene_count": episode.scene_count if episode else None,
                **episode_marketing,
            }
            if episode
            else None
        ),
        "story": (
            {
                "title": story.title if story else None,
                "genre": story.genre if story else None,
                "theme": story.theme if story else None,
                "setting_time": story.setting_time if story else None,
                "setting_location": story.setting_location if story else None,
                "world_building": story.world_building if story else None,
                "main_characters": story.main_characters if story else None,
                **story_marketing,
            }
            if story
            else None
        ),
    }
    # 默认优先使用 OpenAI（其支持 json_schema 更可靠）
    prefer_provider = "openai"
    model_id = model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    # 记录请求参数
    try:
        logger.info(
            f"StoryboardGen Request | script_id={script_id} model={model or 'auto'} prefer_provider={prefer_provider or 'openai'} temp={temperature} fps={frames_per_scene} max_frames={max_frames} scenes={selected_scenes or 'all'}"
        )
    except Exception:
        pass

    scene_map = {idx: sc for idx, sc in enumerate(all_scenes, start=1)}
    existing_frames = _load_existing_frames(script)

    frames_generated: List[Dict[str, Any]] = []
    generation_method = "direct"
    generation_source = f"ai:{prefer_provider or 'auto'}"
    generation_model = model_id
    provider_used: Optional[str] = prefer_provider
    reasoning_trace: Optional[List[str]] = None
    agent_usage: Optional[Dict[str, Any]] = None
    plan_data: Optional[Dict[str, Any]] = None
    plan_fixes: Optional[List[str]] = None

    result = await ai_service.generate_storyboard(
        script=script_data,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=temperature,
        frames_per_scene=frames_per_scene,
        max_frames=max_frames,
        selected_scenes=selected_scenes,
        prefer_graph=use_plan,
    )
    if result:
        try:
            raw_text = result.get("content") if isinstance(result, dict) else None
            if isinstance(raw_text, str):
                logger.info(
                    f"StoryboardGen Raw Response Preview (len={len(raw_text)}): {raw_text[:2000]}"
                    f"{'...<truncated>' if len(raw_text) > 2000 else ''}"
                )
            logger.info(
                f"StoryboardGen Provider: {result.get('provider_used')} Model: {result.get('model_used')} Usage: {result.get('usage')}"
            )
        except Exception:
            pass
        sb_raw = result.get("normalized")
        if not isinstance(sb_raw, dict):
            try:
                sb_raw = result.get("content")
                if not isinstance(sb_raw, dict):
                    sb_raw = extract_json_block(sb_raw)
            except Exception as exc:
                logger.warning(f"StoryboardGen JSON parse failed: {exc}")
                sb_raw = None
        if isinstance(sb_raw, dict):
            try:
                sb_obj = StoryboardModel.model_validate(sb_raw)
                sb_data = sb_obj.model_dump(mode="python")
                frames_generated = sb_data.get("frames") or []
                provider_used = result.get("provider_used") or prefer_provider
                generation_model = result.get("model_used") or model_id
                generation_method = result.get("generation_method") or generation_method
                if generation_method.startswith("langgraph"):
                    generation_source = f"langgraph:{provider_used or 'auto'}"
                else:
                    generation_source = f"ai:{provider_used or 'auto'}"
                reasoning_trace = result.get("reasoning_trace")
                agent_usage = result.get("usage")
                plan_data = result.get("plan")
                plan_fixes = result.get("fixes")
            except Exception as exc:
                logger.warning(f"StoryboardGen validation failed: {exc}")

    if plan_data:
        try:
            script.storyboard_plan = plan_data
            extra_meta = dict(script.extra_metadata or {})
            extra_meta["storyboard_plan"] = plan_data
            script.extra_metadata = extra_meta
        except Exception:
            logger.warning("Storyboard plan persistence failed")

    # Fallback: 基于剧本快速生成简易分镜
    if not frames_generated:
        generation_method = "fallback"
        generation_source = "fallback"
        generation_model = None
        provider_used = "fallback"
        frames_fallback: List[Dict[str, Any]] = []
        shot_cycle = ["远景", "中景", "近景", "特写"]
        movement_cycle = ["固定", "推", "拉", "摇", "移", "跟", "变焦"]
        composition_cycle = ["三分法", "对称", "前后景", "对角线", "中心对称"]
        scenes = scenes_filtered
        frame_no = 1
        if scenes:
            for sidx, sc in enumerate(scenes, start=1):
                real_scene_number = (
                    scene_order[sidx - 1] if (sidx - 1) < len(scene_order) else sidx
                )
                if max_frames and len(frames_fallback) >= max_frames:
                    break
                desc = (
                    sc.get("description")
                    if isinstance(sc, dict)
                    else (str(sc) if sc else "")
                )
                segments = [
                    seg for seg in re.split(r"[。.!?！？]", desc or "") if seg.strip()
                ]
                count = max(1, frames_per_scene)
                for i in range(count):
                    if max_frames and len(frames_fallback) >= max_frames:
                        break
                    text = (
                        segments[i] if i < len(segments) else (desc or f"场景 {sidx}")
                    )
                    variant = frame_no - 1
                    shot = shot_cycle[variant % len(shot_cycle)]
                    movement = movement_cycle[variant % len(movement_cycle)]
                    composition = composition_cycle[variant % len(composition_cycle)]
                    description, ai_prompt = _compose_fallback_text(
                        sc if isinstance(sc, dict) else None,
                        real_scene_number,
                        script_obj=script,
                        base_text=text,
                        shot=shot,
                        movement=movement,
                        composition=composition,
                    )
                    duration = max(2, min(12, 3 + (variant % 3) - 1))
                    frames_fallback.append(
                        {
                            "frame_number": frame_no,
                            "scene_number": real_scene_number,
                            "shot_type": shot,
                            "camera_movement": movement,
                            "composition": composition,
                            "description": description,
                            "duration_seconds": duration,
                            "ai_prompt": ai_prompt,
                            "reference_images": [],
                        }
                    )
                    frame_no += 1
        else:
            paragraphs = (script.content or "").split("\n\n")
            for para in paragraphs:
                if max_frames and len(frames_fallback) >= max_frames:
                    break
                text = para.strip().replace("\n", " ")[:200]
                if not text:
                    continue
                variant = frame_no - 1
                shot = shot_cycle[variant % len(shot_cycle)]
                movement = movement_cycle[variant % len(movement_cycle)]
                composition = composition_cycle[variant % len(composition_cycle)]
                description, ai_prompt = _compose_fallback_text(
                    None,
                    None,
                    script_obj=script,
                    base_text=text,
                    shot=shot,
                    movement=movement,
                    composition=composition,
                )
                duration = max(2, min(12, 3 + (variant % 3) - 1))
                frames_fallback.append(
                    {
                        "frame_number": frame_no,
                        "scene_number": None,
                        "shot_type": shot,
                        "camera_movement": movement,
                        "composition": composition,
                        "description": description,
                        "duration_seconds": duration,
                        "ai_prompt": ai_prompt,
                        "reference_images": [],
                    }
                )
                frame_no += 1
        frames_generated = frames_fallback

    if not frames_generated:
        raise HTTPException(status_code=500, detail="分镜生成失败")

    frames_augmented = _augment_frames(
        frames_generated,
        scene_map=scene_map,
        generation_source=generation_source,
        generation_method=generation_method,
        generation_model=generation_model,
    )

    frames_list = list(frames_augmented)

    if selected_scenes:
        selected_set = {s for s in scene_order if s is not None}
        frames_list = [
            fr for fr in frames_list if _to_int(fr.get("scene_number")) in selected_set
        ]
        try:
            logger.info(
                f"StoryboardGen Frames after scene filter {selected_scenes}: {len(frames_list)}"
            )
        except Exception:
            pass

    if max_frames:
        frames_list = frames_list[:max_frames]
        try:
            logger.info(
                f"StoryboardGen Frames after max_frames({max_frames}) slice: {len(frames_list)}"
            )
        except Exception:
            pass

    # 若有帧，但每个场景的帧数少于 frames_per_scene，则补齐
    try:
        supplementary_raw: List[Dict[str, Any]] = []
        if scene_order:
            target_scenes = scene_order
        else:
            target_scenes = list(range(1, (len(all_scenes) or 0) + 1))
        for s in target_scenes:
            if s is None:
                continue
            existing_count = len(
                [fr for fr in frames_list if _to_int(fr.get("scene_number")) == s]
            )
            deficit = max(0, frames_per_scene - existing_count)
            if deficit <= 0:
                continue
            src = all_scenes[s - 1] if 0 <= (s - 1) < len(all_scenes) else None
            desc = (
                src.get("description")
                if isinstance(src, dict)
                else (str(src) if src else "")
            )
            segs = [seg for seg in re.split(r"[。.!?！？]", desc or "") if seg.strip()]
            for i in range(deficit):
                text = segs[i] if i < len(segs) else (desc or f"场景 {s}")
                supplementary_raw.append(
                    {
                        "scene_number": s,
                        "description": (text or "").strip()[:200],
                        "shot_type": "中景",
                        "camera_movement": "固定",
                        "composition": "三分法",
                        "duration_seconds": 3,
                        "ai_prompt": (text or "").strip()[:200],
                        "reference_images": [],
                    }
                )
        if supplementary_raw:
            supplementary = _augment_frames(
                supplementary_raw,
                scene_map=scene_map,
                generation_source="supplement",
                generation_method="fallback",
                generation_model=generation_model,
            )
            frames_list.extend(supplementary)
        try:
            stats: Dict[Any, int] = {}
            for fr in frames_list:
                sn = _to_int(fr.get("scene_number"))
                stats[sn] = stats.get(sn, 0) + 1
            logger.info(f"StoryboardGen Frames after supplement (per scene): {stats}")
        except Exception:
            pass
    except Exception:
        pass

    # 规范化字段，填充缺省，并增强 ai_prompt
    try:
        allowed_shots = {"远景", "中景", "近景", "特写"}
        shot_map = {
            "wide": "远景",
            "long": "远景",
            "establishing": "远景",
            "ws": "远景",
            "medium": "中景",
            "ms": "中景",
            "close": "近景",
            "cs": "近景",
            "close-up": "特写",
            "cu": "特写",
            "extreme close-up": "特写",
            "ecu": "特写",
        }
        for fr in frames_list:
            shot = (fr.get("shot_type") or "").strip()
            shot_norm = shot_map.get(shot.lower()) if isinstance(shot, str) else None
            if shot_norm:
                fr["shot_type"] = shot_norm
            elif shot in allowed_shots:
                fr["shot_type"] = shot
            else:
                fr["shot_type"] = "中景"
            fr["camera_movement"] = fr.get("camera_movement") or "固定"
            fr["composition"] = fr.get("composition") or "三分法"
            fr["duration_seconds"] = fr.get("duration_seconds") or 3
            scene_no = _to_int(fr.get("scene_number"))
            chars: List[str] = []
            if scene_no and 0 < scene_no <= len(all_scenes):
                sc = all_scenes[scene_no - 1]
                if isinstance(sc, dict) and sc.get("characters"):
                    try:
                        chars = list(sc.get("characters") or [])
                    except Exception:
                        chars = []
            if not chars and story and story.main_characters:
                try:
                    chars = [
                        c.get("name")
                        for c in (story.main_characters or [])
                        if isinstance(c, dict) and c.get("name")
                    ]
                except Exception:
                    pass
            if chars:
                fr["characters"] = chars[:5]
    except Exception:
        pass

    merge_targets = scene_order if selected_scenes else None
    merged_frames = _merge_frames(existing_frames, frames_list, merge_targets)
    diversified_frames = _enforce_storyboard_variety(merged_frames)
    apply_storyboard_prompt_optimizations(diversified_frames)

    frames_serialized = [_serialize_frame(fr) for fr in diversified_frames]
    try:
        StoryboardModel.model_validate({"frames": frames_serialized})
    except Exception as exc:
        logger.error(f"Storyboard validation failed before save: {exc}")
        raise HTTPException(status_code=500, detail="分镜结构不合法")

    sb_meta = {
        "version": script.storyboard_version,
        "updated_at": (
            script.storyboard_updated_at.isoformat()
            if script.storyboard_updated_at
            else None
        ),
        "generation_source": generation_source,
        "generation_method": generation_method,
        "generation_model": generation_model,
        "provider": provider_used,
        "scene_scope": scene_order if selected_scenes else None,
    }
    if reasoning_trace:
        sb_meta["reasoning_trace"] = reasoning_trace
    if agent_usage:
        sb_meta["usage"] = agent_usage
    if plan_fixes:
        sb_meta["plan_fixes"] = plan_fixes
    sb = {"frames": frames_serialized, "meta": sb_meta}
    plan_payload = plan_data or script.storyboard_plan
    if plan_payload:
        sb["plan"] = plan_payload
    extra = dict(script.extra_metadata or {})
    extra["storyboard"] = sb
    script.extra_metadata = extra
    script.storyboard_updated_at = datetime.utcnow()
    script.storyboard_version = (script.storyboard_version or 0) + 1

    db.commit()
    db.refresh(script)

    return {"success": True, "data": sb}


@router.post("/{script_id}/storyboard/generate-async")
async def generate_storyboard_async(
    script_id: int,
    model: str | None = None,
    temperature: float = Query(0.7, ge=0.0, le=1.5, description="创造性温度"),
    frames_per_scene: int = Query(7, ge=1, le=10, description="每场景建议分镜数"),
    max_frames: int | None = Query(None, ge=1, le=500, description="最大分镜帧数上限"),
    scene_numbers: str | None = Query(
        None, description="逗号分隔的场景编号列表，如 1,3,4"
    ),
    use_plan: bool = Query(True, description="是否先使用分镜规划，再逐场景生成"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步生成分镜结构：创建任务并交给 Celery 处理。"""
    from app.models.task import Task

    # 校验剧本归属，与 generate_storyboard_images 对齐
    script_query = (
        _not_deleted(db.query(Script), Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Script.id == script_id)
    )
    if not (current_user.is_admin or current_user.is_superuser):
        script_query = script_query.filter(Story.user_id == current_user.id)
    script = script_query.first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    params = {
        "script_id": script_id,
        "model": model,
        "temperature": temperature,
        "frames_per_scene": frames_per_scene,
        "max_frames": max_frames,
        "scene_numbers": scene_numbers,
        "use_plan": use_plan,
    }
    story = script.episode.story if script.episode else None
    t = Task(
        title=_friendly_task_title("分镜生成", script, script.episode, story),
        description="生成分镜结构（帧列表）",
        task_type=TaskType.STORYBOARD_GENERATION,
        prompt=f"Storyboard generation for script {script_id}",
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    storyboard_generate_task.delay(t.id, params, current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


def _process_storyboard_generation_task(
    task_id: int,
    payload: dict,
    user_id: int,
):
    """后台处理分镜结构生成任务（供 Celery 调用）。"""
    import anyio
    from app.core.database import SessionLocal
    from app.models.task import Task, TaskStatus
    from app.models.user import User

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = int(payload.get("script_id"))

        async def _run():
            user = db.query(User).filter(User.id == user_id).first()
            model = payload.get("model")
            temperature = float(payload.get("temperature") or 0.7)
            frames_per_scene = int(payload.get("frames_per_scene") or 7)
            max_frames = payload.get("max_frames")
            max_frames_arg = int(max_frames) if max_frames is not None else None
            scene_numbers = payload.get("scene_numbers")
            use_plan = bool(payload.get("use_plan"))
            # 直接复用同步路由的生成逻辑，确保行为一致
            await generate_storyboard(
                script_id=script_id,
                model=model,
                temperature=temperature,
                frames_per_scene=frames_per_scene,
                max_frames=max_frames_arg,
                scene_numbers=scene_numbers,
                use_plan=use_plan,
                current_user=user,  # type: ignore[arg-type]
                db=db,  # type: ignore[arg-type]
            )

        anyio.run(_run)

        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{script_id}:storyboard"
            db.commit()
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()


class StoryboardUpdateRequest(BaseModel):
    frames: list[dict]


@router.post("/{script_id}/storyboard/update")
async def update_storyboard(
    script_id: int,
    body: StoryboardUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """保存分镜编辑后的结果（整量更新）"""
    script = db.query(Script).filter(Script.id == script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")
    # 校验结构
    try:
        validated = StoryboardModel.model_validate({"frames": body.frames})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"分镜结构不合法: {e}")
    frames_python = validated.model_dump(mode="python").get("frames", [])
    now_iso = _now_iso()
    for idx, fr in enumerate(frames_python, start=1):
        fr["frame_id"] = _coerce_uuid(fr.get("frame_id"))
        fr["frame_number"] = idx
        scene_number = _to_int(fr.get("scene_number"))
        if scene_number is not None:
            fr["scene_number"] = scene_number
            fr.setdefault("scene_index", scene_number)
        fr["generated_at"] = _ensure_iso_datetime(fr.get("generated_at"), now_iso)
        fr["updated_at"] = now_iso
    frames_serialized = [_serialize_frame(fr) for fr in frames_python]
    extra = dict(script.extra_metadata or {})
    updated_at_dt = datetime.utcnow()
    script.storyboard_updated_at = updated_at_dt
    script.storyboard_version = (script.storyboard_version or 0) + 1
    existing_meta = {}
    if isinstance(extra.get("storyboard"), dict):
        existing_meta = dict(extra["storyboard"].get("meta") or {})
    existing_meta.update(
        {
            "version": script.storyboard_version,
            "updated_at": updated_at_dt.isoformat(),
            "generation_source": existing_meta.get("generation_source") or "manual",
            "generation_method": "manual_edit",
        }
    )
    extra["storyboard"] = {"frames": frames_serialized, "meta": existing_meta}
    script.extra_metadata = extra
    db.commit()
    db.refresh(script)
    return {"success": True}


def _build_reference_image_context(
    labeled_references: list[dict[str, Any]] | None,
) -> str:
    """从带标签的参考图构建上下文说明，让AI知道每张图代表什么。

    返回格式示例：
    [参考图说明]
    - 第1张图是角色"老拐"的参考形象
    - 第2张图是场景环境参考
    """
    if not labeled_references:
        return ""

    lines = []
    for i, ref in enumerate(labeled_references, 1):
        ref_type = ref.get("type", "other")
        label = ref.get("label")

        if ref_type == "character" and label:
            lines.append(f"- 第{i}张图是角色「{label}」的参考形象")
        elif ref_type == "environment":
            lines.append(f"- 第{i}张图是场景环境参考")
        elif ref_type == "primary":
            lines.append(f"- 第{i}张图是首要参考图（用于风格/构图参考）")
        else:
            lines.append(f"- 第{i}张图是补充参考")

    if not lines:
        return ""

    return "[参考图说明]\n" + "\n".join(lines)


def _process_storyboard_image_task(
    task_id: int,
    script_id: int,
    frame_indexes: list[int] | None,
    *,
    prompt_override: str | None = None,
    model: str | None = None,
    generation_profile: str | None = None,
    size: str | None = None,
    width: int | None = None,
    height: int | None = None,
    style: str = "realistic",
    style_preset_id: str | None = None,
    style_spec: dict[str, Any] | None = None,
    aspect_ratio: str | None = None,
    seed: int | None = None,
    steps: int | None = None,
    cfg_scale: float | None = None,
    negative_prompt: str | None = None,
    strength: float | None = None,
    reference_images: Optional[List[str]] = None,
    labeled_references: Optional[List[dict[str, Any]]] = None,
    count: int = 1,
    keyframe_mode: str = "single",
    start_enabled: bool = True,
    end_enabled: bool = True,
):
    from app.core.database import SessionLocal
    from app.models.task import Task, TaskStatus

    logger = get_logger("storyboard_image_task")
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise RuntimeError("剧本不存在")
        sb = (
            (script.extra_metadata or {}).get("storyboard")
            if script.extra_metadata
            else None
        )
        if not sb or not sb.get("frames"):
            raise RuntimeError("未找到分镜数据")

        # 拷贝一份帧列表，避免直接在 SQLAlchemy 追踪的 JSON 结构上就地修改
        import copy as _copy  # 局部导入避免循环依赖

        frames_src = list((sb or {}).get("frames") or [])
        frames: List[Dict[str, Any]] = [
            _copy.deepcopy(fr) if isinstance(fr, dict) else fr for fr in frames_src
        ]
        target_indexes = frame_indexes or list(range(len(frames)))
        start_log = (
            f"[SBIMG] task start | script_id={script_id} task_id={task_id} "
            f"frames_total={len(frames)} target_indexes={target_indexes} model={model} count={count} "
            f"keyframe_mode={keyframe_mode} start_enabled={start_enabled} end_enabled={end_enabled}"
        )
        logger.info(start_log)
        print(start_log, flush=True)

        # 准备环境 / 角色参考图
        scenes = db.query(Scene).filter(Scene.script_id == script_id).all()
        scene_by_number: Dict[int, Scene] = {}
        env_ids: set[int] = set()
        scene_ids: list[int] = []
        for sc in scenes:
            try:
                sn = int(sc.scene_number)
                scene_by_number[sn] = sc
            except Exception:
                continue
            scene_ids.append(sc.id)
            if sc.environment_id:
                env_ids.add(sc.environment_id)

        env_map: Dict[int, Environment] = {}
        env_images_by_scene: Dict[int, List[str]] = {}
        if env_ids:
            envs = db.query(Environment).filter(Environment.id.in_(env_ids)).all()
            env_map = {env.id: env for env in envs}
            for sc in scenes:
                if sc.environment_id and sc.environment_id in env_map:
                    refs = env_map[sc.environment_id].reference_images or []
                    env_images_by_scene[int(sc.scene_number)] = [
                        _abs_url(u) for u in refs if u
                    ]

        scene_char_ids: Dict[int, set[int]] = defaultdict(set)
        if scene_ids:
            shots = db.query(Shot).filter(Shot.scene_id.in_(scene_ids)).all()
            for shot in shots:
                for cid in shot.character_ids or []:
                    try:
                        scene_char_ids[shot.scene_id].add(int(cid))
                    except Exception:
                        continue

        all_char_ids = {cid for ids in scene_char_ids.values() for cid in ids}
        vip_map: Dict[int, VirtualIP] = {}
        char_image_map: Dict[int, str] = {}
        if all_char_ids:
            vips = db.query(VirtualIP).filter(VirtualIP.id.in_(all_char_ids)).all()
            vip_map = {v.id: v for v in vips}
            images = (
                db.query(VirtualIPImage)
                .filter(VirtualIPImage.virtual_ip_id.in_(all_char_ids))
                .order_by(
                    VirtualIPImage.is_default.desc(), VirtualIPImage.created_at.desc()
                )
                .all()
            )
            for img in images:
                if img.virtual_ip_id in char_image_map:
                    continue
                url = img.oss_url or img.file_path
                if url:
                    char_image_map[img.virtual_ip_id] = _abs_url(url)

        from functools import partial as _partial

        import anyio

        try:
            count_int = int(count) if count is not None else 1
        except (TypeError, ValueError):
            count_int = 1
        count_int = max(1, min(count_int, 4))

        width_value = width
        height_value = height
        if (
            (width_value is None or height_value is None)
            and isinstance(size, str)
            and size.strip()
        ):
            from app.services.providers.image_param_utils import size_to_dimensions

            dims = size_to_dimensions(size)
            if dims:
                width_value, height_value = dims
        if width_value is None:
            width_value = 1024
        if height_value is None:
            height_value = 1024

        async def _gen_images(prompt: str, ref_imgs: List[str]) -> dict | None:
            try:
                from app.services.storyboard.storyboard_image_generation import (
                    generate_storyboard_image_urls,
                )

                refs = [_abs_url(u) for u in ref_imgs if u]
                return await generate_storyboard_image_urls(
                    prompt=prompt,
                    refs=refs,
                    model=model,
                    generation_profile=generation_profile,
                    count=count_int,
                    size=size,
                    aspect_ratio=aspect_ratio,
                    width=width_value,
                    height=height_value,
                    style=style,
                    style_preset_id=style_preset_id,
                    style_spec=style_spec,
                    seed=seed,
                    steps=steps,
                    cfg_scale=cfg_scale,
                    negative_prompt=negative_prompt,
                    strength=strength,
                    ai_service=ai_service,
                )
            except Exception as e:
                print(f"图像生成失败: {e}")
            return None

        async def _persist_frame_image(
            url: str,
            idx: int,
            provider: str,
            model: str,
            *,
            keyframe_role: str = "single",
            variant_index: int | None = None,
        ) -> dict | None:
            """将分镜图像下载到本地并上传 OSS，返回最终可用 URL。"""
            try:
                metadata = {
                    "script_id": script_id,
                    "frame_index": idx,
                    "provider": provider,
                    "model": model,
                    "keyframe_role": keyframe_role,
                }
                if variant_index is not None:
                    metadata["variant_index"] = variant_index
                stored = await ai_service._persist_generated_image(
                    image_data=url,
                    ip_name=f"script-{script_id}",
                    category="storyboard",
                    prefix="ai-generated/storyboard",
                    metadata=metadata,
                    # 若已配置 OSS/CDN，则要求上传成功；否则退回本地存储
                    require_upload=bool(oss_service),
                )
            except Exception as e:
                print(f"分镜图像持久化失败 idx={idx}: {e}")
                return None

            final_url = stored.get("oss_url") or stored.get("relative_path")
            if not final_url:
                return None
            return {
                "final_url": final_url,
                "stored": stored,
            }

        # 逐帧生成图像URL
        resolved_style_spec_used: dict | None = None
        resolved_style_spec_resolution_used: Any | None = None
        for idx in target_indexes:
            if idx < 0 or idx >= len(frames):
                warn = (
                    f"[SBIMG] frame index out of range | idx={idx} total={len(frames)}"
                )
                logger.warning(warn)
                print(warn, flush=True)
                continue
            fr = frames[idx]
            base_prompt = fr.get("ai_prompt") or fr.get("description") or ""
            override_clean = (prompt_override or "").strip()
            if override_clean:
                base_prompt = override_clean
            if not base_prompt:
                base_prompt = prompt_manager.render_prompt(
                    PromptTemplate.STORYBOARD_IMAGE_FALLBACK.value,
                    {
                        "frame_index": idx + 1,
                        "scene_number": fr.get("scene_number"),
                    },
                )
            frame_log = (
                f"[SBIMG] generating frame | idx={idx} scene={fr.get('scene_number')} "
                f"prompt_len={len(base_prompt)}"
            )
            logger.info(frame_log)
            print(frame_log, flush=True)

            scene_no = _to_int(fr.get("scene_number"))
            reference_notes: List[Dict[str, Any]] = []

            # 1) 已存在于分镜帧上的参考图（用户手动/前序管线写入）
            frame_refs = _normalize_reference_images(fr.get("reference_images") or [])
            if frame_refs:
                reference_notes.append({"type": "frame"})

            # 2) 前端调用时附带的额外参考图（单次请求作用域）
            # 优先使用带标签的参考图（labeled_references），否则使用原始 reference_images
            if labeled_references:
                # 从带标签的参考图中提取 URL 列表
                payload_refs = _normalize_reference_images(
                    [ref.get("url") for ref in labeled_references if ref.get("url")]
                )
            else:
                payload_refs = _normalize_reference_images(reference_images or [])
            if payload_refs:
                reference_notes.append({"type": "user"})

            # 3) 角色锚点参考图（默认/最新的虚拟 IP 图像）
            char_anchor_refs: List[str] = []
            if scene_no and scene_no in scene_by_number:
                sc_obj = scene_by_number.get(scene_no)
                if sc_obj and sc_obj.id in scene_char_ids:
                    for cid in scene_char_ids[sc_obj.id]:
                        name = vip_map.get(cid).name if cid in vip_map else f"角色{cid}"
                        img_url = char_image_map.get(cid)
                        if img_url:
                            # 参考图 URL 通过 ref_images 传给 image_to_image，提示词只保留语义描述，避免在日志中泄露具体地址
                            reference_notes.append({"type": "character", "name": name})
                            char_anchor_refs.append(_abs_url(img_url))

            # 4) 场景环境参考图
            env_refs = _normalize_reference_images(
                env_images_by_scene.get(scene_no or -1, []) or []
            )
            if env_refs:
                reference_notes.append({"type": "environment"})

            # 参考图顺序：优先使用用户附带的参考图作为 base_image，
            # 然后是帧已有参考图、角色锚点和环境参考图
            ref_images_raw: List[str] = []
            if payload_refs:
                ref_images_raw.extend(payload_refs)
            else:
                ref_images_raw.extend(frame_refs)
                ref_images_raw.extend(char_anchor_refs)
                ref_images_raw.extend(env_refs)
            ref_images = _normalize_reference_images(ref_images_raw)
            refs_log = (
                f"[SBIMG] frame refs | idx={idx} total_refs={len(ref_images)} "
                f"frame_refs={len(frame_refs)} payload_refs={len(payload_refs)} "
                f"char_anchor={len(char_anchor_refs)} env_refs={len(env_refs)}"
            )
            logger.info(refs_log)
            print(refs_log, flush=True)

            prompt = prompt_manager.render_prompt(
                PromptTemplate.STORYBOARD_IMAGE_PROMPT.value,
                {
                    "base_prompt": base_prompt,
                    "reference_notes": reference_notes,
                },
            )

            # 如果前端传了带标签的参考图，添加上下文说明让AI知道每张图代表什么
            if labeled_references:
                ref_context = _build_reference_image_context(labeled_references)
                if ref_context:
                    prompt = f"{ref_context}\n\n{prompt}"
                    context_log = (
                        f"[SBIMG] added labeled ref context | idx={idx} "
                        f"labeled_refs={len(labeled_references)}"
                    )
                    logger.info(context_log)
                    print(context_log, flush=True)

            if ref_images:
                fr["reference_images"] = ref_images

            if keyframe_mode == "start_end":
                # 首尾关键帧：生成 start/end 两张，并保持 image_url 指向首帧用于兼容旧 UI
                use_precomputed = not override_clean and not reference_notes
                start_prompt = (
                    fr.get("start_keyframe_prompt")
                    if use_precomputed and fr.get("start_keyframe_prompt")
                    else render_keyframe_prompt(prompt, "start")
                )
                end_prompt = (
                    fr.get("end_keyframe_prompt")
                    if use_precomputed and fr.get("end_keyframe_prompt")
                    else render_keyframe_prompt(prompt, "end")
                )

                start_result = None
                if start_enabled:
                    start_result = anyio.run(_gen_images, start_prompt, ref_images)
                    if start_result:
                        start_image_gen = start_result.get("image_gen")
                        if isinstance(start_image_gen, dict):
                            fr["start_image_gen"] = start_image_gen
                            fr["image_gen"] = start_image_gen
                        urls_preview = start_result.get("urls") or []
                        url_preview = urls_preview[0] if urls_preview else None
                        if isinstance(url_preview, str) and len(url_preview) > 200:
                            url_preview = url_preview[:200] + "..."
                        print(
                            f"Storyboard keyframe(start) idx={idx} url={url_preview} "
                            f"provider={start_result.get('provider')}"
                        )
                        if resolved_style_spec_used is None and isinstance(
                            start_result.get("style_spec"), dict
                        ):
                            resolved_style_spec_used = start_result.get("style_spec")
                            resolved_style_spec_resolution_used = start_result.get(
                                "style_spec_resolution"
                            )
                start_final_urls: list[str] = []
                start_original_urls: list[str] = []
                if start_result:
                    for variant_index, raw_url in enumerate(
                        start_result.get("urls") or [], start=1
                    ):
                        if not raw_url:
                            continue
                        start_original_urls.append(raw_url)
                        start_persist = anyio.run(
                            _partial(
                                _persist_frame_image,
                                keyframe_role="start",
                                variant_index=variant_index,
                            ),
                            raw_url,
                            idx,
                            start_result.get("provider"),
                            start_result.get("model"),
                        )
                        if start_persist and start_persist.get("final_url"):
                            start_final_urls.append(start_persist["final_url"])

                if start_final_urls:
                    existing_start_urls = (
                        list(fr.get("start_image_urls") or [])
                        if isinstance(fr.get("start_image_urls"), list)
                        else []
                    )
                    merged_start_urls: list[str] = []
                    for url in existing_start_urls + start_final_urls:
                        if url and url not in merged_start_urls:
                            merged_start_urls.append(url)
                    fr["start_image_urls"] = merged_start_urls or start_final_urls
                    if merged_start_urls:
                        fr["start_image_url"] = (
                            fr.get("start_image_url") or merged_start_urls[0]
                        )
                        fr["image_url"] = fr.get("image_url") or merged_start_urls[0]
                    if start_original_urls and not fr.get("start_image_url_original"):
                        fr["start_image_url_original"] = start_original_urls[0]
                    if start_original_urls and not fr.get("image_url_original"):
                        fr["image_url_original"] = start_original_urls[0]

                end_result = None
                if end_enabled:
                    end_result = anyio.run(_gen_images, end_prompt, ref_images)
                    if end_result:
                        end_image_gen = end_result.get("image_gen")
                        if isinstance(end_image_gen, dict):
                            fr["end_image_gen"] = end_image_gen
                        urls_preview = end_result.get("urls") or []
                        url_preview = urls_preview[0] if urls_preview else None
                        if isinstance(url_preview, str) and len(url_preview) > 200:
                            url_preview = url_preview[:200] + "..."
                        print(
                            f"Storyboard keyframe(end) idx={idx} url={url_preview} "
                            f"provider={end_result.get('provider')}"
                        )
                        if resolved_style_spec_used is None and isinstance(
                            end_result.get("style_spec"), dict
                        ):
                            resolved_style_spec_used = end_result.get("style_spec")
                            resolved_style_spec_resolution_used = end_result.get(
                                "style_spec_resolution"
                            )
                end_final_urls: list[str] = []
                end_original_urls: list[str] = []
                if end_result:
                    for variant_index, raw_url in enumerate(
                        end_result.get("urls") or [], start=1
                    ):
                        if not raw_url:
                            continue
                        end_original_urls.append(raw_url)
                        end_persist = anyio.run(
                            _partial(
                                _persist_frame_image,
                                keyframe_role="end",
                                variant_index=variant_index,
                            ),
                            raw_url,
                            idx,
                            end_result.get("provider"),
                            end_result.get("model"),
                        )
                        if end_persist and end_persist.get("final_url"):
                            end_final_urls.append(end_persist["final_url"])

                if end_final_urls:
                    existing_end_urls = (
                        list(fr.get("end_image_urls") or [])
                        if isinstance(fr.get("end_image_urls"), list)
                        else []
                    )
                    merged_end_urls: list[str] = []
                    for url in existing_end_urls + end_final_urls:
                        if url and url not in merged_end_urls:
                            merged_end_urls.append(url)
                    fr["end_image_urls"] = merged_end_urls or end_final_urls
                    if merged_end_urls and not fr.get("end_image_url"):
                        fr["end_image_url"] = merged_end_urls[0]
                    if end_original_urls and not fr.get("end_image_url_original"):
                        fr["end_image_url_original"] = end_original_urls[0]
            else:
                result = anyio.run(_gen_images, prompt, ref_images)
                if result:
                    image_gen = result.get("image_gen")
                    if isinstance(image_gen, dict):
                        fr["image_gen"] = image_gen
                    urls_preview = result.get("urls") or []
                    url_preview = urls_preview[0] if urls_preview else None
                    if isinstance(url_preview, str) and len(url_preview) > 200:
                        url_preview = url_preview[:200] + "..."
                    print(
                        f"Storyboard image result idx={idx} url={url_preview} "
                        f"provider={result.get('provider')}"
                    )
                    if resolved_style_spec_used is None and isinstance(
                        result.get("style_spec"), dict
                    ):
                        resolved_style_spec_used = result.get("style_spec")
                        resolved_style_spec_resolution_used = result.get(
                            "style_spec_resolution"
                        )
                final_urls: list[str] = []
                original_urls: list[str] = []
                if result:
                    for variant_index, raw_url in enumerate(
                        result.get("urls") or [], start=1
                    ):
                        if not raw_url:
                            continue
                        original_urls.append(raw_url)
                        persist = anyio.run(
                            _partial(
                                _persist_frame_image,
                                keyframe_role="single",
                                variant_index=variant_index,
                            ),
                            raw_url,
                            idx,
                            result.get("provider"),
                            result.get("model"),
                        )
                        if persist and persist.get("final_url"):
                            final_urls.append(persist["final_url"])

                if final_urls:
                    before_url = fr.get("image_url")
                    fr["image_url"] = final_urls[0]
                    fr["start_image_url"] = final_urls[0]
                    fr["start_image_urls"] = final_urls
                    if original_urls:
                        fr["image_url_original"] = original_urls[0]
                        fr["start_image_url_original"] = original_urls[0]
                    print(
                        "Storyboard frame set idx=%s old_url=%s new_url=%s",
                        idx,
                        before_url,
                        fr.get("image_url"),
                    )

        # 保存：拷贝一份 JSON，避免 SQLAlchemy JSON 未检测到嵌套变更
        extra_raw = script.extra_metadata or {}
        extra = dict(extra_raw)
        storyboard_payload = dict(sb or {})
        meta_payload: dict[str, Any] = {}
        if isinstance(storyboard_payload.get("meta"), dict):
            meta_payload = dict(storyboard_payload.get("meta") or {})
        meta_payload.update(
            {
                "image_generation_updated_at": datetime.utcnow().isoformat(),
                "image_generation_style": style,
                "image_generation_style_preset_id": (style_preset_id or "").strip()
                or None,
                "image_generation_style_spec": resolved_style_spec_used
                or (style_spec if isinstance(style_spec, dict) else None),
                "image_generation_style_spec_resolution": resolved_style_spec_resolution_used,
            }
        )
        storyboard_payload["meta"] = meta_payload
        storyboard_payload["frames"] = frames
        extra["storyboard"] = storyboard_payload
        # 直接使用 UPDATE 避免 JSON 变更检测问题
        db.query(Script).filter(Script.id == script_id).update(
            {Script.extra_metadata: extra},
            synchronize_session=False,
        )
        db.commit()
        # 调试：确认数据库中已写入 image_url
        try:
            script_after = db.query(Script).filter(Script.id == script_id).first()
            sb_after = (
                (script_after.extra_metadata or {}).get("storyboard")
                if script_after and script_after.extra_metadata
                else None
            )
            frames_after = (sb_after or {}).get("frames") or []
            if frames_after:
                print(
                    "Storyboard DB first_frame image_url after commit:",
                    frames_after[0].get("image_url"),
                )
        except Exception:
            pass

        if task:
            task.status = TaskStatus.COMPLETED
            db.commit()
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
    finally:
        db.close()


class LabeledReferenceImage(BaseModel):
    """带标签的参考图，用于告知AI每张图代表什么角色/环境"""

    url: str = Field(..., description="参考图URL")
    type: str = Field(
        ...,
        description="参考图类型：character=角色, environment=环境, primary=首要参考, other=其他",
    )
    label: Optional[str] = Field(default=None, description="标签名称，如角色名'老拐'")


class StoryboardImageRequest(BaseModel):
    prompt: Optional[str] = Field(
        default=None, description="可选：覆盖默认提示词，用于本次生成"
    )
    frames: list[int] = Field(
        default_factory=list, description="要生成图像的分镜索引列表（基于0的索引）"
    )
    model: Optional[str] = Field(
        default=None, description="模型ID，可选 'provider:model' 形式"
    )
    generation_profile: Optional[str] = Field(
        default=None,
        description="生成参数档位（后端按 provider+model 解析默认 steps/cfg/negative_prompt）",
    )
    size: Optional[str] = Field(
        default=None, description="分辨率/尺寸（例如 1024x1024 / 2K / 1K）"
    )
    width: Optional[int] = Field(
        default=None, ge=64, le=4096, description="宽度（兼容旧字段）"
    )
    height: Optional[int] = Field(
        default=None, ge=64, le=4096, description="高度（兼容旧字段）"
    )
    style: str = Field(default="realistic")
    style_preset_id: Optional[str] = Field(
        default=None, description="风格预设ID（后端为唯一真源）"
    )
    style_spec: Optional[StyleSpec] = Field(
        default=None, description="风格 schema（允许只传部分字段）"
    )
    aspect_ratio: Optional[Literal["9:16", "16:9"]] = Field(
        default=None, description="宽高比（9:16/16:9）"
    )
    seed: Optional[int] = Field(default=None, description="随机种子（可选）")
    steps: Optional[int] = Field(
        default=None, ge=1, le=60, description="采样步数（可选）"
    )
    cfg_scale: Optional[float] = Field(
        default=None, ge=0.0, le=30.0, description="CFG scale（可选）"
    )
    negative_prompt: Optional[str] = Field(
        default=None, description="反向提示词（可选）"
    )
    strength: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="图生图强度（可选）"
    )
    count: int = Field(
        default=1,
        ge=1,
        le=4,
        description="每帧生成的图像数量（keyframe_mode=start_end 时表示每个关键帧角色各生成 count 张）",
    )
    keyframe_mode: str = Field(
        default="single",
        description="生成模式：single=单张（兼容旧字段 image_url）；start_end=生成首尾关键帧（start_image_url/end_image_url）",
    )
    reference_images: Optional[List[str]] = Field(
        default=None,
        description="优先使用的参考图（环境/角色），传入则走图生图；会与场景环境/角色自动锚点合并",
    )
    labeled_references: Optional[List[LabeledReferenceImage]] = Field(
        default=None,
        description="带标签的参考图列表，包含类型和角色名等元数据，用于构造更精准的提示词",
    )
    start_enabled: Optional[bool] = Field(
        default=True,
        description="keyframe_mode=start_end 时是否生成首帧（默认生成）",
    )
    end_enabled: Optional[bool] = Field(
        default=True,
        description="keyframe_mode=start_end 时是否生成尾帧（默认生成）",
    )


@router.post("/{script_id}/storyboard/generate-images")
async def generate_storyboard_images(
    script_id: int,
    body: StoryboardImageRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.models.task import Task

    # 校验剧本归属
    script_query = (
        _not_deleted(db.query(Script), Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Script.id == script_id)
    )
    if not (current_user.is_admin or current_user.is_superuser):
        script_query = script_query.filter(Story.user_id == current_user.id)
    script = script_query.first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    style_spec_payload = (
        body.style_spec.model_dump(mode="json", exclude_none=True)
        if body.style_spec is not None
        else None
    )
    episode = script.episode
    story = episode.story if episode else None
    from app.core.aspect_ratio import resolve_aspect_ratio

    aspect_ratio = resolve_aspect_ratio(
        request_value=body.aspect_ratio,
        episode_value=episode.aspect_ratio if episode else None,
        story_value=story.default_aspect_ratio if story else None,
    )
    # Serialize labeled_references if present
    labeled_refs_payload = None
    if body.labeled_references:
        labeled_refs_payload = [
            ref.model_dump(mode="json") for ref in body.labeled_references
        ]

    t = Task(
        title=_friendly_task_title("分镜图像生成", script, episode, story),
        description="根据分镜生成图像",
        task_type=TaskType.STORYBOARD_IMAGE_GENERATION,
        prompt=f"Storyboard image generation for script {script_id}",
        parameters=json.dumps(
            {
                "script_id": script_id,
                "prompt": body.prompt,
                "frames": body.frames or [],
                "model": body.model,
                "generation_profile": body.generation_profile,
                "width": body.width,
                "height": body.height,
                "style": body.style,
                "style_preset_id": body.style_preset_id,
                "style_spec": style_spec_payload,
                "aspect_ratio": aspect_ratio,
                "seed": body.seed,
                "steps": body.steps,
                "cfg_scale": body.cfg_scale,
                "negative_prompt": body.negative_prompt,
                "strength": body.strength,
                "count": body.count,
                "keyframe_mode": body.keyframe_mode,
                "reference_images": body.reference_images or [],
                "labeled_references": labeled_refs_payload,
                "start_enabled": body.start_enabled,
                "end_enabled": body.end_enabled,
            },
            ensure_ascii=False,
        ),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    # 委托 Celery worker 执行分镜图像生成
    payload = {
        "script_id": script_id,
        "prompt": body.prompt,
        "frames": body.frames or [],
        "model": body.model,
        "generation_profile": body.generation_profile,
        "size": body.size,
        "width": body.width,
        "height": body.height,
        "style": body.style,
        "style_preset_id": body.style_preset_id,
        "style_spec": style_spec_payload,
        "aspect_ratio": aspect_ratio,
        "seed": body.seed,
        "steps": body.steps,
        "cfg_scale": body.cfg_scale,
        "negative_prompt": body.negative_prompt,
        "strength": body.strength,
        "count": body.count,
        "keyframe_mode": body.keyframe_mode,
        "reference_images": body.reference_images or [],
        "labeled_references": labeled_refs_payload,
        "start_enabled": body.start_enabled,
        "end_enabled": body.end_enabled,
    }
    storyboard_image_generate_task.delay(t.id, payload, current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


def _process_storyboard_video_task(
    task_id: int,
    script_id: int,
    frame_indexes: list[int] | None,
    selections: list[dict[str, Any]] | None = None,
    options: dict[str, Any] | None = None,
):
    from app.core.database import SessionLocal
    from app.models.task import Task, TaskStatus
    from app.services.video.video_task_entrypoints import submit_storyboard_video_tasks

    try:
        submit_storyboard_video_tasks(
            task_id=task_id,
            script_id=script_id,
            frame_indexes=frame_indexes,
            selections=selections,
            options=options,
        )
    except Exception as e:
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                db.commit()
        finally:
            db.close()
        # 让 Celery 任务也呈现失败，便于从 worker 日志快速定位
        raise


class StoryboardVideoSelection(BaseModel):
    frame_index: int = Field(..., ge=0, description="分镜索引（基于0）")
    start_image_url: Optional[str] = Field(
        default=None, description="可选：指定该分镜使用的首帧关键帧 URL"
    )
    end_image_url: Optional[str] = Field(
        default=None, description="可选：指定该分镜使用的尾帧关键帧 URL"
    )


class StoryboardVideoRequest(BaseModel):
    frames: list[int] = Field(
        default_factory=list, description="要生成视频的分镜索引列表（基于0的索引）"
    )
    selections: list[StoryboardVideoSelection] = Field(
        default_factory=list,
        description="可选：为每个分镜显式指定首/尾关键帧，用于任意组合生成视频",
    )
    prompt: Optional[str] = Field(
        default=None,
        description="可选：覆盖生成提示词（不传则使用分镜帧 description/ai_prompt）",
    )
    model: Optional[str] = Field(
        default=None,
        description="可选：视频生成模型（支持 provider:model 前缀，例如 volcengine:doubao-seedance-...）",
    )
    duration: Optional[int] = Field(
        default=None, description="可选：覆盖视频时长（秒）"
    )
    fps: Optional[int] = Field(default=None, description="可选：帧率（默认24）")
    resolution: Optional[str] = Field(
        default=None, description="可选：输出分辨率（例如 480p/720p/1080p）"
    )
    ratio: Optional[Literal["9:16", "16:9"]] = Field(
        default=None, description="可选：宽高比（9:16/16:9）"
    )
    watermark: Optional[bool] = Field(default=None, description="可选：是否包含水印")
    seed: Optional[int] = Field(default=None, description="可选：种子整数")
    camera_fixed: Optional[bool] = Field(
        default=None, description="可选：是否固定摄像头"
    )
    service_tier: Optional[str] = Field(
        default=None, description="可选：service_tier（default/flex）"
    )
    execution_expires_after: Optional[int] = Field(
        default=None,
        description="可选：任务超时时间（秒），仅 service_tier=flex 场景生效",
    )
    return_last_frame: Optional[bool] = Field(
        default=True, description="可选：是否返回 last_frame_url（默认开启）"
    )
    camera_control: Optional[Dict[str, Any]] = Field(
        default=None,
        description="可选：摄像机运动控制参数（仅部分模型支持）",
    )
    use_end_frame: Optional[bool] = Field(
        default=None,
        description="可选：是否使用尾帧。为 False 时强制只用首帧，不再回落到分镜中已有的尾帧。",
    )


@router.post("/{script_id}/storyboard/generate-video")
async def generate_storyboard_video(
    script_id: int,
    body: StoryboardVideoRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # 校验剧本归属
    script_query = (
        _not_deleted(db.query(Script), Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Script.id == script_id)
    )
    if not (current_user.is_admin or current_user.is_superuser):
        script_query = script_query.filter(Story.user_id == current_user.id)
    script = script_query.first()
    if not script:
        raise HTTPException(status_code=404, detail="剧本不存在")

    episode = script.episode
    story = episode.story if episode else None
    from app.core.aspect_ratio import resolve_aspect_ratio

    ratio = resolve_aspect_ratio(
        request_value=body.ratio,
        episode_value=episode.aspect_ratio if episode else None,
        story_value=story.default_aspect_ratio if story else None,
    )
    t = Task(
        title=_friendly_task_title("分镜视频生成", script, episode, story),
        description="根据分镜生成视频",
        task_type=TaskType.VIDEO_GENERATION,
        prompt=f"Storyboard video generation for script {script_id}",
        parameters=json.dumps(
            {
                "script_id": script_id,
                "frames": body.frames or [],
                "selections": [
                    sel.model_dump(mode="json", exclude_none=True)
                    for sel in (body.selections or [])
                ],
                "prompt": body.prompt,
                "model": body.model,
                "duration": body.duration,
                "fps": body.fps,
                "resolution": body.resolution,
                "ratio": ratio,
                "watermark": body.watermark,
                "seed": body.seed,
                "camera_fixed": body.camera_fixed,
                "service_tier": body.service_tier,
                "execution_expires_after": body.execution_expires_after,
                "return_last_frame": body.return_last_frame,
                "camera_control": body.camera_control,
                "use_end_frame": body.use_end_frame,
            },
            ensure_ascii=False,
        ),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    payload = {
        "script_id": script_id,
        "frames": body.frames or [],
        "selections": [
            sel.model_dump(mode="json", exclude_none=True)
            for sel in (body.selections or [])
        ],
        "prompt": body.prompt,
        "model": body.model,
        "duration": body.duration,
        "fps": body.fps,
        "resolution": body.resolution,
        "ratio": ratio,
        "watermark": body.watermark,
        "seed": body.seed,
        "camera_fixed": body.camera_fixed,
        "service_tier": body.service_tier,
        "execution_expires_after": body.execution_expires_after,
        "return_last_frame": body.return_last_frame,
        "camera_control": body.camera_control,
        "use_end_frame": body.use_end_frame,
    }
    storyboard_video_generate_task.delay(t.id, payload, current_user.id)
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
    )

    script_content = ai_content.get("content", "")
    scenes = ai_content.get("scenes", [])
    dialogues_raw = ai_content.get("dialogues", [])
    stage_directions_raw = ai_content.get("stage_directions", [])
    dialogues, stage_directions = _populate_dialogues_and_stage_if_missing(
        scenes, dialogues_raw, stage_directions_raw, story=story
    )
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


class ScriptDialogueAudioGenerateRequest(BaseModel):
    tts_model: str | None = Field(None, description="TTS 模型（默认 speech-2.6-hd）")
    timing_model: str | None = Field(
        None, description="时间轴计算 LLM 模型（默认使用系统默认模型）"
    )
    scene_numbers: list[int] | None = Field(
        None, description="指定要生成的场景编号列表（为空则生成全部）"
    )
    overwrite_audio: bool = Field(False, description="是否覆盖已有 scene 音频")
    overwrite_beats: bool = Field(True, description="是否覆盖已有 scene beats")
    use_duration_control: bool = Field(
        False,
        description="是否启用时长精控（Duration Orchestrator Agent）",
    )


def _update_task_progress(db: Session, task: Task | None, description: str) -> None:
    if not task:
        return
    task.description = description
    db.commit()


def _scene_has_dialogue_audio(scene: Scene, script_id: int) -> bool:
    meta = scene.extra_metadata
    if not isinstance(meta, dict):
        return False
    payload = meta.get("dialogue_audio")
    if not isinstance(payload, dict):
        return False
    if payload.get("script_id") != script_id:
        return False
    return bool(payload.get("oss_url"))


def _scene_number_sort_key(scene: Scene) -> tuple[int, int, str]:
    raw = getattr(scene, "scene_number", None)
    num = _to_int(raw)
    if num is None:
        return (1, 0, str(raw or ""))
    return (0, num, str(raw or ""))


@router.post("/{script_id}/dialogue-audio/generate-async")
async def generate_script_dialogue_audio_async(
    script_id: int,
    body: ScriptDialogueAudioGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步生成“场景对白音轨 + scene_beats”。"""
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

    story = script.episode.story if script.episode else None
    episode = script.episode if script.episode else None

    params = body.model_dump()
    params["script_id"] = script_id
    t = Task(
        title=_friendly_task_title("对白音轨生成", script, episode, story),
        description="生成场景对白音轨（scene）",
        task_type=TaskType.DIALOGUE_AUDIO_GENERATION,
        prompt=f"Dialogue audio generation for script {script_id}",
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    script_dialogue_audio_generate_task.delay(t.id, params, current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


def _process_script_dialogue_audio_task(
    task_id: int, payload: dict, user_id: int
) -> None:
    """后台处理剧本场景对白音轨生成任务（供 Celery 调用）。"""
    import anyio
    from app.core.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = int(payload.get("script_id"))
        overwrite_audio = bool(payload.get("overwrite_audio"))
        overwrite_beats = bool(payload.get("overwrite_beats", True))
        tts_model = payload.get("tts_model") or "speech-2.6-hd"
        timing_model = payload.get("timing_model")  # LLM model for timeline calculation
        use_duration_control = bool(payload.get("use_duration_control", False))
        selected_scene_numbers = payload.get("scene_numbers") or []
        selected_set = {
            int(x)
            for x in selected_scene_numbers
            if isinstance(x, (int, str)) and _to_int(x)
        }

        async def _run() -> None:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise RuntimeError("user_not_found")

            script = (
                db.query(Script)
                .join(Episode, Script.episode_id == Episode.id)
                .join(Story, Episode.story_id == Story.id)
                .filter(Script.id == script_id)
                .filter(
                    True
                    if user.is_admin or user.is_superuser
                    else Story.user_id == user.id
                )
                .first()
            )
            if not script:
                raise RuntimeError("script_not_found")
            episode = script.episode
            if not episode:
                raise RuntimeError("episode_not_found")
            story = episode.story
            if not story:
                raise RuntimeError("story_not_found")

            scenes = story_structure_svc.list_scenes_by_script(db, script_id)
            if selected_set:
                scenes = [
                    s
                    for s in scenes
                    if _to_int(getattr(s, "scene_number", None)) in selected_set
                ]
            scenes = sorted(scenes, key=_scene_number_sort_key)
            if not scenes:
                raise RuntimeError("no_scenes_found")

            # 分支：使用 Duration Orchestrator 或传统逐场景生成
            if use_duration_control:
                # 使用 Duration Orchestrator Agent 进行时长精控
                _update_task_progress(
                    db,
                    task,
                    f"时长精控模式：正在编排 {len(scenes)} 个场景",
                )

                def _progress_cb(msg: str) -> None:
                    _update_task_progress(db, task, msg)

                result = await generate_dialogue_with_duration_control(
                    db,
                    story=story,
                    episode=episode,
                    script=script,
                    scenes=scenes,
                    tts_model=str(tts_model),
                    overwrite_beats=overwrite_beats,
                    timing_model=timing_model,
                    progress_callback=_progress_cb,
                )
                if not result.get("success", False):
                    errors = result.get("errors", [])
                    final_val = result.get("final_validation", {})
                    if final_val and not final_val.get("passed"):
                        # 时长验证失败，但生成本身成功
                        ratio = final_val.get("duration_ratio", 0)
                        _update_task_progress(
                            db,
                            task,
                            f"时长验证未通过：{ratio:.1%}（允许±10%）",
                        )
                    else:
                        raise RuntimeError(
                            f"Duration Orchestrator failed: {'; '.join(errors)}"
                        )
                else:
                    _update_task_progress(
                        db,
                        task,
                        f"时长精控完成：{result.get('statistics', {}).get('duration_ratio', 0):.1%}",
                    )
            else:
                # 传统模式：逐场景生成
                # Calculate fallback per-scene target duration from episode
                episode_duration_minutes = getattr(episode, "duration_minutes", None)
                fallback_target_seconds = None
                if episode_duration_minutes and len(scenes) > 0:
                    # Evenly distribute episode duration across scenes as fallback
                    fallback_target_seconds = (episode_duration_minutes * 60) // len(
                        scenes
                    )

                total = len(scenes)
                skipped = 0
                for idx, scene in enumerate(scenes, start=1):
                    if not overwrite_audio and _scene_has_dialogue_audio(
                        scene, script_id
                    ):
                        beat_count = (
                            db.query(SceneBeat)
                            .filter(SceneBeat.scene_id == scene.id)
                            .count()
                        )
                        if beat_count > 0:
                            skipped += 1
                            _update_task_progress(
                                db,
                                task,
                                f"生成对白音轨：{idx}/{total}（跳过 {skipped}） 场景 {scene.scene_number}",
                            )
                            continue

                    _update_task_progress(
                        db,
                        task,
                        f"生成对白音轨：{idx}/{total}（跳过 {skipped}） 场景 {scene.scene_number}",
                    )
                    # Use scene's estimated_duration_seconds if available, else fallback
                    scene_target = getattr(scene, "estimated_duration_seconds", None)
                    if scene_target is None:
                        scene_target = fallback_target_seconds
                    await generate_scene_dialogue_audio(
                        db,
                        story=story,
                        episode=episode,
                        script=script,
                        scene=scene,
                        tts_model=str(tts_model),
                        overwrite_beats=overwrite_beats,
                        timing_model=timing_model,
                        target_duration_seconds=scene_target,
                    )

        anyio.run(_run)

        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{script_id}:dialogue_audio"
            _update_task_progress(db, task, "对白音轨生成完成")
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            _update_task_progress(db, task, f"对白音轨生成失败：{e}")
    finally:
        db.close()


class ScriptAudioTimelineGenerateRequest(BaseModel):
    overwrite: bool = Field(False, description="是否覆盖重算 episode 音频与时间轴")


def _episode_has_audio_timeline(episode: Episode, script_id: int) -> bool:
    meta = episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    timeline = meta.get("audio_timeline") if isinstance(meta, dict) else None
    if not isinstance(timeline, dict):
        return False
    if timeline.get("script_id") != script_id:
        return False
    ep_audio = timeline.get("episode_audio")
    if not isinstance(ep_audio, dict) or not ep_audio.get("oss_url"):
        return False
    beats = timeline.get("beats")
    return isinstance(beats, list) and len(beats) > 0


@router.post("/{script_id}/audio-timeline/generate-async")
async def generate_script_audio_timeline_async(
    script_id: int,
    body: ScriptAudioTimelineGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """异步生成 episode 级对白音轨拼接与时间轴（存于 episodes.extra_metadata.audio_timeline）。"""
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

    story = script.episode.story if script.episode else None
    episode = script.episode if script.episode else None

    params = body.model_dump()
    params["script_id"] = script_id
    t = Task(
        title=_friendly_task_title("时间轴生成", script, episode, story),
        description="拼接场景音轨并生成时间轴（episode）",
        task_type=TaskType.TIMELINE_GENERATION,
        prompt=f"Episode audio timeline generation for script {script_id}",
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    script_audio_timeline_generate_task.delay(t.id, params, current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


def _process_script_audio_timeline_task(
    task_id: int, payload: dict, user_id: int
) -> None:
    """后台处理 episode 音频拼接与时间轴生成任务（供 Celery 调用）。"""
    import anyio
    from app.core.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = int(payload.get("script_id"))
        overwrite = bool(payload.get("overwrite"))

        async def _run() -> None:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise RuntimeError("user_not_found")

            script = (
                db.query(Script)
                .join(Episode, Script.episode_id == Episode.id)
                .join(Story, Episode.story_id == Story.id)
                .filter(Script.id == script_id)
                .filter(
                    True
                    if user.is_admin or user.is_superuser
                    else Story.user_id == user.id
                )
                .first()
            )
            if not script:
                raise RuntimeError("script_not_found")
            episode = script.episode
            if not episode:
                raise RuntimeError("episode_not_found")
            story = episode.story
            if not story:
                raise RuntimeError("story_not_found")

            if not overwrite and _episode_has_audio_timeline(episode, script_id):
                _update_task_progress(
                    db,
                    task,
                    "已存在 episode 时间轴，跳过生成（如需重算请开启 overwrite）",
                )
                return

            _update_task_progress(db, task, "拼接场景音轨并生成时间轴中…")
            await generate_episode_audio_timeline(
                db,
                story=story,
                episode=episode,
                script=script,
            )

        anyio.run(_run)

        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{script_id}:audio_timeline"
            _update_task_progress(db, task, "时间轴生成完成")
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            _update_task_progress(db, task, f"时间轴生成失败：{e}")
    finally:
        db.close()


class TimelinePipelineGenerateRequest(BaseModel):
    """一键生成时间轴流水线请求参数。"""

    tts_model: str | None = Field(None, description="TTS 模型（默认 speech-2.6-hd）")
    timing_model: str | None = Field(
        None, description="时间轴计算 LLM 模型（默认使用系统默认模型）"
    )
    overwrite_audio: bool = Field(False, description="是否覆盖已有 scene 音频")
    overwrite_timeline: bool = Field(False, description="是否覆盖已有时间轴")
    overwrite_storyboard: bool = Field(False, description="是否覆盖已有分镜帧占位")
    min_pause_seconds: float = Field(1.5, description="分镜帧占位最小停顿秒数")
    use_duration_control: bool = Field(
        False,
        description="是否启用时长精控（Duration Orchestrator）确保时长在±10%目标范围内",
    )


@router.post("/{script_id}/timeline-pipeline/generate-async")
async def generate_timeline_pipeline_async(
    script_id: int,
    body: TimelinePipelineGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """一键生成时间轴流水线（对白音轨 → 时间轴 → 分镜帧占位）。"""
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

    story = script.episode.story if script.episode else None
    episode = script.episode if script.episode else None

    params = body.model_dump()
    params["script_id"] = script_id
    t = Task(
        title=_friendly_task_title("一键时间轴流水线", script, episode, story),
        description="一键生成对白音轨、时间轴、分镜帧占位",
        task_type=TaskType.TIMELINE_PIPELINE,
        prompt=f"Timeline pipeline for script {script_id}",
        parameters=json.dumps(params, ensure_ascii=False),
        user_id=current_user.id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    timeline_pipeline_generate_task.delay(t.id, params, current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


def _process_timeline_pipeline_task(task_id: int, payload: dict, user_id: int) -> None:
    """后台处理一键时间轴流水线任务（对白音轨 → 时间轴 → 分镜帧占位）。"""
    import anyio
    from app.core.database import SessionLocal
    from app.models.user import User

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script_id = int(payload.get("script_id"))
        overwrite_audio = bool(payload.get("overwrite_audio"))
        overwrite_timeline = bool(payload.get("overwrite_timeline"))
        overwrite_storyboard = bool(payload.get("overwrite_storyboard"))
        tts_model = payload.get("tts_model") or "speech-2.6-hd"
        timing_model = payload.get("timing_model")
        min_pause_seconds = float(payload.get("min_pause_seconds") or 1.5)
        min_pause_ms = max(0, int(round(min_pause_seconds * 1000)))
        use_duration_control = bool(payload.get("use_duration_control", False))

        async def _run() -> None:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise RuntimeError("user_not_found")

            script = (
                db.query(Script)
                .join(Episode, Script.episode_id == Episode.id)
                .join(Story, Episode.story_id == Story.id)
                .filter(Script.id == script_id)
                .filter(
                    True
                    if user.is_admin or user.is_superuser
                    else Story.user_id == user.id
                )
                .first()
            )
            if not script:
                raise RuntimeError("script_not_found")
            episode = script.episode
            if not episode:
                raise RuntimeError("episode_not_found")
            story = episode.story
            if not story:
                raise RuntimeError("story_not_found")

            # Step 1: Generate dialogue audio for all scenes
            scenes = story_structure_svc.list_scenes_by_script(db, script_id)
            scenes = sorted(scenes, key=_scene_number_sort_key)
            if not scenes:
                raise RuntimeError("no_scenes_found")

            if use_duration_control:
                # Duration Orchestrator 模式：时长精控
                _update_task_progress(
                    db,
                    task,
                    f"步骤 1/3：时长精控模式 - 编排 {len(scenes)} 个场景…",
                )

                def _progress_cb(msg: str) -> None:
                    _update_task_progress(db, task, f"步骤 1/3：{msg}")

                result = await generate_dialogue_with_duration_control(
                    db,
                    story=story,
                    episode=episode,
                    script=script,
                    scenes=scenes,
                    tts_model=str(tts_model),
                    overwrite_beats=True,
                    timing_model=timing_model,
                    progress_callback=_progress_cb,
                )
                if not result.get("success", False):
                    errors = result.get("errors", [])
                    final_val = result.get("final_validation", {})
                    if final_val and not final_val.get("passed"):
                        ratio = final_val.get("duration_ratio", 0)
                        _update_task_progress(
                            db,
                            task,
                            f"步骤 1/3：时长验证未通过 {ratio:.1%}（允许±10%）",
                        )
                    else:
                        raise RuntimeError(
                            f"Duration Orchestrator failed: {'; '.join(errors)}"
                        )
                else:
                    stats = result.get("statistics", {})
                    ratio = stats.get("duration_ratio", 0)
                    _update_task_progress(
                        db,
                        task,
                        f"步骤 1/3：时长精控完成 {ratio:.1%}",
                    )
            else:
                # 传统模式：逐场景生成
                _update_task_progress(db, task, "步骤 1/3：生成对白音轨…")

                # Calculate fallback per-scene target duration from episode
                episode_duration_minutes = getattr(episode, "duration_minutes", None)
                fallback_target_seconds = None
                if episode_duration_minutes and len(scenes) > 0:
                    # Evenly distribute episode duration across scenes as fallback
                    fallback_target_seconds = (episode_duration_minutes * 60) // len(
                        scenes
                    )

                total = len(scenes)
                skipped = 0
                for idx, scene in enumerate(scenes, start=1):
                    if not overwrite_audio and _scene_has_dialogue_audio(
                        scene, script_id
                    ):
                        beat_count = (
                            db.query(SceneBeat)
                            .filter(SceneBeat.scene_id == scene.id)
                            .count()
                        )
                        if beat_count > 0:
                            skipped += 1
                            _update_task_progress(
                                db,
                                task,
                                f"步骤 1/3：对白音轨 {idx}/{total}（跳过 {skipped}）",
                            )
                            continue

                    _update_task_progress(
                        db,
                        task,
                        f"步骤 1/3：对白音轨 {idx}/{total}（跳过 {skipped}）",
                    )
                    # Use scene's estimated_duration_seconds if available, else fallback
                    scene_target = getattr(scene, "estimated_duration_seconds", None)
                    if scene_target is None:
                        scene_target = fallback_target_seconds
                    await generate_scene_dialogue_audio(
                        db,
                        story=story,
                        episode=episode,
                        script=script,
                        scene=scene,
                        tts_model=str(tts_model),
                        overwrite_beats=True,
                        timing_model=timing_model,
                        target_duration_seconds=scene_target,
                    )

            # Step 2: Generate episode audio timeline
            _update_task_progress(db, task, "步骤 2/3：生成时间轴…")
            if not overwrite_timeline and _episode_has_audio_timeline(
                episode, script_id
            ):
                _update_task_progress(db, task, "步骤 2/3：时间轴已存在，跳过")
            else:
                await generate_episode_audio_timeline(
                    db,
                    story=story,
                    episode=episode,
                    script=script,
                )

            # Step 3: Generate storyboard frame slots from timeline
            _update_task_progress(db, task, "步骤 3/3：生成分镜帧占位…")
            generate_storyboard_from_episode_audio_timeline(
                db,
                script=script,
                episode=episode,
                overwrite_existing=overwrite_storyboard,
                min_pause_duration_ms=min_pause_ms,
            )

        anyio.run(_run)

        if task:
            task.status = TaskStatus.COMPLETED
            task.result_file_path = f"script:{script_id}:timeline_pipeline"
            _update_task_progress(db, task, "一键时间轴流水线完成")
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            _update_task_progress(db, task, f"流水线失败：{e}")
    finally:
        db.close()
