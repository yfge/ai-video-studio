from __future__ import annotations

from dataclasses import dataclass

from .coerce import clean_str
from .negative_prompts import VIRTUAL_IP_NEGATIVE_PROMPT_EXTRA, merge_negative_prompt
from .normalize_helpers import (
    normalize_cfg_scale,
    normalize_seed,
    normalize_steps,
    normalize_strength,
    normalize_unit_float,
)
from .profiles import resolve_image_gen_profile
from .types import ImageGenAudit, ImageGenDomain, ImageGenMode, ImageGenRequest


@dataclass(frozen=True, slots=True)
class ResolvedProfileParams:
    generation_profile: str | None
    seed: int | None
    steps: int | None
    cfg_scale: float | None
    negative_prompt: str | None
    strength: float | None
    image_reference: str | None
    image_fidelity: float | None
    human_fidelity: float | None


def resolve_profile_params(
    *,
    provider: str | None,
    model_id: str | None,
    request: ImageGenRequest,
    audit: ImageGenAudit,
) -> ResolvedProfileParams:
    requested_profile = clean_str(request.generation_profile)
    profile = resolve_image_gen_profile(
        provider=provider,
        model_id=model_id,
        mode=request.mode,
        requested_profile=requested_profile,
    )
    generation_profile = profile.id if profile else None
    if profile and requested_profile and profile.id != requested_profile:
        audit.warnings.append(
            f"unknown generation_profile '{requested_profile}', using '{profile.id}'"
        )
    if requested_profile and profile is None:
        audit.warnings.append(
            f"generation_profile '{requested_profile}' ignored (unsupported provider/model)"
        )
    if profile and not requested_profile:
        audit.defaults_applied["generation_profile"] = profile.id

    seed = normalize_seed(request.seed, audit=audit)

    steps_input = request.steps
    if steps_input is None and profile and profile.defaults.steps is not None:
        steps_input = profile.defaults.steps
        audit.defaults_applied["steps"] = steps_input
    steps = normalize_steps(steps_input, audit=audit)
    if steps is None and request.steps is not None and profile and profile.defaults.steps:
        audit.warnings.append("invalid steps; falling back to generation_profile")
        audit.defaults_applied["steps"] = profile.defaults.steps
        steps = normalize_steps(profile.defaults.steps, audit=audit)

    cfg_input = request.cfg_scale
    if cfg_input is None and profile and profile.defaults.cfg_scale is not None:
        cfg_input = profile.defaults.cfg_scale
        audit.defaults_applied["cfg_scale"] = cfg_input
    cfg_scale = normalize_cfg_scale(cfg_input, audit=audit)
    if (
        cfg_scale is None
        and request.cfg_scale is not None
        and profile
        and profile.defaults.cfg_scale is not None
    ):
        audit.warnings.append("invalid cfg_scale; falling back to generation_profile")
        audit.defaults_applied["cfg_scale"] = profile.defaults.cfg_scale
        cfg_scale = normalize_cfg_scale(profile.defaults.cfg_scale, audit=audit)

    negative_prompt_input = clean_str(request.negative_prompt)
    used_profile_negative_prompt = False
    if (
        negative_prompt_input is None
        and profile
        and profile.defaults.negative_prompt is not None
    ):
        negative_prompt_input = clean_str(profile.defaults.negative_prompt)
        if negative_prompt_input is not None:
            used_profile_negative_prompt = True
            audit.defaults_applied["negative_prompt"] = negative_prompt_input
    negative_prompt = negative_prompt_input

    if used_profile_negative_prompt and request.domain == ImageGenDomain.VIRTUAL_IP:
        negative_prompt = merge_negative_prompt(
            negative_prompt, VIRTUAL_IP_NEGATIVE_PROMPT_EXTRA
        )
        audit.defaults_applied["negative_prompt_virtual_ip"] = (
            VIRTUAL_IP_NEGATIVE_PROMPT_EXTRA
        )

    strength = None
    image_reference = None
    image_fidelity = None
    human_fidelity = None

    if request.mode == ImageGenMode.IMAGE_TO_IMAGE:
        strength_input = request.strength
        if strength_input is None and profile and profile.defaults.strength is not None:
            strength_input = profile.defaults.strength
            audit.defaults_applied["strength"] = strength_input
        strength = normalize_strength(strength_input, audit=audit)

        image_reference_input = clean_str(request.image_reference)
        if (
            image_reference_input is None
            and profile
            and profile.defaults.image_reference is not None
        ):
            image_reference_input = clean_str(profile.defaults.image_reference)
            if image_reference_input is not None:
                audit.defaults_applied["image_reference"] = image_reference_input
        image_reference = image_reference_input

        if (
            provider == "keling"
            and image_reference is None
            and (model_id or "").strip().lower()
            in {"kling-v1-5", "kling-image-v1-5"}
        ):
            image_reference = "subject"
            audit.defaults_applied["image_reference"] = image_reference

        image_fidelity_input = request.image_fidelity
        if (
            image_fidelity_input is None
            and profile
            and profile.defaults.image_fidelity is not None
        ):
            image_fidelity_input = profile.defaults.image_fidelity
            audit.defaults_applied["image_fidelity"] = image_fidelity_input
        image_fidelity = normalize_unit_float(
            image_fidelity_input,
            audit=audit,
            field_name="image_fidelity",
        )

        human_fidelity_input = request.human_fidelity
        if (
            human_fidelity_input is None
            and profile
            and profile.defaults.human_fidelity is not None
        ):
            human_fidelity_input = profile.defaults.human_fidelity
            audit.defaults_applied["human_fidelity"] = human_fidelity_input
        human_fidelity = normalize_unit_float(
            human_fidelity_input,
            audit=audit,
            field_name="human_fidelity",
        )
    elif request.strength is not None:
        audit.dropped_fields.append("strength")
        audit.warnings.append("strength ignored for text_to_image")

    return ResolvedProfileParams(
        generation_profile=generation_profile,
        seed=seed,
        steps=steps,
        cfg_scale=cfg_scale,
        negative_prompt=negative_prompt,
        strength=strength,
        image_reference=image_reference,
        image_fidelity=image_fidelity,
        human_fidelity=human_fidelity,
    )

