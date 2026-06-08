"""Legacy storyboard generation logic (non-pipeline path)."""

import re
from datetime import datetime
from typing import Any, Dict, List

from app.core.logging import get_logger
from app.schemas.generation import StoryboardModel
from app.services.ai_service import ai_service
from app.services.storyboard.storyboard_prompt_utils import (
    apply_storyboard_prompt_optimizations,
)
from app.utils.json_utils import extract_json_block
from app.utils.marketing_meta import merge_marketing_meta

from .fallback_utils import generate_fallback_frames
from .frame_utils import (
    _augment_frames,
    _enforce_storyboard_variety,
    _load_existing_frames,
    _merge_frames,
    _serialize_frame,
    _to_int,
)

logger = get_logger()


async def generate_storyboard_logic(
    script,
    db,
    *,
    model: str | None = None,
    temperature: float = 0.7,
    frames_per_scene: int = 7,
    max_frames: int | None = None,
    selected_scenes: list[int] | None = None,
    use_plan: bool = True,
) -> dict:
    """Core legacy storyboard generation logic (non-pipeline path)."""
    from app.models.script import Episode, Story

    all_scenes = script.scenes or []
    scenes_filtered, scene_order = _filter_scenes(all_scenes, selected_scenes)

    episode = db.query(Episode).filter(Episode.id == script.episode_id).first()
    story = (
        db.query(Story).filter(Story.id == episode.story_id).first()
        if episode
        else None
    )

    script_data = _build_script_context(
        script, scenes_filtered, scene_order, episode, story
    )

    prefer_provider = "openai"
    model_id = model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)

    scene_map = {idx: sc for idx, sc in enumerate(all_scenes, start=1)}
    existing_frames = _load_existing_frames(script)

    frames_generated, gen_meta = await _call_ai_and_parse(
        script_data,
        model_id,
        prefer_provider,
        temperature,
        frames_per_scene,
        max_frames,
        selected_scenes,
        use_plan,
    )

    _save_plan_if_present(script, gen_meta)

    if not frames_generated:
        frames_generated = generate_fallback_frames(
            script,
            scenes_filtered,
            scene_order,
            frames_per_scene,
            max_frames,
        )
        gen_meta.update(
            generation_method="fallback",
            generation_source="fallback",
            generation_model=None,
            provider_used="fallback",
        )

    if not frames_generated:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="分镜生成失败")

    frames_augmented = _augment_frames(
        frames_generated,
        scene_map=scene_map,
        generation_source=gen_meta["generation_source"],
        generation_method=gen_meta["generation_method"],
        generation_model=gen_meta["generation_model"],
    )
    frames_list = _apply_filters_and_supplement(
        list(frames_augmented),
        all_scenes,
        scene_order,
        selected_scenes,
        frames_per_scene,
        max_frames,
        gen_meta["generation_model"],
        scene_map,
        story,
    )

    merge_targets = scene_order if selected_scenes else None
    merged = _merge_frames(existing_frames, frames_list, merge_targets)
    diversified = _enforce_storyboard_variety(merged)
    apply_storyboard_prompt_optimizations(diversified)

    frames_serialized = [_serialize_frame(fr) for fr in diversified]
    try:
        StoryboardModel.model_validate({"frames": frames_serialized})
    except Exception as exc:
        logger.error(f"Storyboard validation failed before save: {exc}")
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="分镜结构不合法")

    sb = _persist_storyboard(
        script, db, frames_serialized, gen_meta, scene_order, selected_scenes
    )
    return {"success": True, "data": sb}


def _filter_scenes(all_scenes, selected_scenes):
    if selected_scenes:
        selected_set = set(selected_scenes)
        scenes_filtered = [
            sc for idx, sc in enumerate(all_scenes, 1) if idx in selected_set
        ]
        scene_order = [
            idx for idx in range(1, len(all_scenes) + 1) if idx in selected_set
        ]
    else:
        scenes_filtered = all_scenes
        scene_order = list(range(1, len(all_scenes) + 1))
    return scenes_filtered, scene_order


def _build_script_context(script, scenes, scene_order, episode, story):
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
    return {
        "content": script.content,
        "scenes": scenes,
        "dialogues": script.dialogues,
        "stage_directions": script.stage_directions,
        "scene_indices": scene_order,
        "episode": (
            {
                "episode_number": episode.episode_number,
                "title": episode.title,
                "summary": episode.summary,
                "duration_minutes": episode.duration_minutes,
                "scene_count": episode.scene_count,
                **episode_marketing,
            }
            if episode
            else None
        ),
        "story": (
            {
                "title": story.title,
                "genre": story.genre,
                "theme": story.theme,
                "setting_time": story.setting_time,
                "setting_location": story.setting_location,
                "world_building": story.world_building,
                "main_characters": story.main_characters,
                **story_marketing,
            }
            if story
            else None
        ),
    }


