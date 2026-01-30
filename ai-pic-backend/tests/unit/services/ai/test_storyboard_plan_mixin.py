import pytest
from app.schemas.generation import StoryboardPlanScene
from app.services.ai.storyboard_plan import StoryboardPlanMixin


class _DummyResponse:
    def __init__(self, *, success: bool, data: str):
        self.success = success
        self.data = data
        self.provider = "deepseek"
        self.model = "deepseek-chat"
        self.usage = {}


class _DummyManager:
    def __init__(self, response: _DummyResponse):
        self._response = response

    async def generate_text(self, **_: object):
        return self._response


class _DummyService(StoryboardPlanMixin):
    def __init__(self, response: _DummyResponse):
        self.ai_manager = _DummyManager(response)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_storyboard_plan_mixin_coerces_ad_snippet_string_into_object():
    response = _DummyResponse(
        success=True,
        data=(
            "```json\n"
            "{\n"
            '  "frames": [\n'
            "    {\n"
            '      "scene_number": 1,\n'
            '      "shot_type": "中景",\n'
            '      "camera_movement": "固定",\n'
            '      "composition": "三分法",\n'
            '      "description": "测试画面描述",\n'
            '      "duration_seconds": 3,\n'
            '      "ai_prompt": "test prompt",\n'
            '      "hook_tag": "hook",\n'
            '      "ad_snippet": "投流钩子一句话",\n'
            '      "reference_images": "https://example.com/ref.png"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "```\n"
        ),
    )

    service = _DummyService(response)
    frames = await service.generate_storyboard_from_plan_for_scene(
        script={"scenes": [{"description": "scene"}]},
        scene_plan=StoryboardPlanScene.model_validate(
            {
                "scene_number": 1,
                "target_frames": 1,
                "frames": [],
            }
        ),
        model="deepseek-chat",
        prefer_provider="deepseek",
        temperature=0.7,
        max_frames=1,
    )

    assert frames is not None
    assert frames[0]["scene_number"] == 1
    assert frames[0]["reference_images"] == ["https://example.com/ref.png"]
    assert frames[0]["ad_snippet"]["hook"] == "投流钩子一句话"
