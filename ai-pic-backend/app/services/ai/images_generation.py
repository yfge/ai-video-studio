from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate
from app.utils.model_utils import parse_model_and_provider

from app.services.storage.oss_service import oss_service


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

        # 使用提示词管理器生成专业提示词
        try:
            variables = {
                "character_name": ip_name,
                "character_description": description,
                "background_story": background_story,
                "style": derived_style,
                "category": category,
                "additional_prompts": additional_prompts or [],
                "is_default": category == "portrait",
            }

            prompt_manager.render_prompt(
                PromptTemplate.IMAGE_GENERATION.value, variables
            )

            # 使用简单的提示词，避免复杂的AI管理器调用
            if category == "portrait":
                final_prompt = f"A professional {derived_style} portrait of {ip_name}, {description}"
            else:
                final_prompt = f"A professional {derived_style} {category} of {ip_name}, {description}"
            if additional_prompts:
                final_prompt += f", {', '.join(additional_prompts)}"

            direct_prompt = final_prompt
            if style_prompt:
                direct_prompt = f"{final_prompt}\n\n{style_prompt}"

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

            normalized_model = pure_model.lower()
            if (
                normalized_model.startswith("keling-")
                or normalized_model.startswith("kling-")
                or normalized_model in {"keling", "kling"}
            ):
                # 使用可灵AI生成图像
                image_url = await self._generate_with_keling_image(
                    final_prompt,
                    derived_style,
                    category,
                    pure_model,
                    style_preset_id=style_preset_id,
                    style_spec=style_spec,
                    aspect_ratio=aspect_ratio,
                )
                provider_used = "keling"
                generation_method = "keling_image"
            elif normalized_model.startswith("dall-e") or normalized_model.startswith(
                "dalle"
            ):
                # 使用 OpenAI DALL-E 直连 API，并支持按官方 size 选项控制分辨率
                image_url = await self._generate_with_openai_dalle(
                    direct_prompt,
                    openai_style,
                    category,
                    size=size or "1024x1024",
                )
                provider_used = "openai"
                generation_method = "openai_dalle"
            elif self.ai_manager:
                # 使用AI管理器的其他服务（根据模型名偏向特定提供商）
                prefer_provider = provider_hint
                if normalized_model.startswith(
                    "seedream"
                ) or normalized_model.startswith("volcengine"):
                    prefer_provider = "volcengine"
                elif normalized_model.startswith("deepseek"):
                    prefer_provider = "deepseek"
                elif normalized_model.startswith("google"):
                    prefer_provider = "google"
                response = await self.ai_manager.generate_image(
                    prompt=final_prompt,
                    width=1024,
                    height=1024,
                    style=derived_style,
                    style_preset_id=style_preset_id,
                    style_spec=style_spec,
                    model=pure_model,
                    n=count or 1,
                    prefer_provider=prefer_provider,
                    # 对火山 Ark Seedream，size 由 VolcengineProvider 映射为 Ark 的 size 字段（例如 "2K"）
                    size=size if prefer_provider == "volcengine" else size,
                    aspect_ratio=aspect_ratio,
                )
                if response.success:
                    images = response.data.get("images", [])
                    image_url = images[0] if images else None
                    provider_used = response.provider or provider_used
                    generation_method = f"ai_{provider_used}"
                else:
                    self.logger.error(f"AI管理器图像生成失败: {response.error}")
                    image_url = None
            else:
                # 默认使用OpenAI DALL-E（保持向后兼容）
                image_url = await self._generate_with_openai_dalle(
                    direct_prompt,
                    openai_style,
                    category,
                )
                provider_used = "openai"
                generation_method = "openai_dalle"

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
                            "model": model,
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
                    "prompt": direct_prompt,
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
                    "template_used": PromptTemplate.IMAGE_GENERATION.value,
                    "provider_used": provider_used,
                    "model_used": model,
                    "usage": {},
                }

        except Exception as exc:
            print(f"图像生成失败: {exc}")

        return None
