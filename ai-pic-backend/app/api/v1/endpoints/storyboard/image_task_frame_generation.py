"""Single-frame storyboard image task generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.ai_service import ai_service as default_ai_service
from app.services.storage.oss_service import oss_service

from .frame_utils import _abs_url
from .image_task_frame_results import process_keyframe_pair, process_single_image
from .image_task_prompt_runtime import (
    compile_storyboard_image_prompt,
    frame_base_prompt,
    render_storyboard_image_prompt,
)
from .image_task_refs import build_frame_references


@dataclass(frozen=True)
class FramePromptContext:
    override_clean: str
    prompt: str
    ref_images: list[str]
    reference_notes: list[dict[str, Any]]
    compiled_prompt: dict[str, Any]


def generate_frame_image(
    frames,
    idx,
    ctx,
    *,
    options: dict[str, Any],
    prompt_manager,
    ai_service=default_ai_service,
) -> dict:
    fr = frames[idx]
    prompt_ctx = _prepare_prompt_context(fr, idx, ctx, options, prompt_manager)
    if prompt_ctx.ref_images:
        fr["reference_images"] = prompt_ctx.ref_images

    gen_fn = _generation_callback(options, ai_service)
    persist_fn = _persist_callback(options["script_id"], ai_service)
    result_meta: dict = {}
    _process_frame_images(fr, idx, prompt_ctx, options, gen_fn, persist_fn, result_meta)
    return result_meta


def _prepare_prompt_context(
    frame, idx, ctx, options, prompt_manager
) -> FramePromptContext:
    base_prompt, override_clean = frame_base_prompt(
        frame,
        idx,
        prompt_override=options.get("prompt_override"),
        prompt_manager=prompt_manager,
    )
    ref_images, reference_notes, _ = build_frame_references(
        frame,
        idx,
        ctx,
        prompt=base_prompt,
        reference_images=options.get("reference_images"),
        labeled_references=options.get("labeled_references"),
    )
    if options.get("require_reference_images") and not ref_images:
        raise RuntimeError(
            f"分镜帧 {idx + 1} 缺少参考图，请先绑定场景环境或镜头角色参考图后再生成画面"
        )

    compiled_prompt = compile_storyboard_image_prompt(
        frame,
        base_prompt=base_prompt,
        reference_notes=reference_notes,
        model=options.get("model"),
    )
    from app.services.storyboard.dynamic_prompt import apply_dynamic_prompt_bundle

    compiled_prompt = apply_dynamic_prompt_bundle(
        compiled_prompt, options.get("dynamic_prompt_bundle")
    )
    frame["storyboard_prompt_v2"] = compiled_prompt
    prompt = render_storyboard_image_prompt(
        compiled_prompt,
        style=options.get("style"),
        reference_notes=reference_notes,
        labeled_references=options.get("labeled_references"),
        prompt_manager=prompt_manager,
    )
    return FramePromptContext(
        override_clean=override_clean,
        prompt=prompt,
        ref_images=ref_images,
        reference_notes=reference_notes,
        compiled_prompt=compiled_prompt,
    )


def _process_frame_images(
    fr,
    idx,
    prompt_ctx: FramePromptContext,
    options,
    gen_fn,
    persist_fn,
    result_meta,
):
    if options.get("keyframe_mode") == "start_end":
        process_keyframe_pair(
            fr,
            idx,
            prompt_ctx.prompt,
            prompt_ctx.ref_images,
            gen_fn,
            persist_fn,
            options.get("start_enabled"),
            options.get("end_enabled"),
            result_meta,
            prompt_ctx.override_clean,
            prompt_ctx.reference_notes,
            prompt_ctx.compiled_prompt,
        )
        return
    process_single_image(
        fr,
        idx,
        prompt_ctx.prompt,
        prompt_ctx.ref_images,
        gen_fn,
        persist_fn,
        result_meta,
    )


def _generation_callback(options, ai_service):
    async def _gen(prompt, refs):
        try:
            from app.services.storyboard.storyboard_image_generation import (
                generate_storyboard_image_urls,
            )

            return await generate_storyboard_image_urls(
                prompt=prompt,
                refs=[_abs_url(url) for url in refs if url],
                model=options.get("model"),
                generation_profile=options.get("generation_profile"),
                count=options.get("count"),
                size=options.get("size"),
                aspect_ratio=options.get("aspect_ratio"),
                width=options.get("width"),
                height=options.get("height"),
                style=options.get("style"),
                style_preset_id=options.get("style_preset_id"),
                style_spec=options.get("style_spec"),
                seed=options.get("seed"),
                steps=options.get("steps"),
                cfg_scale=options.get("cfg_scale"),
                negative_prompt=options.get("negative_prompt"),
                strength=options.get("strength"),
                ai_service=ai_service,
            )
        except Exception as exc:
            print(f"图像生成失败: {exc}")
        return None

    return _gen


def _persist_callback(script_id, ai_service):
    async def _persist(
        url, frame_index, provider, model, *, keyframe_role="single", variant_index=None
    ):
        try:
            meta = {
                "script_id": script_id,
                "frame_index": frame_index,
                "provider": provider,
                "model": model,
                "keyframe_role": keyframe_role,
            }
            if variant_index is not None:
                meta["variant_index"] = variant_index
            stored = await ai_service._persist_generated_image(
                image_data=url,
                ip_name=f"script-{script_id}",
                category="storyboard",
                prefix="ai-generated/storyboard",
                metadata=meta,
                require_upload=bool(oss_service),
            )
        except Exception as exc:
            print(f"分镜图像持久化失败 idx={frame_index}: {exc}")
            return None
        final_url = stored.get("oss_url") or stored.get("relative_path")
        return {"final_url": final_url, "stored": stored} if final_url else None

    return _persist
