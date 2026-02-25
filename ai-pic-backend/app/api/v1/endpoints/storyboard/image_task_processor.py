"""Storyboard image generation task processor."""

import copy as _copy
from datetime import datetime
from functools import partial as _partial
from typing import Any, Dict, List, Optional

import anyio

from app.core.logging import get_logger
from app.models.script import Script
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.services.ai_service import ai_service
from app.services.storage.oss_service import oss_service
from app.services.storyboard.storyboard_prompt_utils import render_keyframe_prompt

from .frame_utils import _abs_url, _normalize_reference_images, _to_int
from .image_task_refs import ImageRefContext, build_frame_references, load_image_ref_context

logger = get_logger("storyboard_image_task")

def _process_storyboard_image_task(
    task_id: int, script_id: int, frame_indexes: list[int] | None,
    *, prompt_override: str | None = None, model: str | None = None,
    generation_profile: str | None = None, size: str | None = None,
    width: int | None = None, height: int | None = None,
    style: str = "realistic", style_preset_id: str | None = None,
    style_spec: dict[str, Any] | None = None, aspect_ratio: str | None = None,
    seed: int | None = None, steps: int | None = None,
    cfg_scale: float | None = None, negative_prompt: str | None = None,
    strength: float | None = None, reference_images: Optional[List[str]] = None,
    labeled_references: Optional[List[dict[str, Any]]] = None,
    count: int = 1, keyframe_mode: str = "single",
    start_enabled: bool = True, end_enabled: bool = True,
):
    from app.core.database import SessionLocal
    from app.models.task import Task, TaskStatus

    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            task.status = TaskStatus.PROCESSING
            db.commit()

        script = db.query(Script).filter(Script.id == script_id).first()
        if not script:
            raise RuntimeError("剧本不存在")
        sb = (script.extra_metadata or {}).get("storyboard") if script.extra_metadata else None
        if not sb or not sb.get("frames"):
            raise RuntimeError("未找到分镜数据")

        frames_src = list((sb or {}).get("frames") or [])
        frames = [_copy.deepcopy(fr) if isinstance(fr, dict) else fr for fr in frames_src]
        target_indexes = frame_indexes or list(range(len(frames)))

        logger.info(f"[SBIMG] task start | script={script_id} task={task_id} "
                     f"total={len(frames)} targets={target_indexes} model={model}")

        ctx = load_image_ref_context(db, script, script_id)
        w, h = _resolve_dimensions(width, height, size)
        count_int = max(1, min(4, int(count) if count is not None else 1))

        resolved_style_spec_used: dict | None = None
        resolved_style_spec_resolution_used: Any = None

        for idx in target_indexes:
            if idx < 0 or idx >= len(frames):
                logger.warning(f"[SBIMG] frame index out of range: {idx}/{len(frames)}")
                continue
            result_meta = _generate_frame_image(
                frames, idx, ctx,
                prompt_override=prompt_override, model=model,
                generation_profile=generation_profile, size=size,
                width=w, height=h, style=style,
                style_preset_id=style_preset_id, style_spec=style_spec,
                aspect_ratio=aspect_ratio, seed=seed, steps=steps,
                cfg_scale=cfg_scale, negative_prompt=negative_prompt,
                strength=strength, reference_images=reference_images,
                labeled_references=labeled_references,
                count=count_int, keyframe_mode=keyframe_mode,
                start_enabled=start_enabled, end_enabled=end_enabled,
                script_id=script_id,
            )
            if resolved_style_spec_used is None and result_meta.get("style_spec"):
                resolved_style_spec_used = result_meta["style_spec"]
                resolved_style_spec_resolution_used = result_meta.get("style_spec_resolution")

        _save_frames_to_db(
            db, script_id, sb, frames, style, style_preset_id,
            style_spec, resolved_style_spec_used, resolved_style_spec_resolution_used,
        )
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

def _resolve_dimensions(width, height, size):
    w, h = width, height
    if (w is None or h is None) and isinstance(size, str) and size.strip():
        from app.services.providers.image_param_utils import size_to_dimensions
        dims = size_to_dimensions(size)
        if dims:
            w, h = dims
    return w or 1024, h or 1024

