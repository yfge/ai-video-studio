from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.template_audit import build_prompt_template_audit, sha256_text
from app.services.image_gen import (
    ImageGenDomain,
    ImageGenMode,
    ImageGenRequest,
    build_ai_manager_call,
    normalize_image_gen_request,
)
from app.services.storage.oss_service import oss_service
from app.utils.model_utils import parse_model_and_provider


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
        model: str = "dalle-3",
        additional_prompts: List[str] = None,
        background_story: str = None,
        count: int = 1,
        size: str | None = None,
        aspect_ratio: str | None = None,
    ) -> Optional[Dict[str, Any]]:
        """为虚拟IP生成图像"""

        raw_model = model or "dalle-3"
        pure_model, provider_hint = parse_model_and_provider(raw_model)
        pure_model = pure_model or "dall-e-3"

        # Canonicalize common OpenAI DALL-E aliases ("dalle-3" -> "dall-e-3"),
        # so size/aspect-ratio normalization can apply provider UI rules reliably.
        if (
            provider_hint == "openai"
            and pure_model
            and pure_model.lower().startswith("dalle-")
        ):
            pure_model = pure_model.lower().replace("dalle-", "dall-e-", 1)
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
                base_prompt = prompt_manager.render_prompt(
                    "virtual_ip_image", variables
                ).strip()
                prompt_template = build_prompt_template_audit(
                    "virtual_ip_image", variables=variables
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
                    style=style,
                    style_preset_id=normalized_style_preset_id,
                    style_spec=style_spec,
                    count=count,
                    size=size,
                    aspect_ratio=aspect_ratio,
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
            generation_method = "openai_dalle"
            image_url = None
            model_used = model

            model_id = (normalized.model_id or pure_model).lower()
            provider_key = (normalized.provider or provider_hint or "openai").lower()

            if provider_key == "openai" and model_id.startswith(("dall-e", "dalle")):
                # 使用 OpenAI DALL-E 直连 API，并支持按官方 size 选项控制分辨率
                image_url = await self._generate_with_openai_dalle(
                    final_prompt,
                    openai_style,
                    category,
                    size=normalized.size or size or "1024x1024",
                )
                provider_used = "openai"
                generation_method = "openai_dalle"
                model_used = "dall-e-3"
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
                # 默认使用OpenAI DALL-E（保持向后兼容）
                image_url = await self._generate_with_openai_dalle(
                    final_prompt,
                    openai_style,
                    category,
                )
                provider_used = "openai"
                generation_method = "openai_dalle"
                model_used = "dall-e-3"

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
                            "aspect_ratio": aspect_ratio,
                            "provider": provider_used,
                            "model": model_used,
                            "prompt_template": prompt_template,
                            "prompt_sha256": prompt_sha256,
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
                    "template_used": "virtual_ip_image",
                    "prompt_template": prompt_template,
                    "prompt_sha256": prompt_sha256,
                    "provider_used": provider_used,
                    "model_used": model_used,
                    "usage": {},
                }

        except Exception as exc:
            print(f"图像生成失败: {exc}")

        return None
