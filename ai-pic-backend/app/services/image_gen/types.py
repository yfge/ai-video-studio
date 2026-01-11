from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence


class ImageGenDomain(str, Enum):
    VIRTUAL_IP = "virtual_ip"
    ENVIRONMENT = "environment"
    STORYBOARD = "storyboard"


class ImageGenMode(str, Enum):
    TEXT_TO_IMAGE = "text_to_image"
    IMAGE_TO_IMAGE = "image_to_image"


@dataclass(slots=True)
class ImageGenAudit:
    """Track normalization decisions for reproducibility/debugging."""

    warnings: list[str] = field(default_factory=list)
    dropped_fields: list[str] = field(default_factory=list)
    defaults_applied: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ImageGenRequest:
    """Raw image-generation request as collected by endpoints/workers."""

    domain: ImageGenDomain
    mode: ImageGenMode
    prompt: str | None

    model: str | None = None
    prefer_provider: str | None = None
    generation_profile: str | None = None

    style: str | None = None
    style_preset_id: str | None = None
    style_spec: Any | None = None

    size: str | None = None
    aspect_ratio: str | None = None
    width: int | None = None
    height: int | None = None

    count: int | None = None

    seed: int | None = None
    steps: int | None = None
    cfg_scale: float | None = None
    negative_prompt: str | None = None
    strength: float | None = None
    image_reference: str | None = None
    image_fidelity: float | None = None
    human_fidelity: float | None = None

    base_image: str | None = None
    reference_images: Sequence[str] = ()
    labeled_references: Any | None = None

    backend_base: str | None = None


@dataclass(slots=True)
class ImageGenNormalized:
    """Normalized request ready to call AIServiceManager."""

    domain: ImageGenDomain
    mode: ImageGenMode

    provider: str | None
    model_id: str | None
    generation_profile: str | None

    prompt: str
    style: str
    style_preset_id: str | None
    style_spec: Any | None

    size: str | None
    aspect_ratio: str | None
    width: int
    height: int
    count: int

    seed: int | None
    steps: int | None
    cfg_scale: float | None
    negative_prompt: str | None
    strength: float | None
    image_reference: str | None
    image_fidelity: float | None
    human_fidelity: float | None

    base_image_url: str | None
    extra_images: list[str]

    audit: ImageGenAudit
