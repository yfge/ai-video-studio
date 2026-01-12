import pytest
from app.core.logging import get_logger
from app.services.ai_service_manager import AIServiceManager


@pytest.mark.asyncio
async def test_convert_base64_images_to_oss_normalizes_dict_items(monkeypatch):
    monkeypatch.setattr("app.services.storage.oss_service.oss_service", None, raising=False)

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

