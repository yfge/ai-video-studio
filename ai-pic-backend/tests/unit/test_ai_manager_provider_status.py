from types import SimpleNamespace

from app.services.ai_manager_provider_status import (
    build_provider_status,
    update_provider_config,
)
from app.services.ai_service_manager import ProviderPriority, ProviderWeight
from app.services.providers.base import AIModelType, ModelInfo


def test_build_provider_status_uses_weight_and_model_metadata():
    provider = SimpleNamespace(
        supported_model_types=[AIModelType.TEXT_GENERATION],
        available_models=[
            ModelInfo(
                model_id="m1",
                name="Model One",
                description="test",
                model_type=AIModelType.TEXT_GENERATION,
                capabilities=["text_generation"],
            )
        ],
    )
    weight = ProviderWeight(
        provider_name="dummy",
        priority=ProviderPriority.HIGH,
        weight=2.5,
        enabled=False,
        current_requests=3,
        max_requests_per_minute=99,
    )

    status = build_provider_status({"dummy": provider}, {"dummy": weight})

    assert status["dummy"]["enabled"] is False
    assert status["dummy"]["priority"] == "HIGH"
    assert status["dummy"]["weight"] == 2.5
    assert status["dummy"]["current_requests"] == 3
    assert status["dummy"]["max_requests_per_minute"] == 99
    assert status["dummy"]["supported_model_types"] == ["text_generation"]
    assert status["dummy"]["available_models"] == [
        {
            "id": "m1",
            "name": "Model One",
            "type": "text_generation",
            "capabilities": ["text_generation"],
        }
    ]


def test_update_provider_config_creates_and_updates_weight():
    weights = {}

    update_provider_config(
        weights,
        provider_name="dummy",
        create_provider_weight=ProviderWeight,
        enabled=False,
        weight=3.0,
        priority=ProviderPriority.LOW,
        max_requests_per_minute=7,
    )

    weight = weights["dummy"]
    assert weight.provider_name == "dummy"
    assert weight.enabled is False
    assert weight.weight == 3.0
    assert weight.priority == ProviderPriority.LOW
    assert weight.max_requests_per_minute == 7
