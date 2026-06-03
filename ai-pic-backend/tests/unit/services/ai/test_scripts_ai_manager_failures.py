from __future__ import annotations

from typing import Any

import pytest
from app.services.ai.scripts_ai_manager import ScriptManagerMixin
from app.services.script.beat_contract_generation import BeatContractGenerationError


class _DummyResponse:
    def __init__(self) -> None:
        self.success = False
        self.data = None
        self.provider = "deepseek"
        self.model = "deepseek-v4-pro"
        self.error = "provider timeout"
        self.usage = {}


class _DummyManager:
    async def generate_text(self, **_: Any):
        return _DummyResponse()


class _DummyService(ScriptManagerMixin):
    def __init__(self) -> None:
        self.ai_manager = _DummyManager()

    def _build_script_text(self, *_args: Any, **_kwargs: Any) -> str:
        return "ASSEMBLED"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_call_ai_manager_script_preserves_explicit_provider_failure():
    service = _DummyService()

    with pytest.raises(BeatContractGenerationError) as exc_info:
        await service._call_ai_manager_script(
            episode={
                "duration_minutes": 1,
                "scenes": [
                    {
                        "scene_number": 1,
                        "slug_line": "INT. Room - day",
                        "summary": "opening",
                    },
                    {
                        "scene_number": 2,
                        "slug_line": "INT. Hall - day",
                        "summary": "turn",
                    },
                ],
            },
            story={"title": "T"},
            format_type="short_video",
            language="zh",
            dialogue_style="natural",
            scene_detail_level="medium",
            additional_requirements=None,
            style_preferences=None,
            model="deepseek-v4-pro",
            prefer_provider="deepseek",
            temperature=0.7,
        )

    assert exc_info.value.code == "beat_contract_failed"
    assert str(exc_info.value) == "beat_contract_failed: provider timeout"
