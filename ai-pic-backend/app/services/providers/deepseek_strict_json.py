from __future__ import annotations

from typing import Any

from app.services.providers.deepseek_models import DEEPSEEK_V4_PRO_MODEL


def deepseek_v4_pro_strict_json_kwargs(
    *,
    prefer_provider: str | None,
    model: str | None,
) -> dict[str, Any]:
    if (prefer_provider or "").lower() != "deepseek":
        return {}
    if (model or "").lower() != DEEPSEEK_V4_PRO_MODEL:
        return {}
    return {"thinking": {"type": "disabled"}}
