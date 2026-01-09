from unittest.mock import AsyncMock, patch

import pytest
from app.services.story.story_novel_export_planner import generate_zhihu_plan_compact


@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_zhihu_plan_compact_falls_back_when_chapters_missing():
    story_payload = {
        "title": "程序员之我家掉下来个？林妹妹？七仙女？不！是个锅盖～～～～",
        "episodes": [
            {
                "episode_number": 1,
                "title": "开端",
                "summary": "主角在加班时遇到离奇事件，生活被彻底打乱。",
                "plot_points": ["锅盖从天而降", "主角决定追查来源"],
            }
        ],
    }

    with patch(
        "app.services.story.story_novel_export_planner.generate_story_novel_text",
        new=AsyncMock(return_value="{}"),
    ):
        plan, chapters = await generate_zhihu_plan_compact(
            story_payload=story_payload,
            target_words=18000,
            chapter_total=3,
            model_id=None,
            prefer_provider=None,
            system_prompt="system",
        )

    assert isinstance(plan, dict)
    assert len(chapters) == 3
    assert [ch.get("chapter_number") for ch in chapters] == [1, 2, 3]
    assert all(ch.get("cliffhanger_hint") for ch in chapters)
