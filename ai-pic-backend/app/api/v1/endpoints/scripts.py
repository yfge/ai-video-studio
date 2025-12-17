import json
import re
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.middleware import get_current_active_user
from app.models.script import Episode, Script, Story
from app.models.story_structure import Environment, Scene, SceneBeat, Shot
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPImage
from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
from app.schemas.generation import (
    StoryboardModel,
    StoryboardPlanModel,
    StoryboardPlanScene,
)
from app.schemas.script import (
    ScriptCreate,
    ScriptGenerationRequest,
    ScriptResponse,
    ScriptUpdate,
)
from app.schemas.story_structure import SceneCreate, ShotCreate
from app.schemas.style import StyleSpec
from app.services import story_structure_service as story_structure_svc
from app.services.ai_service import ai_service
from app.services.dialogue_audio_service import (
    generate_episode_audio_timeline,
    generate_scene_dialogue_audio,
    generate_storyboard_from_episode_audio_timeline,
)
from app.services.storage.oss_service import oss_service
from app.services.task_worker import (
    script_audio_storyboard_generate_task,
    script_audio_timeline_generate_task,
    script_dialogue_audio_generate_task,
    script_generate_task,
    storyboard_generate_task,
    storyboard_image_generate_task,
    storyboard_video_generate_task,
)
from app.utils.json_utils import extract_json_block
from app.utils.model_utils import infer_provider_from_model
from app.utils.script_parser import extract_script_structure
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


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
    return {
        "episode_number": episode.episode_number,
        "title": episode.title,
        "summary": episode.summary,
        "plot_points": episode.plot_points,
        "character_arcs": episode.character_arcs,
        "conflicts": episode.conflicts,
        "duration_minutes": episode.duration_minutes,
        "scene_count": scene_count,
        "scenes": scenes,
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
    return {
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
        "previous_episode_summaries": previous_episode_summaries,
        "character_profiles": character_profiles,
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

    return SceneCreate(
        script_id=script_id,
        scene_number=str(scene_no),
        slug_line=str(slug_line),
        location=location,
        time_of_day=time_of_day,
        summary=summary,
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
    """为缺失的对白/舞台指示生成占位，避免空内容阻断前端流程。"""
    if dialogues:
        return dialogues, stage_directions

    speakers: List[str] = []
    if story and isinstance(story.main_characters, list):
        for raw in story.main_characters:
            if not isinstance(raw, dict):
                continue
            name = raw.get("name") or raw.get("character_name")
            if name:
                speakers.append(str(name))
            if len(speakers) >= 3:
                break
    if not speakers:
        speakers = ["旁白", "路人"]

    generated_dialogues: List[Dict[str, Any]] = []
    generated_stage: List[Dict[str, Any]] = []
    for idx, sc in enumerate(scenes, start=1):
        if not isinstance(sc, dict):
            continue
        scene_no = _to_int(sc.get("scene_number")) or idx
        summary = (
            sc.get("summary")
            or sc.get("description")
            or sc.get("slug_line")
            or f"场景 {scene_no}"
        )
        speaker_a = speakers[0]
        speaker_b = speakers[1] if len(speakers) > 1 else speaker_a
        generated_dialogues.append(
            {
                "scene_number": scene_no,
                "character": speaker_a,
                "content": f"{summary}——我需要再确认细节。",
            }
        )
        generated_dialogues.append(
            {
                "scene_number": scene_no,
                "character": speaker_b,
                "content": "明白，这里可以突出冲突或情绪。",
            }
        )
        if not stage_directions:
            generated_stage.append(
                {
                    "scene_number": scene_no,
                    "timing": "mid",
                    "content": summary,
                    "type": "action",
                }
            )

    final_stage = stage_directions or generated_stage
    return generated_dialogues, final_stage


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
            frame["duration_seconds"] = max(
                2, min(12, (frame.get("duration_seconds") or 3) + ((count % 3) - 1))
            )
            prompt_parts = [
                frame["description"],
                f"景别:{frame['shot_type']}",
                f"运镜:{frame['camera_movement']}",
                f"构图:{frame['composition']}",
            ]
            frame["ai_prompt"] = "；".join(prompt_parts)[:500]
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
    prompt_parts = details + [f"镜头语言:{shot}/{movement}/{composition}"]
    ai_prompt = "；".join(prompt_parts)[:500]
    return description, ai_prompt


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

        import anyio

        async def _run():
            prefer_provider = None
            model_id = request_dict.get("model")
            if model_id and ":" in model_id:
                prefer_provider, model_id = model_id.split(":", 1)
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
        task_type="image_generation",
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
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    t = Task(
        title=f"生成剧本 - 剧集{request.episode_id}",
        description="异步剧本生成",
        task_type="image_generation",
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
    # 简化版提示词
    prompt = (
        "你是专业分镜师，基于剧本的场景生成分镜列表。每个分镜包含："
        "frame_number, scene_number, shot_type, camera_movement, composition, description, duration_seconds, ai_prompt。"
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
    use_plan: bool = Query(False, description="是否先使用分镜规划，再逐场景生成"),
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
                "duration_minutes": episode.duration_minutes if episode else None,
                "scene_count": episode.scene_count if episode else None,
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

    reasoner_result = None
    if getattr(ai_service, "storyboard_reasoner", None) and use_plan:
        try:
            reasoner_result = await ai_service.storyboard_reasoner.generate(
                script=script_data,
                frames_per_scene=frames_per_scene,
                max_frames=max_frames,
                model=model_id,
                prefer_provider=prefer_provider,
                temperature=temperature,
                selected_scenes=selected_scenes,
            )
            if reasoner_result and reasoner_result.get("reasoning_trace"):
                try:
                    logger.info(
                        f"Storyboard Reasoner trace: {reasoner_result['reasoning_trace']}"
                    )
                except Exception:
                    pass
        except Exception as exc:
            logger.warning(f"Storyboard LangGraph reasoner failed: {exc}")

    frames_generated: List[Dict[str, Any]] = []
    generation_method = "direct"
    generation_source = f"ai:{prefer_provider or 'auto'}"
    generation_model = model_id
    provider_used: Optional[str] = prefer_provider

    if reasoner_result and reasoner_result.get("content"):
        try:
            reasoned_raw = reasoner_result.get("content")
            reasoned_payload = (
                reasoned_raw
                if isinstance(reasoned_raw, dict)
                else extract_json_block(reasoned_raw)
            )
            if not isinstance(reasoned_payload, dict):
                raise ValueError("Storyboard reasoner returned non-JSON payload")
            StoryboardModel.model_validate(reasoned_payload)
            frames_generated = reasoned_payload.get("frames") or []
            provider_used = reasoner_result.get("provider_used") or prefer_provider
            generation_model = reasoner_result.get("model_used") or model_id
            generation_method = (
                reasoner_result.get("generation_method") or "langgraph_plan"
            )
            generation_source = f"langgraph:{provider_used or 'auto'}"
        except Exception as exc:
            logger.warning(
                f"Storyboard reasoner response invalid, fallback to standard pipeline: {exc}"
            )
            frames_generated = []

    # 先走规划流程（可选）
    if not frames_generated and use_plan:
        plan_resp = await ai_service.generate_storyboard_plan(
            script=script_data,
            frames_per_scene=frames_per_scene,
            selected_scenes=selected_scenes,
            model=model_id,
            prefer_provider=prefer_provider,
            temperature=0.3,
        )
        if plan_resp and plan_resp.get("normalized"):
            try:
                StoryboardPlanModel.model_validate(plan_resp["normalized"])
                script.storyboard_plan = plan_resp["normalized"]
                extra_meta = dict(script.extra_metadata or {})
                extra_meta["storyboard_plan"] = plan_resp["normalized"]
                script.extra_metadata = extra_meta
                generation_method = "plan"
                provider_used = plan_resp.get("provider_used") or prefer_provider
                generation_source = f"ai_plan:{provider_used or 'auto'}"
                generation_model = plan_resp.get("model_used") or model_id

                plan_scenes = plan_resp["normalized"].get("scenes", [])
                frames_all: List[Dict[str, Any]] = []
                for sp in plan_scenes:
                    try:
                        sp_model = StoryboardPlanScene.model_validate(sp)
                    except Exception:
                        continue
                    frames_scene = (
                        await ai_service.generate_storyboard_from_plan_for_scene(
                            script=script_data,
                            scene_plan=sp_model,
                            model=model_id,
                            prefer_provider=prefer_provider,
                            temperature=temperature,
                            max_frames=max_frames,
                        )
                    )
                    if frames_scene:
                        frames_all.extend(frames_scene)
                if frames_all:
                    frames_generated = frames_all
            except Exception as e:
                logger.warning(f"Storyboard plan validate/apply failed: {e}")

    # 若规划流程未生成结果，则直接调用AI接口
    if not frames_generated:
        result = await ai_service.generate_storyboard(
            script=script_data,
            model=model_id,
            prefer_provider=prefer_provider,
            temperature=temperature,
            frames_per_scene=frames_per_scene,
            max_frames=max_frames,
            # 此处已在上方显式尝试过 LangGraph / 规划管线，这里只作为直连兜底，
            # 因此关闭 AIService 内部的 LangGraph 优先逻辑，避免重复尝试。
            prefer_graph=False,
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
                    generation_source = f"ai:{provider_used or 'auto'}"
                    generation_model = result.get("model_used") or model_id
                    generation_method = (
                        result.get("generation_method") or generation_method
                    )
                except Exception as exc:
                    logger.warning(f"StoryboardGen validation failed: {exc}")

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
            base_desc = (fr.get("description") or "").strip()
            prompt_parts = [base_desc]
            if scene_no:
                prompt_parts.append(f"场景 {scene_no}")
            prompt_parts.append(f"景别: {fr.get('shot_type')}")
            prompt_parts.append(f"运镜: {fr.get('camera_movement')}")
            prompt_parts.append(f"构图: {fr.get('composition')}")
            if chars:
                prompt_parts.append(f"人物: {', '.join(chars[:5])}")
            fr["ai_prompt"] = "；".join([p for p in prompt_parts if p])[:500]
    except Exception:
        pass

    merge_targets = scene_order if selected_scenes else None
    merged_frames = _merge_frames(existing_frames, frames_list, merge_targets)
    diversified_frames = _enforce_storyboard_variety(merged_frames)

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
    sb = {"frames": frames_serialized, "meta": sb_meta}
    if script.storyboard_plan:
        sb["plan"] = script.storyboard_plan
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
    use_plan: bool = Query(False, description="是否先使用分镜规划，再逐场景生成"),
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
        task_type="image_generation",
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


def _process_storyboard_image_task(
    task_id: int,
    script_id: int,
    frame_indexes: list[int] | None,
    *,
    prompt_override: str | None = None,
    model: str | None = None,
    width: int = 1024,
    height: int = 1024,
    style: str = "realistic",
    style_preset_id: str | None = None,
    style_spec: dict[str, Any] | None = None,
    reference_images: Optional[List[str]] = None,
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

        async def _gen_images(prompt: str, ref_imgs: List[str]) -> dict | None:
            try:
                prefer_provider = None
                model_id = model
                if model_id and ":" in model_id:
                    prefer_provider, model_id = model_id.split(":", 1)
                if not prefer_provider:
                    prefer_provider = infer_provider_from_model(model_id or "")

                refs = [_abs_url(u) for u in ref_imgs if u]

                if refs:
                    base_image = refs[0]
                    extra = refs[1:]
                    resp = await ai_service.ai_manager.image_to_image(
                        image_url=base_image,
                        prompt=prompt,
                        model=model_id,
                        prefer_provider=prefer_provider,
                        count=count_int,
                        extra_images=extra,
                        width=width,
                        height=height,
                        style=style,
                        style_preset_id=style_preset_id,
                        style_spec=style_spec,
                    )
                else:
                    resp = await ai_service.ai_manager.generate_image(
                        prompt=prompt,
                        model=model_id,
                        prefer_provider=prefer_provider,
                        width=width,
                        height=height,
                        style=style,
                        style_preset_id=style_preset_id,
                        style_spec=style_spec,
                        n=count_int,
                    )
                if resp.success:
                    data = resp.data if isinstance(resp.data, dict) else {}
                    urls: list[str] = []
                    url_single = data.get("image_url") or data.get("url")
                    if isinstance(url_single, str) and url_single:
                        urls.append(url_single)
                    # 兼容火山 Seedream 等返回 {"images": [...]} 的格式
                    images = data.get("images")
                    if isinstance(images, list):
                        for item in images:
                            if isinstance(item, str) and item:
                                urls.append(item)
                            elif isinstance(item, dict) and item.get("url"):
                                urls.append(str(item.get("url")))

                    deduped: list[str] = []
                    for u in urls:
                        if u and u not in deduped:
                            deduped.append(u)
                    if deduped:
                        return {
                            "urls": deduped,
                            "provider": resp.provider,
                            "model": resp.model,
                            "style_spec": (
                                (resp.metadata or {}).get("style_spec")
                                if isinstance(resp.metadata, dict)
                                else None
                            ),
                            "style_spec_resolution": (
                                (resp.metadata or {}).get("style_spec_resolution")
                                if isinstance(resp.metadata, dict)
                                else None
                            ),
                        }
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
            prompt = fr.get("ai_prompt") or fr.get("description") or ""
            override_clean = (prompt_override or "").strip()
            if override_clean:
                prompt = override_clean
            if not prompt:
                prompt = (
                    f"Generate an image for storyboard frame {idx + 1} (scene {fr.get('scene_number') or ''}) "
                    "consistent with references and overall story style."
                )
            frame_log = f"[SBIMG] generating frame | idx={idx} scene={fr.get('scene_number')} prompt_len={len(prompt)}"
            logger.info(frame_log)
            print(frame_log, flush=True)

            scene_no = _to_int(fr.get("scene_number"))
            char_refs: List[str] = []

            # 1) 已存在于分镜帧上的参考图（用户手动/前序管线写入）
            frame_refs = _normalize_reference_images(fr.get("reference_images") or [])
            if frame_refs:
                char_refs.append("帧参考图")

            # 2) 前端调用时附带的额外参考图（单次请求作用域）
            payload_refs = _normalize_reference_images(reference_images or [])
            if payload_refs:
                char_refs.append("用户提供的参考图")

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
                            char_refs.append(f"{name} 的参考图")
                            char_anchor_refs.append(_abs_url(img_url))

            # 4) 场景环境参考图
            env_refs = _normalize_reference_images(
                env_images_by_scene.get(scene_no or -1, []) or []
            )
            if env_refs:
                char_refs.append("环境参考图")

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

            if char_refs:
                prompt = prompt + "\n参考图像：" + " | ".join(char_refs)
            if ref_images:
                fr["reference_images"] = ref_images

            if keyframe_mode == "start_end":
                # 首尾关键帧：生成 start/end 两张，并保持 image_url 指向首帧用于兼容旧 UI
                start_prompt = f"{prompt}\n\n（关键帧：首帧）请生成该镜头开始瞬间的画面，保持构图与风格一致。"
                end_prompt = f"{prompt}\n\n（关键帧：尾帧）请生成该镜头结束瞬间的画面，体现动作完成后的状态，保持构图与风格一致。"

                start_result = None
                if start_enabled:
                    start_result = anyio.run(_gen_images, start_prompt, ref_images)
                    if start_result:
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
    width: int = Field(default=1024, ge=64, le=2048)
    height: int = Field(default=1024, ge=64, le=2048)
    style: str = Field(default="realistic")
    style_preset_id: Optional[str] = Field(
        default=None, description="风格预设ID（后端为唯一真源）"
    )
    style_spec: Optional[StyleSpec] = Field(
        default=None, description="风格 schema（允许只传部分字段）"
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
    background_tasks: BackgroundTasks,
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
    t = Task(
        title=_friendly_task_title("分镜图像生成", script, episode, story),
        description="根据分镜生成图像",
        task_type="image_generation",
        prompt=f"Storyboard image generation for script {script_id}",
        parameters=json.dumps(
            {
                "script_id": script_id,
                "prompt": body.prompt,
                "frames": body.frames or [],
                "model": body.model,
                "width": body.width,
                "height": body.height,
                "style": body.style,
                "style_preset_id": body.style_preset_id,
                "style_spec": style_spec_payload,
                "count": body.count,
                "keyframe_mode": body.keyframe_mode,
                "reference_images": body.reference_images or [],
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
        "width": body.width,
        "height": body.height,
        "style": body.style,
        "style_preset_id": body.style_preset_id,
        "style_spec": style_spec_payload,
        "count": body.count,
        "keyframe_mode": body.keyframe_mode,
        "reference_images": body.reference_images or [],
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
    from app.core.logging import get_logger
    from app.models.task import Task, TaskStatus

    logger = get_logger("storyboard_video_task")
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

        if not ai_service.ai_manager:
            raise RuntimeError("AI管理器未初始化，无法生成视频")

        # 拷贝一份帧列表，避免直接在 SQLAlchemy 追踪的 JSON 结构上就地修改
        import copy as _copy  # 局部导入避免循环依赖

        frames_src = list((sb or {}).get("frames") or [])
        frames: List[Dict[str, Any]] = [
            _copy.deepcopy(fr) if isinstance(fr, dict) else fr for fr in frames_src
        ]
        target_indexes = frame_indexes or list(range(len(frames)))

        import anyio

        def _coerce_duration(value: Any) -> int:
            try:
                dur = float(value)
            except (TypeError, ValueError):
                return 5
            if dur <= 0:
                return 5
            # Seedance 目前支持 2~12 秒（参考 docs/api/volcengine-video.md）
            dur_int = int(round(dur))
            return max(2, min(dur_int, 12))

        selection_by_index: dict[int, dict[str, Any]] = {}
        for item in selections or []:
            if not isinstance(item, dict):
                continue
            raw_idx = item.get("frame_index")
            try:
                idx_int = int(raw_idx)
            except (TypeError, ValueError):
                continue
            selection_by_index[idx_int] = item

        opts = options or {}
        return_last_frame = opts.get("return_last_frame")
        if return_last_frame is None:
            return_last_frame = True

        async def _gen_video(
            image_url: str,
            prompt: Optional[str],
            duration: int,
            end_image_url: Optional[str] = None,
        ) -> dict:
            try:
                result = await ai_service.generate_video(
                    prompt=prompt,
                    image_url=image_url,
                    end_image_url=end_image_url,
                    model=opts.get("model"),
                    duration=duration,
                    fps=int(opts.get("fps") or 24),
                    resolution=str(opts.get("resolution") or "720p"),
                    ratio=opts.get("ratio"),
                    watermark=opts.get("watermark"),
                    seed=opts.get("seed"),
                    camera_fixed=opts.get("camera_fixed"),
                    service_tier=opts.get("service_tier"),
                    execution_expires_after=opts.get("execution_expires_after"),
                    return_last_frame=return_last_frame,
                )
                return result or {"success": False, "error": "视频生成失败（空响应）"}
            except Exception as e:
                logger.exception("视频生成失败: %s", e)
                return {"success": False, "error": str(e)}

        generated_count = 0
        skipped_no_start = 0
        last_error: str | None = None

        for idx in target_indexes:
            if idx < 0 or idx >= len(frames):
                continue
            fr = frames[idx]
            if not isinstance(fr, dict):
                continue

            selection = selection_by_index.get(idx) or {}
            raw_start_url = selection.get("start_image_url")
            raw_end_url = selection.get("end_image_url")

            if not raw_start_url:
                raw_start_url = (
                    fr.get("start_image_url")
                    or fr.get("image_url")
                    or (
                        (fr.get("start_image_urls") or [None])[0]
                        if isinstance(fr.get("start_image_urls"), list)
                        else None
                    )
                    or fr.get("end_image_url")
                    or (
                        (fr.get("end_image_urls") or [None])[0]
                        if isinstance(fr.get("end_image_urls"), list)
                        else None
                    )
                    or ""
                )
            if not raw_end_url:
                raw_end_url = (
                    fr.get("end_image_url")
                    or (
                        (fr.get("end_image_urls") or [None])[0]
                        if isinstance(fr.get("end_image_urls"), list)
                        else None
                    )
                    or ""
                )

            if not raw_start_url:
                skipped_no_start += 1
                continue

            start_url = _abs_url(str(raw_start_url))
            end_url = _abs_url(str(raw_end_url)) if raw_end_url else None

            prompt_value = (
                fr.get("ai_prompt") or fr.get("description") or ""
            ).strip() or None
            prompt_override = (
                (opts.get("prompt") or "").strip() if opts.get("prompt") else None
            )
            if prompt_override:
                prompt_value = prompt_override

            duration_int = _coerce_duration(
                opts.get("duration")
                if opts.get("duration") is not None
                else fr.get("duration_seconds")
            )

            video = anyio.run(
                _gen_video,
                start_url,
                prompt_value,
                duration_int,
                end_url,
            )
            if not isinstance(video, dict) or not video.get("video_url"):
                if isinstance(video, dict) and video.get("error"):
                    last_error = str(video.get("error"))
                else:
                    last_error = "视频生成失败：未返回 video_url"
                continue

            fr["video_url"] = video.get("video_url")
            fr["video_url_original"] = video.get("original_video_url")
            fr["video_thumbnail_url"] = video.get("thumbnail_url")
            fr["video_thumbnail_url_original"] = video.get("original_thumbnail_url")
            fr["video_last_frame_url"] = video.get("last_frame_url")
            fr["video_last_frame_url_original"] = video.get("original_last_frame_url")

            def _merge_urls(existing: Any, new_val: str | None) -> list[str]:
                merged: list[str] = []
                if isinstance(existing, list):
                    for u in existing:
                        if isinstance(u, str) and u and u not in merged:
                            merged.append(u)
                if new_val and new_val not in merged:
                    merged.append(new_val)
                return merged

            fr["video_urls"] = _merge_urls(fr.get("video_urls"), video.get("video_url"))
            fr["video_thumbnail_urls"] = _merge_urls(
                fr.get("video_thumbnail_urls"), video.get("thumbnail_url")
            )
            fr["video_last_frame_urls"] = _merge_urls(
                fr.get("video_last_frame_urls"), video.get("last_frame_url")
            )

            fr["video_generation"] = {
                "duration": video.get("duration"),
                "provider": video.get("provider_used"),
                "model": video.get("model_used"),
                "method": video.get("generation_method"),
                "prompt": prompt_value,
                "resolution": opts.get("resolution"),
                "ratio": opts.get("ratio"),
                "start_image_url": raw_start_url,
                "end_image_url": raw_end_url or None,
                "thumbnail_url": video.get("thumbnail_url"),
                "last_frame_url": video.get("last_frame_url"),
            }
            generated_count += 1

        if generated_count == 0:
            if skipped_no_start > 0 and not last_error:
                raise RuntimeError("未生成任何视频：未找到可用首帧关键帧 URL")
            raise RuntimeError(f"未生成任何视频：{last_error or '未知错误'}")

        # 保存：拷贝一份 JSON，避免 SQLAlchemy JSON 未检测到嵌套变更
        extra_raw = script.extra_metadata or {}
        extra = dict(extra_raw)
        storyboard_payload = dict(sb or {})
        storyboard_payload["frames"] = frames
        extra["storyboard"] = storyboard_payload
        db.query(Script).filter(Script.id == script_id).update(
            {Script.extra_metadata: extra},
            synchronize_session=False,
        )
        db.commit()

        if task:
            task.status = TaskStatus.COMPLETED
            db.commit()
    except Exception as e:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            db.commit()
        # 让 Celery 任务也呈现失败，便于从 worker 日志快速定位
        raise
    finally:
        db.close()


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
    ratio: Optional[str] = Field(
        default=None, description="可选：宽高比（例如 16:9/9:16/adaptive）"
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
    t = Task(
        title=_friendly_task_title("分镜视频生成", script, episode, story),
        description="根据分镜生成视频",
        task_type="image_generation",
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
                "ratio": body.ratio,
                "watermark": body.watermark,
                "seed": body.seed,
                "camera_fixed": body.camera_fixed,
                "service_tier": body.service_tier,
                "execution_expires_after": body.execution_expires_after,
                "return_last_frame": body.return_last_frame,
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
        "ratio": body.ratio,
        "watermark": body.watermark,
        "seed": body.seed,
        "camera_fixed": body.camera_fixed,
        "service_tier": body.service_tier,
        "execution_expires_after": body.execution_expires_after,
        "return_last_frame": body.return_last_frame,
    }
    storyboard_video_generate_task.delay(t.id, payload, current_user.id)
    return {"success": True, "data": {"task_id": t.id, "status": t.status}}


@router.get("/", response_model=List[ScriptResponse])
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
    query = (
        _not_deleted(db.query(Script), Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Episode.is_deleted.is_(False))
        .filter(Story.is_deleted.is_(False))
    )

    if episode_id:
        query = query.filter(Script.episode_id == episode_id)
    if episode_business_id:
        query = query.filter(Episode.business_id == episode_business_id)

    if status:
        query = query.filter(Script.status == status)

    if format_type:
        query = query.filter(Script.format_type == format_type)

    # 只允许访问当前用户故事下的剧本
    if not current_user.is_admin and not current_user.is_superuser:
        query = query.filter(Story.user_id == current_user.id)

    scripts = query.order_by(Script.created_at.desc()).offset(skip).limit(limit).all()
    return [ScriptResponse.from_orm(script) for script in scripts]


@router.get("", response_model=List[ScriptResponse], include_in_schema=False)
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


@router.get("/episode/{episode_id}", response_model=List[ScriptResponse])
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
    # 这里不再对结果做 ORDER BY，仅取一批脚本返回，前端默认使用第一条。
    scripts = (
        _not_deleted(db.query(Script), Script)
        .filter(Script.episode_id == episode_id)
        .limit(50)
        .all()
    )
    return [ScriptResponse.from_orm(script) for script in scripts]


@router.get("/episode/business/{episode_business_id}", response_model=List[ScriptResponse])
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
        .filter(Script.episode_id == episode.id)
        .limit(50)
        .all()
    )
    return [ScriptResponse.from_orm(script) for script in scripts]


async def _regenerate_script_instance(
    *,
    db: Session,
    script: Script,
    episode: Episode,
    story: Story,
) -> Script:
    """复用的剧本重新生成逻辑，供业务ID/主键路由调用。"""
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
    prefer_provider = None
    model_id = original_params.get("model")
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


@router.post("/{script_id}/regenerate", response_model=ScriptResponse)
async def regenerate_script(
    script_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """重新生成剧本内容"""
    script = _get_script_by_identifier(db, script_id, None, current_user)

    episode = script.episode
    if not episode or getattr(episode, "is_deleted", False):
        raise HTTPException(status_code=404, detail="剧集不存在")

    story = episode.story
    if not story or getattr(story, "is_deleted", False):
        raise HTTPException(status_code=404, detail="故事不存在")

    regenerated = await _regenerate_script_instance(
        db=db, script=script, episode=episode, story=story
    )
    return ScriptResponse.from_orm(regenerated)


@router.post("/business/{script_business_id}/regenerate", response_model=ScriptResponse)
async def regenerate_script_by_business_id(
    script_business_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """按 business_id 重新生成剧本内容"""
    script = _get_script_by_identifier(db, None, script_business_id, current_user)
    episode = script.episode
    if not episode or getattr(episode, "is_deleted", False):
        raise HTTPException(status_code=404, detail="剧集不存在")
    story = episode.story
    if not story or getattr(story, "is_deleted", False):
        raise HTTPException(status_code=404, detail="故事不存在")

    regenerated = await _regenerate_script_instance(
        db=db, script=script, episode=episode, story=story
    )
    return ScriptResponse.from_orm(regenerated)


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
    scene_numbers: list[int] | None = Field(
        None, description="指定要生成的场景编号列表（为空则生成全部）"
    )
    overwrite_audio: bool = Field(False, description="是否覆盖已有 scene 音频")
    overwrite_beats: bool = Field(True, description="是否覆盖已有 scene beats")


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
        task_type="image_generation",
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

            total = len(scenes)
            skipped = 0
            for idx, scene in enumerate(scenes, start=1):
                if not overwrite_audio and _scene_has_dialogue_audio(scene, script_id):
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
                await generate_scene_dialogue_audio(
                    db,
                    story=story,
                    episode=episode,
                    script=script,
                    scene=scene,
                    tts_model=str(tts_model),
                    overwrite_beats=overwrite_beats,
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
        task_type="image_generation",
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
