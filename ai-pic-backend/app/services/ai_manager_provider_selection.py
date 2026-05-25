"""Provider rate-limit and selection helpers for AI manager."""

from __future__ import annotations

import random
import time
from typing import Any, Optional


def check_rate_limit(provider_weights: dict[str, Any], provider_name: str) -> bool:
    weight = provider_weights.get(provider_name)
    if not weight:
        return True

    current_time = time.time()
    if current_time - weight.last_reset_time > 60:
        weight.current_requests = 0
        weight.last_reset_time = current_time

    return weight.current_requests < weight.max_requests_per_minute


def select_provider(
    available_providers: list[str],
    provider_weights: dict[str, Any],
    *,
    enable_load_balancing: bool,
    default_priority_value: int,
    prefer_provider: str | None = None,
) -> Optional[str]:
    if not available_providers:
        return None
    if prefer_provider and prefer_provider in available_providers:
        return prefer_provider
    if not enable_load_balancing:
        return select_by_priority(
            available_providers,
            provider_weights,
            default_priority_value=default_priority_value,
        )
    return select_by_weight(available_providers, provider_weights)


def select_by_priority(
    providers: list[str],
    provider_weights: dict[str, Any],
    *,
    default_priority_value: int,
) -> str:
    priority_map: dict[int, list[str]] = {}
    for name in providers:
        weight = provider_weights.get(name)
        priority = weight.priority.value if weight else default_priority_value
        priority_map.setdefault(priority, []).append(name)

    highest_priority = min(priority_map.keys())
    return random.choice(priority_map[highest_priority])


def select_by_weight(providers: list[str], provider_weights: dict[str, Any]) -> str:
    weights = []
    for name in providers:
        weight = provider_weights.get(name)
        weights.append(weight.weight if weight else 1.0)

    total_weight = sum(weights)
    if total_weight == 0:
        return random.choice(providers)

    cursor = random.uniform(0, total_weight)
    cumulative = 0
    for index, weight in enumerate(weights):
        cumulative += weight
        if cursor <= cumulative:
            return providers[index]

    return providers[-1]


def update_request_count(provider_weights: dict[str, Any], provider_name: str) -> None:
    weight = provider_weights.get(provider_name)
    if weight:
        weight.current_requests += 1
