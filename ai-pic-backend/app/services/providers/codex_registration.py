"""Runtime registration for the Codex provider."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.config import settings
from app.services.ai.manager import ProviderPriority, ProviderWeight

from .base import ProviderConfig
from .codex_auth import DEFAULT_CODEX_AUTH_PATH
from .codex_provider import CodexProvider


def resolve_codex_auth_path() -> Path:
    raw = settings.CODEX_AUTH_PATH
    return Path(raw).expanduser() if raw else DEFAULT_CODEX_AUTH_PATH


def install_codex_provider(ai_manager: Any) -> None:
    """Install Codex provider into an initialized AI manager when auth exists."""
    if ai_manager is None:
        return
    if not settings.CODEX_AUTH_PATH:
        return
    auth_path = resolve_codex_auth_path()
    if not auth_path.is_file():
        return

    provider_config = ProviderConfig(
        name="codex",
        api_key=str(auth_path),
        base_url=settings.CODEX_RESPONSES_URL,
        timeout=120.0,
        default_model=settings.CODEX_DEFAULT_MODEL,
    )
    ai_manager.provider_classes["codex"] = CodexProvider
    ai_manager.config.providers["codex"] = provider_config
    ai_manager.config.provider_weights["codex"] = ProviderWeight(
        provider_name="codex",
        weight=0.9,
        priority=ProviderPriority.HIGH,
        enabled=True,
        max_requests_per_minute=60,
    )
    ai_manager.providers["codex"] = CodexProvider(provider_config)
