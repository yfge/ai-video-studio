"""Provider status and configuration helpers for AI service manager."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


def build_provider_status(
    providers: dict[str, Any],
    provider_weights: dict[str, Any],
) -> dict[str, Any]:
    """Build the public provider status payload."""
    status: dict[str, Any] = {}
    for name, provider in providers.items():
        weight = provider_weights.get(name)
        status[name] = {
            "enabled": weight.enabled if weight else True,
            "priority": weight.priority.name if weight else "MEDIUM",
            "weight": weight.weight if weight else 1.0,
            "current_requests": weight.current_requests if weight else 0,
            "max_requests_per_minute": (
                weight.max_requests_per_minute if weight else 60
            ),
            "supported_model_types": [
                model_type.value for model_type in provider.supported_model_types
            ],
            "available_models": [
                {
                    "id": model.model_id,
                    "name": model.name,
                    "type": model.model_type.value,
                    "capabilities": model.capabilities,
                }
                for model in provider.available_models
            ],
        }
    return status


def update_provider_config(
    provider_weights: dict[str, Any],
    *,
    provider_name: str,
    create_provider_weight: Callable[[str], Any],
    enabled: bool | None = None,
    weight: float | None = None,
    priority: Any | None = None,
    max_requests_per_minute: int | None = None,
) -> None:
    """Update or create provider weight configuration."""
    if provider_name not in provider_weights:
        provider_weights[provider_name] = create_provider_weight(provider_name)

    weight_config = provider_weights[provider_name]

    if enabled is not None:
        weight_config.enabled = enabled
    if weight is not None:
        weight_config.weight = weight
    if priority is not None:
        weight_config.priority = priority
    if max_requests_per_minute is not None:
        weight_config.max_requests_per_minute = max_requests_per_minute
