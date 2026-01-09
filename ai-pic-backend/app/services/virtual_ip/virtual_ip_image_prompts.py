from __future__ import annotations

from app.prompts.manager import prompt_manager

VIRTUAL_IP_IMAGE_VARIANT_TEMPLATE = "virtual_ip_image_variant"


def render_virtual_ip_image_variant_prompt(
    *,
    character_name: str,
    variant_prompt: str,
    character_description: str | None = None,
    background_story: str | None = None,
    style: str | None = None,
    category: str | None = None,
    style_prompt: str | None = None,
    base_prompt: str | None = None,
    template_name: str = VIRTUAL_IP_IMAGE_VARIANT_TEMPLATE,
) -> str:
    """Render Virtual IP img2img prompt via PromptManager (fallbacks to variant_prompt)."""
    variables = {
        "character_name": character_name,
        "variant_prompt": variant_prompt,
        "character_description": character_description,
        "background_story": background_story,
        "style": style,
        "category": category,
        "style_prompt": style_prompt,
        "base_prompt": base_prompt,
    }

    try:
        rendered = prompt_manager.render_prompt(template_name, variables)
    except Exception:
        return variant_prompt

    if isinstance(rendered, str) and rendered.strip():
        return rendered.strip()
    return variant_prompt
