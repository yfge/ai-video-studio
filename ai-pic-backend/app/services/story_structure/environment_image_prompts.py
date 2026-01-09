from __future__ import annotations

import re

from app.models.story_structure import Environment
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate

DEFAULT_ENV_VARIANT_EXTRA_PROMPT = (
    "Generate stylistically consistent variants based on this environment reference"
)


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def compose_environment_prompt(env: Environment, extra: str | None = None) -> str:
    """Render environment image prompt via the unified PromptManager templates."""
    prompt_value = (extra or "").strip() or (env.description or "").strip() or env.name
    if not prompt_value:
        prompt_value = "Environment scene with clear spatial layout and lighting cues"

    tags_value = ", ".join([t for t in (env.tags or []) if t]) or None
    description_value = (env.description or "").strip() or None
    if description_value and description_value.lower() == prompt_value.lower():
        description_value = None

    variables = {
        "environment_name": env.name or f"environment-{env.id}",
        "category": env.category or "indoor",
        "tags": tags_value,
        "description": description_value,
        "prompt": prompt_value,
        "additional_prompts": None,
    }
    try:
        rendered = prompt_manager.render_prompt(
            PromptTemplate.ENVIRONMENT_IMAGE.value, variables
        )
        return _compact_text(rendered)
    except Exception:
        parts = [
            f"Environment: {variables['environment_name']}",
            f"Category: {variables['category']}",
        ]
        if tags_value:
            parts.append(f"Tags: {tags_value}")
        if description_value:
            parts.append(f"Description: {description_value}")
        parts.append(prompt_value)
        return " | ".join([p for p in parts if p])
