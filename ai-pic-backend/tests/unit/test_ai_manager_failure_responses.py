from app.services import ai_manager_failure_responses as failures
from app.services.ai_manager_logging import AI_MANAGER_PROVIDER
from app.services.providers.base import AIModelType, AITaskType


def test_manager_failure_response_uses_manager_provider_and_unknown_model():
    resp = failures.manager_failure_response(
        error="no provider",
        model=None,
        task_type=AITaskType.STORY_GENERATION,
        model_type=AIModelType.TEXT_GENERATION,
    )

    assert resp.success is False
    assert resp.error == "no provider"
    assert resp.provider == AI_MANAGER_PROVIDER
    assert resp.model == "unknown"


def test_provider_prefixed_error_avoids_duplicate_provider_prefix():
    assert failures.provider_prefixed_error("boom", "openai") == "openai: boom"
    assert failures.provider_prefixed_error("openai: boom", "openai") == "openai: boom"


def test_terminal_failure_response_prefers_provider_error():
    resp = failures.terminal_failure_response(
        default_error="all failed",
        last_error="rate limited",
        last_provider="google",
        model="gemini",
        task_type=AITaskType.PORTRAIT_GENERATION,
        model_type=AIModelType.TEXT_TO_IMAGE,
    )

    assert resp.error == "google: rate limited"
    assert resp.provider == "google"
    assert resp.model == "gemini"


def test_terminal_failure_response_uses_default_without_last_error():
    resp = failures.terminal_failure_response(
        default_error="all failed",
        last_error=None,
        last_provider=None,
        model=None,
        task_type=AITaskType.VOICE_GENERATION,
        model_type=AIModelType.TEXT_TO_SPEECH,
    )

    assert resp.error == "all failed"
    assert resp.provider == AI_MANAGER_PROVIDER
    assert resp.model == "unknown"
