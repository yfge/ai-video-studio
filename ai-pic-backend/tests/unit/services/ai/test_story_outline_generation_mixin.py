from __future__ import annotations

import logging
from typing import Any

import app.services.ai.story_outline as story_outline_module
import pytest
from app.schemas.story_seed import StorySeedEnvelope
from app.services.ai.story_outline import StoryOutlineMixin
from app.services.story.story_outline_normalizer import normalize_story_outline_strict


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_story_outline_production_uses_story_seed_contract(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    async def _fake_generate_with_repair(**kwargs: Any) -> dict[str, Any]:
        captured["base_prompt"] = kwargs["base_prompt"]
        captured["pydantic_model"] = kwargs["pydantic_model"]
        return {
            "content": '{"story_seed":{"schema":"story_seed_v1"}}',
            "normalized": {
                "story_seed": {
                    "schema": "story_seed_v1",
                    "title": "T",
                    "premise": "Hero发现证据被抢。",
                    "outline": "Hero追查证据并面对阻力。",
                    "protagonists": [
                        {
                            "virtual_ip_business_id": "vip-hero",
                            "initial_state": "尚不知道黑手身份",
                        }
                    ],
                    "world_constraints": [],
                    "central_conflict": "证据争夺",
                    "ending_direction": None,
                    "target_audience": None,
                    "content_constraints": [],
                },
            },
            "validation_errors": [],
            "repair_attempts": [],
            "first_attempt": {
                "provider_used": "mock-provider",
                "model_used": "mock-model",
                "usage": {},
            },
        }

    monkeypatch.setattr(
        story_outline_module, "generate_with_repair", _fake_generate_with_repair
    )

    class _Svc(StoryOutlineMixin):
        def __init__(self) -> None:
            self.story_agent = None
            self.ai_manager = object()
            self.logger = logging.getLogger(__name__)

    service = _Svc()
    result = await service.generate_story_outline(
        title="T",
        genre="drama",
        characters=[{"business_id": "vip-hero", "name": "Hero", "description": "lead"}],
        story_format="short_drama",
        generation_mode="production",
    )

    assert result is not None
    assert result["generation_mode"] == "production"
    assert result["production_mode"] is True
    assert captured["pydantic_model"] is StorySeedEnvelope
    prompt = captured["base_prompt"]
    assert "story_seed_v1" in prompt
    assert "只建立后续小说创作所需的初始条件" in prompt
    assert "不得生成前三集结构" in prompt
    assert "structured_story_contract" not in prompt


@pytest.mark.unit
def test_story_outline_normalizer_accepts_story_seed_envelope() -> None:
    payload = {
        "story_seed": {
            "schema": "story_seed_v1",
            "title": "T",
            "premise": "P",
            "outline": "O",
            "protagonists": [
                {"virtual_ip_business_id": "vip-hero", "initial_state": "S"}
            ],
            "world_constraints": [],
            "central_conflict": "C",
            "ending_direction": None,
            "target_audience": None,
            "content_constraints": [],
        }
    }

    normalized = normalize_story_outline_strict(
        {"normalized": payload, "production_mode": True}
    )

    assert normalized == payload
