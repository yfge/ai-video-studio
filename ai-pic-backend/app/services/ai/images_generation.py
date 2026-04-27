from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.prompts.manager import prompt_manager
from app.prompts.template_audit import build_prompt_template_audit, sha256_text
from app.prompts.templates import PromptTemplate
from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    build_ai_manager_call,
    normalize_image_gen_request,
)
from app.services.storage.oss_service import oss_service
from app.utils.model_utils import (
    DEFAULT_OPENAI_IMAGE_MODEL,
    canonicalize_openai_image_model,
    is_openai_image_model,
    parse_model_and_provider,
)


def _get_backend_base() -> str:
    return (
        getattr(settings, "INTERNAL_BACKEND_URL", None) or "http://localhost:8000"
    ).rstrip("/")


class ImageGenerationMixin:
    # 保持原有的图像生成功能
    async def generate_virtual_ip_image(
        self,
        ip_name: str,
        description: str,
        style: str = "realistic",
        style_preset_id: str | None = None,
        style_spec: Any | None = None,
        category: str = "portrait",
        model: str = DEFAULT_OPENAI_IMAGE_MODEL,
        additional_prompts: List[str] = None,
        background_story: str = None,
        count: int = 1,
        size: str | None = None,
        aspect_ratio: str | None = None,
        generation_profile: str | None = None,
        seed: int | None = None,
        steps: int | None = None,
        cfg_scale: float | None = None,
        negative_prompt: str | None = None,
        reference_images: list[str] | None = None,
    ) -> Optional[Dict[str, Any]]:
        """为虚拟IP生成图像"""

        raw_model = model or DEFAULT_OPENAI_IMAGE_MODEL
        pure_model, provider_hint = parse_model_and_provider(raw_model)
        pure_model = pure_model or DEFAULT_OPENAI_IMAGE_MODEL

        # Canonicalize common OpenAI image aliases ("dalle-3" -> "dall-e-3"),
        # so size/aspect-ratio normalization can apply provider UI rules reliably.
        if provider_hint == "openai" and pure_model:
            pure_model = canonicalize_openai_image_model(pure_model) or pure_model
            raw_model = f"openai:{pure_model}" if ":" in raw_model else pure_model

        normalized_style_preset_id = (style_preset_id or "").strip() or None

        resolved_style_spec = None
        style_spec_resolution: dict[str, Any] | None = None
        derived_style = style
        style_prompt = ""
        openai_style = "natural" if style == "realistic" else "vivid"
        try:
            if style_preset_id or style_spec is not None:
                from app.utils.style_utils import (
                    build_style_prompt,
                    derive_legacy_image_style,
                    derive_openai_image_style,
                    resolve_style_spec,
                )

                resolved_style_spec, style_spec_resolution = resolve_style_spec(
                    style_spec=style_spec,
                    style_preset_id=style_preset_id,
                    legacy_style=style,
                    fill_defaults=True,
                )
                derived_style = derive_legacy_image_style(resolved_style_spec)
                style_prompt = build_style_prompt(resolved_style_spec)
                openai_style = derive_openai_image_style(
                    resolved_style_spec, fallback=derived_style
                )
        except Exception as exc:  # pragma: no cover - defensive
            resolved_style_spec = None
            style_spec_resolution = {"error": str(exc)}
            derived_style = style
            style_prompt = ""
            openai_style = "natural" if style == "realistic" else "vivid"

        # 使用统一 PromptManager 模板生成运行时提示词（直接用于图像模型）
        try:
            variables = {
                "character_name": ip_name,
                "character_description": description,
                "background_story": background_story,
                "style": derived_style,
                "category": category,
                # style_spec 的 prompt suffix 统一由 AIServiceManager 注入（避免重复叠加）
                "style_prompt": None,
                "additional_prompts": additional_prompts or [],
            }

            prompt_template = None
            try:
                template_name = PromptTemplate.VIRTUAL_IP_IMAGE.value
                base_prompt = prompt_manager.render_prompt(
                    template_name, variables
                ).strip()
                prompt_template = build_prompt_template_audit(
                    template_name, variables=variables
                )
            except Exception:
                if category == "portrait":
                    base_prompt = f"A professional {derived_style} portrait of {ip_name}, {description}"
                else:
                    base_prompt = f"A professional {derived_style} {category} of {ip_name}, {description}"
                if additional_prompts:
                    base_prompt += f", {', '.join(additional_prompts)}"

            normalized = normalize_image_gen_request(
                ImageGenRequest(
                    domain=ImageGenDomain.VIRTUAL_IP,
                    mode=ImageGenMode.TEXT_TO_IMAGE,
                    prompt=base_prompt,
                    model=raw_model,
                    prefer_provider=provider_hint,
                    generation_profile=generation_profile,
                    style=style,
                    style_preset_id=normalized_style_preset_id,
                    style_spec=style_spec,
                    count=count,
                    size=size,
                    aspect_ratio=aspect_ratio,
                    seed=seed,
                    steps=steps,
                    cfg_scale=cfg_scale,
                    negative_prompt=negative_prompt,
                    reference_images=reference_images or [],
                    backend_base=_get_backend_base(),
                ),
                strict=False,
            )
            call = build_ai_manager_call(normalized)

            # For OpenAI direct call / task metadata: approximate the final prompt that will be
            # sent downstream (AIServiceManager appends the same style_spec suffix).
            final_prompt = base_prompt
            if style_prompt:
                final_prompt = f"{final_prompt.rstrip()}\n\n{style_prompt}"
            prompt_sha256 = sha256_text(final_prompt)

            self.logger.info(f"生成图像提示词: {final_prompt[:200]}...")
            self.logger.info(
                "使用模型: %s (provider_hint=%s), 风格: %s, 类别: %s",
                pure_model,
                provider_hint,
                derived_style,
                category,
            )

            # 根据模型选择不同的AI服务
            provider_used = "openai"
            generation_method = "openai_image"
            image_url = None
            model_used = model

            model_id = (normalized.model_id or pure_model).lower()
            provider_key = (normalized.provider or provider_hint or "openai").lower()

            if provider_key == "openai" and is_openai_image_model(model_id):
                # 使用 OpenAI 图像直连 API，并支持按官方 size 选项控制分辨率
                image_url = await self._generate_with_openai_dalle(
                    final_prompt,
                    openai_style,
                    category,
                    size=normalized.size or size or "1024x1024",
                    model=model_id,
                    reference_images=normalized.extra_images,
                )
                provider_used = "openai"
                generation_method = "openai_image"
                model_used = model_id
            elif self.ai_manager:
                response = await self.ai_manager.generate_image(**call)
                if response.success:
                    images = response.data.get("images", [])
                    image_url = images[0] if images else None
                    provider_used = response.provider or provider_used
                    generation_method = f"ai_{provider_used}"
                    model_used = response.model or model_used
                else:
                    self.logger.error(f"AI管理器图像生成失败: {response.error}")
                    image_url = None
            else:
                # 默认使用 OpenAI 图像模型（保持向后兼容）
                image_url = await self._generate_with_openai_dalle(
                    final_prompt,
                    openai_style,
                    category,
                    model=DEFAULT_OPENAI_IMAGE_MODEL,
                )
                provider_used = "openai"
                generation_method = "openai_image"
                model_used = DEFAULT_OPENAI_IMAGE_MODEL

            if image_url:
                try:
                    stored = await self._persist_generated_image(
                        image_url,
                        ip_name=ip_name,
                        category=category,
                        prefix="ai-generated/virtual-ip",
                        metadata={
                            "ip_name": ip_name,
                            "style": derived_style,
                            "category": category,
                            "style_preset_id": (style_preset_id or "").strip() or None,
                            "style_spec": (
                                resolved_style_spec.model_dump(
                                    mode="json", exclude_none=True
                                )
                                if resolved_style_spec is not None
                                else None
                            ),
                            "style_spec_resolution": style_spec_resolution,
                            "size": normalized.size,
                            "aspect_ratio": normalized.aspect_ratio,
                            "width": normalized.width,
                            "height": normalized.height,
                            "provider": provider_used,
                            "model": model_used,
                            "prompt_template": prompt_template,
                            "prompt_sha256": prompt_sha256,
                            "generation_profile": normalized.generation_profile,
                            "seed": normalized.seed,
                            "steps": normalized.steps,
                            "cfg_scale": normalized.cfg_scale,
                            "negative_prompt": normalized.negative_prompt,
                        },
                        require_upload=bool(oss_service),
                    )
                except Exception as exc:
                    self.logger.error(f"图像保存/上传失败: {exc}")
                    return None

                final_image_url = stored.get("oss_url") or stored.get("relative_path")

                return {
                    "image_url": final_image_url,
                    "oss_url": stored.get("oss_url"),
                    "local_file_path": stored.get("local_file_path"),
                    "relative_path": stored.get("relative_path"),
                    "original_image_url": image_url,
                    "oss_upload": stored.get("oss_upload"),
                    "prompt": final_prompt,
                    "style": derived_style,
                    "style_preset_id": (style_preset_id or "").strip() or None,
                    "style_spec": (
                        resolved_style_spec.model_dump(mode="json", exclude_none=True)
                        if resolved_style_spec is not None
                        else None
                    ),
                    "style_spec_resolution": style_spec_resolution,
                    "category": category,
                    "generation_method": generation_method,
                    "template_used": PromptTemplate.VIRTUAL_IP_IMAGE.value,
                    "prompt_template": prompt_template,
                    "prompt_sha256": prompt_sha256,
                    "size": normalized.size,
                    "aspect_ratio": normalized.aspect_ratio,
                    "width": normalized.width,
                    "height": normalized.height,
                    "generation_profile": normalized.generation_profile,
                    "seed": normalized.seed,
                    "steps": normalized.steps,
                    "cfg_scale": normalized.cfg_scale,
                    "negative_prompt": normalized.negative_prompt,
                    "provider_used": provider_used,
                    "model_used": model_used,
                    "usage": {},
                }

        except Exception as exc:
            print(f"图像生成失败: {exc}")

        return None
