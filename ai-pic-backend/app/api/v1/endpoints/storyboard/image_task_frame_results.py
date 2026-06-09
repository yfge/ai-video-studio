"""Persist and merge storyboard image task generation results."""

from __future__ import annotations

from functools import partial as _partial

import anyio
from app.services.storyboard.storyboard_prompt_utils import render_keyframe_prompt


def process_single_image(fr, idx, prompt, ref_images, gen_fn, persist_fn, result_meta):
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


def process_keyframe_pair(
    fr,
    idx,
    prompt,
    ref_images,
    gen_fn,
    persist_fn,
    start_enabled,
    end_enabled,
    result_meta,
    override_clean,
    reference_notes,
    compiled_prompt=None,
):
    use_compiled = isinstance(compiled_prompt, dict)
    use_precomputed = not use_compiled and not override_clean and not reference_notes
    start_prompt = (
        compiled_prompt.get("start_keyframe_prompt")
        if use_compiled
        else (
            fr.get("start_keyframe_prompt")
            if use_precomputed and fr.get("start_keyframe_prompt")
            else render_keyframe_prompt(prompt, "start")
        )
    )
    end_prompt = (
        compiled_prompt.get("end_keyframe_prompt")
        if use_compiled
        else (
            fr.get("end_keyframe_prompt")
            if use_precomputed and fr.get("end_keyframe_prompt")
            else render_keyframe_prompt(prompt, "end")
        )
    )

    if start_enabled:
        start_result = anyio.run(gen_fn, start_prompt, ref_images)
        if start_result:
            if isinstance(start_result.get("image_gen"), dict):
                fr["start_image_gen"] = start_result["image_gen"]
                fr["image_gen"] = start_result["image_gen"]
            if isinstance(start_result.get("style_spec"), dict) and not result_meta.get(
                "style_spec"
            ):
                result_meta["style_spec"] = start_result["style_spec"]
                result_meta["style_spec_resolution"] = start_result.get(
                    "style_spec_resolution"
                )
        start_finals, start_originals = _persist_all_variants(
            start_result, idx, persist_fn, "start"
        )
        _merge_keyframe_urls(fr, "start", start_finals, start_originals)

    if end_enabled:
        end_result = anyio.run(gen_fn, end_prompt, ref_images)
        if end_result:
            if isinstance(end_result.get("image_gen"), dict):
                fr["end_image_gen"] = end_result["image_gen"]
            if isinstance(end_result.get("style_spec"), dict) and not result_meta.get(
                "style_spec"
            ):
                result_meta["style_spec"] = end_result["style_spec"]
                result_meta["style_spec_resolution"] = end_result.get(
                    "style_spec_resolution"
                )
        end_finals, end_originals = _persist_all_variants(
            end_result, idx, persist_fn, "end"
        )
        _merge_keyframe_urls(fr, "end", end_finals, end_originals)


def _persist_all_variants(result, idx, persist_fn, role):
    final_urls, original_urls = [], []
    if not result:
        return final_urls, original_urls
    for vi, raw_url in enumerate(result.get("urls") or [], start=1):
        if not raw_url:
            continue
        original_urls.append(raw_url)
        p = anyio.run(
            _partial(persist_fn, keyframe_role=role, variant_index=vi),
            raw_url,
            idx,
            result.get("provider"),
            result.get("model"),
        )
        if p and p.get("final_url"):
            final_urls.append(p["final_url"])
    return final_urls, original_urls


def _merge_keyframe_urls(fr, role, final_urls, original_urls):
    if not final_urls:
        return
    key_urls = f"{role}_image_urls"
    key_url = f"{role}_image_url"
    key_orig = f"{role}_image_url_original"
    existing = (
        list(fr.get(key_urls) or []) if isinstance(fr.get(key_urls), list) else []
    )
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
