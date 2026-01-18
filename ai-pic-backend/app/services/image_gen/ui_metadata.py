from __future__ import annotations

from typing import Any, Iterable

from app.services.providers.volcengine_provider.guidance_scale import (
    supports_guidance_scale,
)

from .provider_params import supported_ai_manager_keys
from .types import ImageGenMode


def _bool(value: bool) -> bool:
    return bool(value)


def build_image_gen_ui_metadata(
    *,
    provider: str | None,
    model_id: str | None,
    caps: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Build UI metadata describing supported image-gen params by provider+mode."""
    provider_key = (provider or "").strip().lower()
    mid = (model_id or "").strip()
    caps_list = [str(c).lower() for c in (caps or []) if c is not None]

    text_keys = supported_ai_manager_keys(provider_key, ImageGenMode.TEXT_TO_IMAGE)
    image_keys = supported_ai_manager_keys(provider_key, ImageGenMode.IMAGE_TO_IMAGE)

    supports_cfg_scale_t2i = "cfg_scale" in text_keys
    supports_cfg_scale_i2i = "cfg_scale" in image_keys
    if provider_key == "volcengine":
        # Volcengine accepts cfg_scale (mapped to guidance_scale) only on specific models.
        supports_cfg = supports_guidance_scale(mid)
        supports_cfg_scale_t2i = supports_cfg
        supports_cfg_scale_i2i = supports_cfg

    max_count_t2i = 4 if "n" in text_keys else 1
    max_count_i2i = 4 if "count" in image_keys else 1
    if provider_key == "openai" and "dall-e-3" in mid.lower():
        # DALL·E 3 only supports n=1 in practice (and image_to_image is unsupported).
        max_count_t2i = 1
        max_count_i2i = 1

    # Some providers expose img2img as a capability on text_to_image models.
    supports_reference_image = "image_to_image" in caps_list

    max_reference_images_t2i: int | None = None
    if provider_key == "keling":
        max_reference_images_t2i = 1
    if provider_key == "google":
        max_reference_images_t2i = 4

    text_to_image = {
        "supports_seed": _bool("seed" in text_keys),
        "supports_steps": _bool("steps" in text_keys),
        "supports_cfg_scale": _bool(supports_cfg_scale_t2i),
        "supports_negative_prompt": _bool("negative_prompt" in text_keys),
        "supports_style_preset_id": _bool("style_preset_id" in text_keys),
        "supports_style_spec": _bool("style_spec" in text_keys),
        "max_count": max_count_t2i,
        "supports_reference_images": _bool(
            "reference_images" in text_keys
            or "extra_images" in text_keys
            or "image" in text_keys
        ),
    }

    if (
        max_reference_images_t2i is not None
        and text_to_image["supports_reference_images"]
    ):
        text_to_image["max_reference_images"] = max_reference_images_t2i

    image_to_image = {
        "supports_seed": _bool("seed" in image_keys),
        "supports_steps": _bool("steps" in image_keys),
        "supports_cfg_scale": _bool(supports_cfg_scale_i2i),
        "supports_negative_prompt": _bool("negative_prompt" in image_keys),
        "supports_style_preset_id": _bool("style_preset_id" in image_keys),
        "supports_style_spec": _bool("style_spec" in image_keys),
        "supports_strength": _bool("strength" in image_keys),
        "supports_image_reference": _bool("image_reference" in image_keys),
        "supports_image_fidelity": _bool("image_fidelity" in image_keys),
        "supports_human_fidelity": _bool("human_fidelity" in image_keys),
        "max_count": max_count_i2i,
        "supports_extra_images": _bool(
            "extra_images" in image_keys or "reference_images" in image_keys
        ),
    }

    def _append_note(target: list[str], note: str) -> None:
        if note and note not in target:
            target.append(note)

    text_notes: list[str] = []
    image_notes: list[str] = []

    negative_prompt_note = (
        "该提供商不支持 negative_prompt：常用约束需写入 prompt（模板已内置 Constraints）"
    )
    if not text_to_image["supports_negative_prompt"]:
        _append_note(text_notes, negative_prompt_note)

    if supports_reference_image and not image_to_image["supports_negative_prompt"]:
        if provider_key == "keling":
            _append_note(image_notes, "可灵图生图不支持 negative_prompt：请将约束写入 prompt")
        else:
            _append_note(image_notes, negative_prompt_note)

    volc_cfg_note = "火山引擎 cfg_scale 会映射到 guidance_scale（有效范围约 1-10）"
    if provider_key == "volcengine":
        if text_to_image["supports_cfg_scale"]:
            _append_note(text_notes, volc_cfg_note)
        if supports_reference_image and image_to_image["supports_cfg_scale"]:
            _append_note(image_notes, volc_cfg_note)

    if provider_key == "keling" and text_to_image["supports_reference_images"]:
        _append_note(
            text_notes,
            "可灵文生图参考图仅支持 1 张；使用参考图时 negative_prompt 会合并进 prompt",
        )

    if provider_key == "google" and text_to_image["supports_reference_images"]:
        _append_note(
            text_notes,
            "Google/Gemini 参考图会以内联方式上传：为避免 413，建议≤4张且尽量小图（后台会自动压缩）",
        )

    payload: dict[str, Any] = {
        "version": 1,
        "text_to_image": {**text_to_image, "notes": text_notes},
        "image_to_image": {**image_to_image, "notes": image_notes},
    }

    legacy_notes: list[str] = []
    for note in [*text_notes, *image_notes]:
        _append_note(legacy_notes, note)
    if legacy_notes:
        payload["notes"] = legacy_notes

    return {"image_gen": payload}
