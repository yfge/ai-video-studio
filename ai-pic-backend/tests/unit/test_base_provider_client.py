import pytest

from app.services.providers.base import (
    AIModelType,
    AITaskType,
    BaseProvider,
    ProviderConfig,
    AIResponse,
)


class DummyClient:
    def __init__(self):
        self.is_closed = False


class DummyProvider(BaseProvider):
    def __init__(self):
        super().__init__(ProviderConfig(name="dummy"))
        self.init_calls = 0

    async def _initialize_client(self):
        self.init_calls += 1
        self._client = DummyClient()

    @property
    def supported_model_types(self):
        return []

    @property
    def available_models(self):
        return []

    async def generate_text(self, prompt: str, model: str = None, **kwargs):
        return AIResponse(
            success=True,
            data=prompt,
            error=None,
            provider=self.name,
            model=model or "unknown",
            task_type=AITaskType.STORY_GENERATION,
            model_type=AIModelType.TEXT_GENERATION,
        )

    async def generate_image(self, prompt: str, model: str = None, **kwargs):
        return await self.generate_text(prompt, model, **kwargs)


@pytest.mark.asyncio
async def test_get_client_reinitializes_when_closed():
    provider = DummyProvider()
    client1 = await provider.get_client()
    assert provider.init_calls == 1
    assert client1 is provider._client

    provider._client.is_closed = True
    client2 = await provider.get_client()
    assert provider.init_calls == 2
    assert client2 is provider._client
    assert client2 is not client1
