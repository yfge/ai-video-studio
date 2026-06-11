"""ModelInfo definitions for the Codex provider."""

from __future__ import annotations

from typing import List

from .base import AIModelType, ModelInfo

DEFAULT_CODEX_TEXT_MODEL = "gpt-5.4"
CODEX_IMAGE_MODEL_ID = "gpt-image-2"


def build_codex_models(default_model: str) -> List[ModelInfo]:
    model_ids = [default_model]
    if DEFAULT_CODEX_TEXT_MODEL not in model_ids:
        model_ids.append(DEFAULT_CODEX_TEXT_MODEL)
    models = [
        ModelInfo(
            model_id=model_id,
            name=f"ChatGPT {model_id} (Codex)",
            description=(
                "ChatGPT subscription model via the Codex responses endpoint"
            ),
            model_type=AIModelType.TEXT_GENERATION,
            capabilities=["text_generation", "analysis", "code_generation"],
            metadata={"auth": "codex_cli", "endpoint": "codex_responses"},
        )
        for model_id in model_ids
    ]
    models.append(
        ModelInfo(
            model_id=CODEX_IMAGE_MODEL_ID,
            name="GPT Image 2 (Codex)",
            description=(
                "GPT Image via the ChatGPT image_generation tool, billed to "
                "the ChatGPT subscription"
            ),
            model_type=AIModelType.TEXT_TO_IMAGE,
            supported_formats=["png"],
            capabilities=["text_to_image", "reference_image"],
            metadata={"auth": "codex_cli", "endpoint": "codex_responses"},
        )
    )
    return models