async def _call_ai_and_parse(
    script_data,
    model_id,
    prefer_provider,
    temperature,
    frames_per_scene,
    max_frames,
    selected_scenes,
    use_plan,
):
    gen_meta = dict(
        generation_method="direct",
        generation_source=f"ai:{prefer_provider or 'auto'}",
        generation_model=model_id,
        provider_used=prefer_provider,
        reasoning_trace=None,
        agent_usage=None,
        plan_data=None,
        plan_fixes=None,
    )
    frames: List[Dict[str, Any]] = []
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
    if not result:
        return frames, gen_meta
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
            frames = sb_obj.model_dump(mode="python").get("frames") or []
            gen_meta["provider_used"] = result.get("provider_used") or prefer_provider
            gen_meta["generation_model"] = result.get("model_used") or model_id
            method = result.get("generation_method") or gen_meta["generation_method"]
            gen_meta["generation_method"] = method
            prefix = "langgraph" if method.startswith("langgraph") else "ai"
            gen_meta["generation_source"] = (
                f"{prefix}:{gen_meta['provider_used'] or 'auto'}"
            )
            gen_meta["reasoning_trace"] = result.get("reasoning_trace")
            gen_meta["agent_usage"] = result.get("usage")
            gen_meta["plan_data"] = result.get("plan")
            gen_meta["plan_fixes"] = result.get("fixes")
        except Exception as exc:
            logger.warning(f"StoryboardGen validation failed: {exc}")
    return frames, gen_meta


def _save_plan_if_present(script, gen_meta):
    if gen_meta.get("plan_data"):
        try:
            script.storyboard_plan = gen_meta["plan_data"]
            extra_meta = dict(script.extra_metadata or {})
            extra_meta["storyboard_plan"] = gen_meta["plan_data"]
            script.extra_metadata = extra_meta
        except Exception:
            logger.warning("Storyboard plan persistence failed")


def _apply_filters_and_supplement(
    frames_list,
    all_scenes,
    scene_order,
    selected_scenes,
    frames_per_scene,
    max_frames,
    generation_model,
    scene_map,
    story,
):
    if selected_scenes:
        selected_set = {s for s in scene_order if s is not None}
        frames_list = [
            fr for fr in frames_list if _to_int(fr.get("scene_number")) in selected_set
        ]
    if max_frames:
        frames_list = frames_list[:max_frames]
    _supplement_deficit_scenes(
        frames_list,
        all_scenes,
        scene_order,
        frames_per_scene,
        generation_model,
        scene_map,
    )
    _normalize_shot_types(frames_list, all_scenes, story)
    return frames_list


def _supplement_deficit_scenes(
    frames_list, all_scenes, scene_order, frames_per_scene, generation_model, scene_map
):
    try:
        supplementary_raw: List[Dict[str, Any]] = []
        targets = scene_order or list(range(1, len(all_scenes) + 1))
        for s in targets:
            if s is None:
                continue
            count = len(
                [fr for fr in frames_list if _to_int(fr.get("scene_number")) == s]
            )
            deficit = max(0, frames_per_scene - count)
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
            frames_list.extend(
                _augment_frames(
                    supplementary_raw,
                    scene_map=scene_map,
                    generation_source="supplement",
                    generation_method="fallback",
                    generation_model=generation_model,
                )
            )
    except Exception:
        pass


def _normalize_shot_types(frames_list, all_scenes, story):
    allowed = {"远景", "中景", "近景", "特写"}
    en_to_cn = {
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
        norm = en_to_cn.get(shot.lower()) if isinstance(shot, str) else None
        fr["shot_type"] = norm or (shot if shot in allowed else "中景")
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
                    pass
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


def _persist_storyboard(
    script, db, frames_serialized, gen_meta, scene_order, selected_scenes
):
    sb_meta = {
        "version": script.storyboard_version,
        "updated_at": (
            script.storyboard_updated_at.isoformat()
            if script.storyboard_updated_at
            else None
        ),
        "generation_source": gen_meta["generation_source"],
        "generation_method": gen_meta["generation_method"],
        "generation_model": gen_meta["generation_model"],
        "provider": gen_meta["provider_used"],
        "scene_scope": scene_order if selected_scenes else None,
    }
    if gen_meta.get("reasoning_trace"):
        sb_meta["reasoning_trace"] = gen_meta["reasoning_trace"]
    if gen_meta.get("agent_usage"):
        sb_meta["usage"] = gen_meta["agent_usage"]
    if gen_meta.get("plan_fixes"):
        sb_meta["plan_fixes"] = gen_meta["plan_fixes"]
    sb = {"frames": frames_serialized, "meta": sb_meta}
    plan_payload = gen_meta.get("plan_data") or script.storyboard_plan
    if plan_payload:
        sb["plan"] = plan_payload
    extra = dict(script.extra_metadata or {})
    extra["storyboard"] = sb
    script.extra_metadata = extra
    script.storyboard_updated_at = datetime.utcnow()
    script.storyboard_version = (script.storyboard_version or 0) + 1
    db.commit()
    db.refresh(script)
    return sb
