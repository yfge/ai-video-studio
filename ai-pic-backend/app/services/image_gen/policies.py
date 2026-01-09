from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .types import ImageGenDomain, ImageGenRequest


@dataclass(frozen=True, slots=True)
class ImageGenPolicy:
    """Domain-specific normalization rules."""

    domain: ImageGenDomain
    allow_style_spec: bool = True

    def apply(self, request: ImageGenRequest) -> dict[str, Any]:
        """Return field overrides to apply before normalization."""
        if self.domain == ImageGenDomain.ENVIRONMENT:
            return {
                "style_preset_id": None,
                "style_spec": None,
            }
        return {}


def get_policy(domain: ImageGenDomain) -> ImageGenPolicy:
    if domain == ImageGenDomain.ENVIRONMENT:
        return ImageGenPolicy(domain=domain, allow_style_spec=False)
    return ImageGenPolicy(domain=domain, allow_style_spec=True)
