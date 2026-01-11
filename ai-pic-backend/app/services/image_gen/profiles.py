from __future__ import annotations

from dataclasses import dataclass, field

from .types import ImageGenMode


@dataclass(frozen=True, slots=True)
class ImageGenProfileDefaults:
    steps: int | None = None
    cfg_scale: float | None = None
    negative_prompt: str | None = None
    strength: float | None = None
    image_reference: str | None = None
    image_fidelity: float | None = None
    human_fidelity: float | None = None


@dataclass(frozen=True, slots=True)
class ImageGenProfile:
    id: str
    label: str
    description: str | None = None
    defaults: ImageGenProfileDefaults = field(default_factory=ImageGenProfileDefaults)


@dataclass(frozen=True, slots=True)
class ImageGenProfileSet:
    default_profile_id: str
    profiles: tuple[ImageGenProfile, ...]

    def resolve(self, profile_id: str | None) -> ImageGenProfile:
        wanted = (profile_id or "").strip()
        if wanted:
            for profile in self.profiles:
                if profile.id == wanted:
                    return profile
        for profile in self.profiles:
            if profile.id == self.default_profile_id:
                return profile
        return self.profiles[0]


DEFAULT_NEGATIVE_PROMPT = (
    "text, watermark, logo, subtitles, UI, collage, split-screen, multi-panel, blurry, lowres, "
    "low quality, jpeg artifacts, bad anatomy, deformed, extra limbs, extra fingers, mutated hands"
)


def _normalize_model_id(value: str) -> str:
    return (value or "").strip().lower().replace(".", "-")


def list_image_gen_profiles(
    *,
    provider: str | None,
    model_id: str | None,
    mode: ImageGenMode,
) -> ImageGenProfileSet | None:
    """Return available profiles for a provider+model (if supported)."""
    if not provider or not model_id:
        return None
    provider_key = provider.lower()
    normalized_model_id = _normalize_model_id(model_id)

    if provider_key == "jimeng":
        if mode == ImageGenMode.IMAGE_TO_IMAGE:
            return ImageGenProfileSet(
                default_profile_id="balanced",
                profiles=(
                    ImageGenProfile(
                        id="balanced",
                        label="均衡",
                        description="适合大多数场景的默认质量档位",
                        defaults=ImageGenProfileDefaults(
                            strength=0.75,
                            steps=25,
                            cfg_scale=7.0,
                        ),
                    ),
                    ImageGenProfile(
                        id="quality",
                        label="质量优先",
                        description="更高步数以获得更稳定细节（更慢）",
                        defaults=ImageGenProfileDefaults(
                            strength=0.7,
                            steps=35,
                            cfg_scale=7.5,
                        ),
                    ),
                    ImageGenProfile(
                        id="fast",
                        label="速度优先",
                        description="更低步数以加快生成（细节可能下降）",
                        defaults=ImageGenProfileDefaults(
                            strength=0.8,
                            steps=18,
                            cfg_scale=6.5,
                        ),
                    ),
                ),
            )

        return ImageGenProfileSet(
            default_profile_id="balanced",
            profiles=(
                ImageGenProfile(
                    id="balanced",
                    label="均衡",
                    description="适合大多数场景的默认质量档位",
                    defaults=ImageGenProfileDefaults(
                        steps=30,
                        cfg_scale=7.0,
                        negative_prompt=DEFAULT_NEGATIVE_PROMPT,
                    ),
                ),
                ImageGenProfile(
                    id="quality",
                    label="质量优先",
                    description="更高步数以获得更稳定细节（更慢）",
                    defaults=ImageGenProfileDefaults(
                        steps=40,
                        cfg_scale=7.5,
                        negative_prompt=DEFAULT_NEGATIVE_PROMPT,
                    ),
                ),
                ImageGenProfile(
                    id="fast",
                    label="速度优先",
                    description="更低步数以加快生成（细节可能下降）",
                    defaults=ImageGenProfileDefaults(
                        steps=20,
                        cfg_scale=6.5,
                        negative_prompt=DEFAULT_NEGATIVE_PROMPT,
                    ),
                ),
            ),
        )

    if provider_key == "keling":
        if mode == ImageGenMode.IMAGE_TO_IMAGE:
            return ImageGenProfileSet(
                default_profile_id="balanced",
                profiles=(
                    ImageGenProfile(
                        id="balanced",
                        label="均衡",
                        description="使用可灵默认参考强度（更适合大多数场景）",
                        defaults=ImageGenProfileDefaults(
                            image_fidelity=0.5,
                            human_fidelity=0.45,
                        ),
                    ),
                    ImageGenProfile(
                        id="identity",
                        label="身份优先",
                        description="更强参考强度，适合虚拟 IP 多次生成保持一致（更保守）",
                        defaults=ImageGenProfileDefaults(
                            image_fidelity=0.7,
                            human_fidelity=0.6,
                        ),
                    ),
                    ImageGenProfile(
                        id="creative",
                        label="更自由",
                        description="更弱参考强度，允许更多变化（更发散）",
                        defaults=ImageGenProfileDefaults(
                            image_fidelity=0.35,
                            human_fidelity=0.35,
                        ),
                    ),
                ),
            )
        return ImageGenProfileSet(
            default_profile_id="balanced",
            profiles=(
                ImageGenProfile(
                    id="balanced",
                    label="均衡",
                    description="默认反向提示词（去水印/文字/低清晰度等）",
                    defaults=ImageGenProfileDefaults(
                        negative_prompt=DEFAULT_NEGATIVE_PROMPT,
                    ),
                ),
            ),
        )

    if provider_key == "volcengine":
        # Volcengine guidance_scale is supported by specific legacy Seedream/Seededit models.
        if (
            mode == ImageGenMode.TEXT_TO_IMAGE
            and "seedream-3-0" in normalized_model_id
            and "t2i" in normalized_model_id
        ):
            return ImageGenProfileSet(
                default_profile_id="balanced",
                profiles=(
                    ImageGenProfile(
                        id="balanced",
                        label="默认",
                        description="使用官方默认 guidance_scale（映射到 cfg_scale）",
                        defaults=ImageGenProfileDefaults(cfg_scale=2.5),
                    ),
                ),
            )
        if (
            mode == ImageGenMode.IMAGE_TO_IMAGE
            and "seededit-3-0" in normalized_model_id
            and "i2i" in normalized_model_id
        ):
            return ImageGenProfileSet(
                default_profile_id="balanced",
                profiles=(
                    ImageGenProfile(
                        id="balanced",
                        label="默认",
                        description="使用官方默认 guidance_scale（映射到 cfg_scale）",
                        defaults=ImageGenProfileDefaults(cfg_scale=5.5),
                    ),
                ),
            )
        return None

    return None


def resolve_image_gen_profile(
    *,
    provider: str | None,
    model_id: str | None,
    mode: ImageGenMode,
    requested_profile: str | None,
) -> ImageGenProfile | None:
    profiles = list_image_gen_profiles(provider=provider, model_id=model_id, mode=mode)
    if profiles is None:
        return None
    return profiles.resolve(requested_profile)
