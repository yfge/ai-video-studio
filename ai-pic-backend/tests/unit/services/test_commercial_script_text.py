import pytest
from app.services.ai.script_text import build_script_text


@pytest.mark.unit
def test_build_script_text_uses_commercial_vertical_format():
    text = build_script_text(
        scenes=[
            {
                "scene_number": 1,
                "slug_line": "内. 客厅 - 夜",
                "summary": "开场钩子：林雪当众甩出账本。",
            }
        ],
        dialogues=[
            {
                "scene_number": 1,
                "character": "林雪",
                "content": "账本在这，你还要装吗？",
                "emotion": "冷笑",
            },
            {
                "scene_number": 1,
                "character": "陈默",
                "content": "你怎么会有它？",
                "emotion": "慌乱",
            },
        ],
        stage_directions=[
            {
                "scene_number": 1,
                "timing": "intro",
                "content": "【音效】砰！门被踹开，众人回头。",
                "type": "sfx",
            },
            {
                "scene_number": 1,
                "timing": "outro",
                "content": "【特写】账本最后一页露出陌生签名。",
                "type": "camera",
            },
        ],
        format_type="screenplay",
        language="zh-CN",
        episode_number=1,
        template_style="commercial_vertical_drama",
        target_chars_per_episode=1300,
    )

    assert text.startswith("第1集")
    assert "1-1 内. 客厅 - 夜" in text
    assert "人物： 林雪、陈默" in text
    assert "▲【音效】砰！门被踹开" in text
    assert "林雪(冷笑)：账本在这，你还要装吗？" in text
    assert "▲【特写】账本最后一页露出陌生签名。" in text
