from __future__ import annotations

from dataclasses import dataclass, field

from .types import ImageGenMode


@dataclass(frozen=True, slots=True)
class ImageGenProfileDefaults:
    steps: int | None = None
    cfg_scale: float | None = None
    negative_prompt: str | None = None
    strength: float | None = None


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
                            steps=25,
                            cfg_scale=7.0,
                            negative_prompt=DEFAULT_NEGATIVE_PROMPT,
                        ),
                    ),
                    ImageGenProfile(
                        id="quality",
                        label="质量优先",
                        description="更高步数以获得更稳定细节（更慢）",
                        defaults=ImageGenProfileDefaults(
                            steps=35,
                            cfg_scale=7.5,
                            negative_prompt=DEFAULT_NEGATIVE_PROMPT,
                        ),
                    ),
                    ImageGenProfile(
                        id="fast",
                        label="速度优先",
                        description="更低步数以加快生成（细节可能下降）",
                        defaults=ImageGenProfileDefaults(
                            steps=18,
                            cfg_scale=6.5,
                            negative_prompt=DEFAULT_NEGATIVE_PROMPT,
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
        # Our provider-safe mapping only guarantees negative_prompt passthrough today.
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
