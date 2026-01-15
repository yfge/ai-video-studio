from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.story_structure.environment_image_generation import (
    generate_environment_images,
)
from app.services.story_structure.environment_image_requests import (
    EnvironmentTextToImageRequest,
)


class _DummyDB:
    def commit(self) -> None:
        return None

    def refresh(self, _obj: object) -> None:
        return None


class _DummyAIManager:
    def __init__(self) -> None:
        self.last_kwargs: dict | None = None

    async def generate_image(self, **kwargs):  # type: ignore[no-untyped-def]
        self.last_kwargs = kwargs
        return SimpleNamespace(
            success=True,
            data={"images": ["http://example.com/generated.png"]},
            error=None,
            provider="google",
            model="gemini-2.0-flash-exp",
            metadata={},
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_environment_images_passes_txt2img_reference_images(monkeypatch):
    import app.services.story_structure.environment_image_generation as module

    monkeypatch.setattr(module, "_get_backend_base", lambda: "http://backend.local")

    async def _fake_persist_environment_images(**_kwargs):  # type: ignore[no-untyped-def]
        return ["/ai-generated/environments/image/saved.png"]

    monkeypatch.setattr(module, "persist_environment_images", _fake_persist_environment_images)

    ai_manager = _DummyAIManager()
    ai_service = SimpleNamespace(ai_manager=ai_manager)

    env = SimpleNamespace(
        id=1,
        name="Test Env",
        description="desc",
        tags=[],
        category="indoor",
        extra_metadata={},
        reference_images=[],
    )

    req = EnvironmentTextToImageRequest(
        prompt="extra",
        model="google:gemini-2.0-flash-exp",
        count=1,
        size=None,
        aspect_ratio=None,
        style="realistic",
        style_preset_id=None,
        style_spec=None,
        generation_profile=None,
        seed=None,
        steps=None,
        cfg_scale=None,
        negative_prompt=None,
        reference_images=["/ai-generated/environments/image/example.png"],
    )

    saved = await generate_environment_images(
        db=_DummyDB(),
        env=env,
        request=req,
        ai_service=ai_service,
        require_upload=False,
    )

    assert saved == ["/ai-generated/environments/image/saved.png"]
    assert ai_manager.last_kwargs is not None
    assert ai_manager.last_kwargs["reference_images"] == [
        "http://backend.local/ai-generated/environments/image/example.png"
    ]

