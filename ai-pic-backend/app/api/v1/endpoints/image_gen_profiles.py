from __future__ import annotations

from app.core.middleware import get_current_active_user
from app.models.user import User
from app.schemas.image_gen_profiles import (
    ImageGenProfileDefaultsResponse,
    ImageGenProfileResponse,
    ImageGenProfilesResponse,
)
from app.services.image_gen.profiles import list_image_gen_profiles
from app.services.image_gen.types import ImageGenMode
from app.utils.model_utils import infer_provider_from_model, parse_model_and_provider
from fastapi import APIRouter, Depends, Query

router = APIRouter()


@router.get("/profiles", response_model=ImageGenProfilesResponse)
async def get_image_gen_profiles(
    model: str = Query(..., description="模型，形如 provider:model_id 或直接 model_id"),
    mode: ImageGenMode = Query(
        ImageGenMode.TEXT_TO_IMAGE, description="生成模式：text_to_image/image_to_image"
    ),
    current_user: User = Depends(get_current_active_user),
):
    _ = current_user  # auth guard

    clean_model, provider_hint = parse_model_and_provider(model)
    provider = provider_hint or (
        infer_provider_from_model(clean_model or "") if clean_model else None
    )
    provider = provider.lower() if provider else None

    profiles = list_image_gen_profiles(
        provider=provider, model_id=clean_model, mode=mode
    )
    if profiles is None:
        return ImageGenProfilesResponse(
            provider=provider,
            model_id=clean_model,
            mode=mode.value,
            default_profile_id=None,
            profiles=[],
        )

    return ImageGenProfilesResponse(
        provider=provider,
        model_id=clean_model,
        mode=mode.value,
        default_profile_id=profiles.default_profile_id,
        profiles=[
            ImageGenProfileResponse(
                id=profile.id,
                label=profile.label,
                description=profile.description,
                defaults=ImageGenProfileDefaultsResponse(
                    steps=profile.defaults.steps,
                    cfg_scale=profile.defaults.cfg_scale,
                    negative_prompt=profile.defaults.negative_prompt,
                    strength=profile.defaults.strength,
                    image_reference=profile.defaults.image_reference,
                    image_fidelity=profile.defaults.image_fidelity,
                    human_fidelity=profile.defaults.human_fidelity,
                ),
            )
            for profile in profiles.profiles
        ],
    )
