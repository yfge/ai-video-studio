import httpx
import pytest
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    OPENAI_API_KEY: str = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = TestSettings()
OPENAI_API_KEY = settings.OPENAI_API_KEY


@pytest.mark.asyncio
async def test_openai_dalle_api():
    """测试OpenAI DALL-E API直接调用"""

    if not OPENAI_API_KEY:
        pytest.skip("OPENAI_API_KEY not configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/images/generations",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "dall-e-3",
                "prompt": "A simple test image",
                "n": 1,
                "size": "1024x1024",
                "response_format": "b64_json",
            },
            timeout=60.0,
        )

    assert response.status_code == 200, f"API failed: {response.text}"
    result = response.json()
    assert "data" in result
    assert "b64_json" in result["data"][0]
    assert len(result["data"][0]["b64_json"]) > 1000  # base64数据应该很长