def _generate_frame_image(frames, idx, ctx, *, prompt_override, model,
                            generation_profile, size, width, height, style,
                            style_preset_id, style_spec, aspect_ratio,
                            seed, steps, cfg_scale, negative_prompt, strength,
                            reference_images, labeled_references,
                            count, keyframe_mode, start_enabled, end_enabled,
                            script_id) -> dict:
    fr = frames[idx]
    base_prompt = fr.get("ai_prompt") or fr.get("description") or ""
    override_clean = (prompt_override or "").strip()
    if override_clean:
        base_prompt = override_clean
    if not base_prompt:
        base_prompt = prompt_manager.render_prompt(
            PromptTemplate.STORYBOARD_IMAGE_FALLBACK.value,
            {"frame_index": idx + 1, "scene_number": fr.get("scene_number")},
        )

    ref_images, reference_notes, _ = build_frame_references(
        fr, idx, ctx, prompt=base_prompt,
        reference_images=reference_images, labeled_references=labeled_references,
    )

    prompt = prompt_manager.render_prompt(
        PromptTemplate.STORYBOARD_IMAGE_PROMPT.value,
        {"base_prompt": base_prompt, "reference_notes": reference_notes},
    )
    if labeled_references:
        from .utils import build_reference_image_context
        ref_context = build_reference_image_context(labeled_references)
        if ref_context:
            prompt = ref_context + chr(10) + chr(10) + prompt

    if ref_images:
        fr["reference_images"] = ref_images

    async def _gen(p, refs):
        try:
            from app.services.storyboard.storyboard_image_generation import (
                generate_storyboard_image_urls,
            )
            return await generate_storyboard_image_urls(
                prompt=p, refs=[_abs_url(u) for u in refs if u],
                model=model, generation_profile=generation_profile,
                count=count, size=size, aspect_ratio=aspect_ratio,
                width=width, height=height, style=style,
                style_preset_id=style_preset_id, style_spec=style_spec,
                seed=seed, steps=steps, cfg_scale=cfg_scale,
                negative_prompt=negative_prompt, strength=strength,
                ai_service=ai_service,
            )
        except Exception as e:
            print(f"图像生成失败: {e}")
        return None

    async def _persist(url, fidx, provider, mdl, *, keyframe_role="single", variant_index=None):
        try:
            meta = {"script_id": script_id, "frame_index": fidx,
                     "provider": provider, "model": mdl, "keyframe_role": keyframe_role}
            if variant_index is not None:
                meta["variant_index"] = variant_index
            stored = await ai_service._persist_generated_image(
                image_data=url, ip_name=f"script-{script_id}",
                category="storyboard", prefix="ai-generated/storyboard",
                metadata=meta, require_upload=bool(oss_service),
            )
        except Exception as e:
            print(f"分镜图像持久化失败 idx={fidx}: {e}")
            return None
        final_url = stored.get("oss_url") or stored.get("relative_path")
        return {"final_url": final_url, "stored": stored} if final_url else None

    result_meta: dict = {}
    if keyframe_mode == "start_end":
        _process_keyframe_pair(fr, idx, prompt, ref_images, _gen, _persist,
                                start_enabled, end_enabled, result_meta, override_clean, reference_notes)
    else:
        _process_single_image(fr, idx, prompt, ref_images, _gen, _persist, result_meta)
    return result_meta

def _process_single_image(fr, idx, prompt, ref_images, gen_fn, persist_fn, result_meta):
    result = anyio.run(gen_fn, prompt, ref_images)
    if result:
        if isinstance(result.get("image_gen"), dict):
            fr["image_gen"] = result["image_gen"]
        if isinstance(result.get("style_spec"), dict):
            result_meta["style_spec"] = result["style_spec"]
            result_meta["style_spec_resolution"] = result.get("style_spec_resolution")
    final_urls, original_urls = _persist_all_variants(result, idx, persist_fn, "single")
    if final_urls:
        fr["image_url"] = final_urls[0]
        fr["start_image_url"] = final_urls[0]
        fr["start_image_urls"] = final_urls
        if original_urls:
            fr["image_url_original"] = original_urls[0]
            fr["start_image_url_original"] = original_urls[0]

