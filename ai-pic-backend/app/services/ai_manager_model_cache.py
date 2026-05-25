"""Model-list cache helpers for the AI service manager."""

from __future__ import annotations

from time import monotonic
from typing import Any, Dict, List

from app.services.providers.base import AIModelType

ModelListCache = dict[str, tuple[float, List[Dict[str, Any]]]]


def model_cache_key(source: str, model_type: AIModelType | str | None) -> str:
    type_key = (
        model_type.value if isinstance(model_type, AIModelType) else model_type or "all"
    )
    return f"{source}:{type_key}"


def get_cached_models(
    cache: ModelListCache,
    *,
    cache_ttl: float,
    cache_key: str,
) -> list[dict[str, Any]] | None:
    if cache_ttl <= 0 or cache_key not in cache:
        return None
    cached_at, cached = cache[cache_key]
    if monotonic() - cached_at >= cache_ttl:
        return None
    return list(cached)


def store_cached_models(
    cache: ModelListCache,
    *,
    cache_ttl: float,
    cache_key: str,
    models: list[dict[str, Any]],
) -> None:
    if cache_ttl <= 0:
        return
    cache[cache_key] = (monotonic(), list(models))
