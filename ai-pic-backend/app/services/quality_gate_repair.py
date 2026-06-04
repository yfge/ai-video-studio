from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.services.providers.deepseek_strict_json import (
    deepseek_v4_pro_strict_json_kwargs,
)
from app.utils.json_utils import extract_json_block


async def repair_quality_gate_payload(
    *,
    ai_manager: Any,
    kind: str,
    payload: Dict[str, Any],
    quality_gate: Dict[str, Any],
    schema: Dict[str, Any],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
) -> Optional[Dict[str, Any]]:
    if not ai_manager:
        return None

    prompt = (
        f"The generated {kind} JSON failed strict quality gate validation.\n"
        "Repair the JSON while preserving the same schema and story intent.\n"
        "Return strict JSON only, no markdown.\n\n"
        f"quality_gate:\n{json.dumps(quality_gate, ensure_ascii=False)[:6000]}\n\n"
        f"payload:\n{json.dumps(payload, ensure_ascii=False)[:12000]}"
    )
    response = await ai_manager.generate_text(
        prompt=prompt,
        temperature=min(0.3, temperature),
        model=model,
        prefer_provider=prefer_provider,
        json_schema=schema,
        system_prompt="You repair narrative JSON. Return strict JSON only.",
        stream=False,
        **deepseek_v4_pro_strict_json_kwargs(
            prefer_provider=prefer_provider,
            model=model,
        ),
    )
    if not getattr(response, "success", False):
        return None
    if isinstance(response.data, dict):
        return response.data
    parsed = extract_json_block(
        response.data if isinstance(response.data, str) else str(response.data)
    )
    return parsed if isinstance(parsed, dict) else None