def _process_keyframe_pair(fr, idx, prompt, ref_images, gen_fn, persist_fn,
                            start_enabled, end_enabled, result_meta,
                            override_clean, reference_notes):
    use_precomputed = not override_clean and not reference_notes
    start_prompt = (fr.get("start_keyframe_prompt")
                    if use_precomputed and fr.get("start_keyframe_prompt")
                    else render_keyframe_prompt(prompt, "start"))
    end_prompt = (fr.get("end_keyframe_prompt")
                  if use_precomputed and fr.get("end_keyframe_prompt")
                  else render_keyframe_prompt(prompt, "end"))

    if start_enabled:
        start_result = anyio.run(gen_fn, start_prompt, ref_images)
        if start_result:
            if isinstance(start_result.get("image_gen"), dict):
                fr["start_image_gen"] = start_result["image_gen"]
                fr["image_gen"] = start_result["image_gen"]
            if isinstance(start_result.get("style_spec"), dict) and not result_meta.get("style_spec"):
                result_meta["style_spec"] = start_result["style_spec"]
                result_meta["style_spec_resolution"] = start_result.get("style_spec_resolution")
        start_finals, start_originals = _persist_all_variants(start_result, idx, persist_fn, "start")
        _merge_keyframe_urls(fr, "start", start_finals, start_originals)

    if end_enabled:
        end_result = anyio.run(gen_fn, end_prompt, ref_images)
        if end_result:
            if isinstance(end_result.get("image_gen"), dict):
                fr["end_image_gen"] = end_result["image_gen"]
            if isinstance(end_result.get("style_spec"), dict) and not result_meta.get("style_spec"):
                result_meta["style_spec"] = end_result["style_spec"]
                result_meta["style_spec_resolution"] = end_result.get("style_spec_resolution")
        end_finals, end_originals = _persist_all_variants(end_result, idx, persist_fn, "end")
        _merge_keyframe_urls(fr, "end", end_finals, end_originals)

def _persist_all_variants(result, idx, persist_fn, role):
    final_urls, original_urls = [], []
    if not result:
        return final_urls, original_urls
    for vi, raw_url in enumerate(result.get("urls") or [], start=1):
        if not raw_url:
            continue
        original_urls.append(raw_url)
        p = anyio.run(_partial(persist_fn, keyframe_role=role, variant_index=vi),
                       raw_url, idx, result.get("provider"), result.get("model"))
        if p and p.get("final_url"):
            final_urls.append(p["final_url"])
    return final_urls, original_urls

def _merge_keyframe_urls(fr, role, final_urls, original_urls):
    if not final_urls:
        return
    key_urls = f"{role}_image_urls"
    key_url = f"{role}_image_url"
    key_orig = f"{role}_image_url_original"
    existing = list(fr.get(key_urls) or []) if isinstance(fr.get(key_urls), list) else []
    merged = []
    for url in existing + final_urls:
        if url and url not in merged:
            merged.append(url)
    fr[key_urls] = merged or final_urls
    if merged and not fr.get(key_url):
        fr[key_url] = merged[0]
    if role == "start":
        fr.setdefault("image_url", merged[0] if merged else None)
        if original_urls and not fr.get("image_url_original"):
            fr["image_url_original"] = original_urls[0]
    if original_urls and not fr.get(key_orig):
        fr[key_orig] = original_urls[0]

def _save_frames_to_db(db, script_id, sb, frames, style, style_preset_id,
                        style_spec, resolved_style_spec, resolved_resolution):
    extra_raw = db.query(Script).filter(Script.id == script_id).first()
    if not extra_raw:
        return
    extra = dict(extra_raw.extra_metadata or {})
    storyboard_payload = dict(sb or {})
    meta_payload = dict(storyboard_payload.get("meta") or {}) if isinstance(storyboard_payload.get("meta"), dict) else {}
    meta_payload.update({
        "image_generation_updated_at": datetime.utcnow().isoformat(),
        "image_generation_style": style,
        "image_generation_style_preset_id": (style_preset_id or "").strip() or None,
        "image_generation_style_spec": resolved_style_spec or (style_spec if isinstance(style_spec, dict) else None),
        "image_generation_style_spec_resolution": resolved_resolution,
    })
    storyboard_payload["meta"] = meta_payload
    storyboard_payload["frames"] = frames
    extra["storyboard"] = storyboard_payload
    db.query(Script).filter(Script.id == script_id).update(
        {Script.extra_metadata: extra}, synchronize_session=False,
    )
    db.commit()
