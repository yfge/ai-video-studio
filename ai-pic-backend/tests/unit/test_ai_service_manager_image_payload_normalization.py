import base64
import hashlib

import pytest
from app.core.logging import get_logger
from app.services.ai_service_manager import AIServiceManager


@pytest.mark.asyncio
async def test_convert_base64_images_to_oss_normalizes_dict_items(monkeypatch):
    monkeypatch.setattr(
        "app.services.storage.oss_service.oss_service", None, raising=False
    )

    manager = AIServiceManager.__new__(AIServiceManager)
    manager.logger = get_logger()

    images = [
        {"index": 0, "url": "https://example.com/a.png"},
        {"url": "https://example.com/b.png"},
        "https://example.com/c.png",
    ]

    result = await manager._convert_base64_images_to_oss(images)

    assert result == [
        "https://example.com/a.png",
        "https://example.com/b.png",
        "https://example.com/c.png",
    ]


@pytest.mark.asyncio
async def test_convert_base64_images_to_oss_uploads_data_url(monkeypatch):
    import importlib
    from unittest.mock import AsyncMock

    fake_oss = type(
        "FakeOSS",
        (),
        {
            "upload_file_content": AsyncMock(
                return_value={
                    "success": True,
                    "file_url": "https://cdn.example.com/generated.png",
                }
            )
        },
    )()

    oss_module = importlib.import_module("app.services.storage.oss_service")
    monkeypatch.setattr(oss_module, "oss_service", fake_oss, raising=False)

    manager = AIServiceManager.__new__(AIServiceManager)
    manager.logger = get_logger()

    raw = b"hello"
    b64 = base64.b64encode(raw).decode("ascii")
    images = [f"data:image/png;base64,{b64}"]

    result = await manager._convert_base64_images_to_oss(
        images, prefix="ai-generated/test"
    )

    assert result == ["https://cdn.example.com/generated.png"]
    call_kwargs = fake_oss.upload_file_content.call_args.kwargs
    assert call_kwargs["file_type"] == "image"
    assert call_kwargs["prefix"] == "ai-generated/test"
    assert call_kwargs["metadata"]["sha256"] == hashlib.sha256(raw).hexdigest()
