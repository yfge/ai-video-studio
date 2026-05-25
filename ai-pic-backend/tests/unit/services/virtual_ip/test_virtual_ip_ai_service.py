import json
from types import SimpleNamespace

import pytest
from app.services.virtual_ip_ai_service import (
    VIRTUAL_IP_CONTENT_FILL_MODEL,
    VIRTUAL_IP_CONTENT_FILL_PROVIDER,
    VirtualIPAIService,
)


class RecordingAIManager:
    def __init__(self) -> None:
        self.calls = []

    async def generate_text(self, **kwargs):
        self.calls.append(kwargs)
        if "只输出中文提示词" in kwargs["prompt"]:
            return SimpleNamespace(
                data="电影感肖像，冷色调办公室光线，职业装，面部细节清晰",
                model=kwargs["model"],
                usage={"total_tokens": 12},
            )

        payload = {
            "detailed_description": "短发女性合伙人，职业装，神情冷静克制。",
            "background_story": "从基层一路成长为合伙人，习惯用事实解决危机。",
            "personality": "理性、克制、重情义",
            "skills": "谈判、风控、快速决策",
            "relationships": "与团队保持严格但可靠的伙伴关系",
            "lifestyle": "高强度工作，重视长期承诺",
            "signature_traits": "黑色西装与冷静目光",
            "development_potential": "适合现代商战与复仇成长线",
            "suggested_tags": ["现代", "金融", "合伙人"],
        }
        return SimpleNamespace(
            data=json.dumps(payload, ensure_ascii=False),
            model=kwargs["model"],
            usage={"total_tokens": 88},
        )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_virtual_ip_content_fill_uses_deepseek_v4_flash():
    service = VirtualIPAIService()
    manager = RecordingAIManager()
    service.ai_manager = manager

    result = await service.generate_complete_ip_with_details(
        name="林静",
        basic_info="35岁上海金融行业女性合伙人",
    )
    style_prompt = await service.generate_style_prompt(
        name="林静",
        description=result["content"]["description"],
        biography=result["content"]["biography"],
    )

    assert result["generation_details"]["model"] == VIRTUAL_IP_CONTENT_FILL_MODEL
    assert style_prompt == "电影感肖像，冷色调办公室光线，职业装，面部细节清晰"
    assert [call["model"] for call in manager.calls] == [
        VIRTUAL_IP_CONTENT_FILL_MODEL,
        VIRTUAL_IP_CONTENT_FILL_MODEL,
    ]
    assert [call["prefer_provider"] for call in manager.calls] == [
        VIRTUAL_IP_CONTENT_FILL_PROVIDER,
        VIRTUAL_IP_CONTENT_FILL_PROVIDER,
    ]
