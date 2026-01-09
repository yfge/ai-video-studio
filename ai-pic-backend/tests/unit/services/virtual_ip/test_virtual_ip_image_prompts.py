import pytest
from app.services.virtual_ip.virtual_ip_image_prompts import (
    render_virtual_ip_image_variant_prompt,
)


@pytest.mark.unit
def test_render_virtual_ip_image_variant_prompt_renders_template():
    rendered = render_virtual_ip_image_variant_prompt(
        character_name="小雅",
        character_description="22岁女性，银色短发，黑色高领毛衣",
        variant_prompt="背面照，全身照，保持同一人物特征",
        style="realistic",
        category="portrait",
        style_prompt="studio lighting",
    )

    assert "Virtual IP Variant:" in rendered
    assert "小雅" in rendered
    assert "背面照" in rendered


@pytest.mark.unit
def test_render_virtual_ip_image_variant_prompt_falls_back_when_template_missing():
    fallback = render_virtual_ip_image_variant_prompt(
        character_name="小雅",
        variant_prompt="背面照",
        template_name="__missing_template__",
    )
    assert fallback == "背面照"
