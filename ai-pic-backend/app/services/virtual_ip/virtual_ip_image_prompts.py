from __future__ import annotations

from app.prompts.manager import prompt_manager
from app.prompts.template_audit import build_prompt_template_audit

VIRTUAL_IP_IMAGE_VARIANT_TEMPLATE = "virtual_ip_image_variant"


def render_virtual_ip_image_variant_prompt_with_audit(
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
) -> tuple[str, dict | None]:
    """Render Virtual IP img2img prompt and return template audit when applicable."""
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
        return variant_prompt, None

    if isinstance(rendered, str) and rendered.strip():
        prompt_text = rendered.strip()
        audit = build_prompt_template_audit(template_name, variables=variables)
        return prompt_text, audit
    return variant_prompt, None


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
    prompt_text, _ = render_virtual_ip_image_variant_prompt_with_audit(
        character_name=character_name,
        variant_prompt=variant_prompt,
        character_description=character_description,
        background_story=background_story,
        style=style,
        category=category,
        style_prompt=style_prompt,
        base_prompt=base_prompt,
        template_name=template_name,
    )
    return prompt_text
