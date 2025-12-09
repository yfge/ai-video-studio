import pytest

from app.services.ai_service import AIService


@pytest.mark.asyncio
async def test_story_outline_falls_back_to_mock_when_ai_manager_unavailable():
    service = AIService()
    # 强制关闭 AI 管理器，模拟无可用提供商的场景
    service.ai_manager = None

    result = await service.generate_story_outline(
        title="Fallback Story",
        genre="drama",
        characters=[{"name": "Hero", "description": "A curious hero"}],
        theme="fallback path",
    )

    assert result is not None
    assert result["generation_method"] == "ai_fallback"
    assert result["provider_used"] == "fallback"
    assert result.get("prompt")
    assert result.get("normalized")
    assert result["normalized"].get("premise")
