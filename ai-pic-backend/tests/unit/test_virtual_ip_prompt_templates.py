import pytest
from app.prompts.manager import prompt_manager
from app.prompts.templates import PromptTemplate


def test_virtual_ip_creation_template_includes_constraints():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.VIRTUAL_IP_CREATION.value,
        {
            "name": "测试角色",
            "description": "35岁上海金融行业女性合伙人，外表冷静利落，内心重情义；整体写实现代；拒绝夸张中二语气。",
            "age": None,
            "gender": None,
            "personality_traits": None,
            "style_preference": None,
            "target_audience": None,
            "content_type": None,
        },
    )

    assert "重要约束" in prompt
    assert "不要在任何字段中提及“虚拟IP" in prompt
    assert "不要以“测试角色是一个" in prompt


def test_virtual_ip_style_prompt_template_renders():
    prompt = prompt_manager.render_prompt(
        PromptTemplate.VIRTUAL_IP_STYLE_PROMPT.value,
        {
            "name": "测试角色",
            "description": "短发，职业装，冷静利落",
            "biography": "金融行业合伙人，克制理性但重情义",
            "image_category": "portrait",
        },
    )

    assert "只输出中文提示词" in prompt
    assert "虚拟 ip" not in prompt.lower()


@pytest.mark.asyncio
async def test_virtual_ip_style_prompt_template_is_registered():
    # PromptTemplate 枚举存在即代表模板名已注册；此处避免被重构误删
    assert PromptTemplate.VIRTUAL_IP_STYLE_PROMPT.value == "virtual_ip_style_prompt"
