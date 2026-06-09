from app.services.audio.dialogue_processing.audio_dialogue_filter import (
    repair_scene_dialogues_for_audio,
    should_treat_dialogue_as_action_for_audio,
    split_audio_dialogues_and_action_blocks,
)
from app.services.audio.dialogue_processing.prose_dialogue_splitter import (
    sanitize_stage_directions_for_audio,
    split_prose_dialogue_block,
)


def test_split_prose_dialogue_block_extracts_quoted_dialogues_with_speakers() -> None:
    alias_to_canonical = {"文闻": "文闻", "老拐": "老拐"}
    text = (
        "文闻震惊地后退半步：“你……你怎么知道我在写小说？还知道我有瓶颈？” "
        "老拐指了指她的电脑：“你死机前，屏幕残留的界面是写作软件的编辑窗口。"
        "另外，我刚才在调试脚本时，监控到公共Wi-Fi上有一个终端持续向云端同步一个大型文档，"
        "但近一小时内的数据增量极小。这是典型的内容创作者遇到‘卡文’时的网络行为模式。” "
        "文闻脸色发白，但“卡文”这个词精准戳中了她的痛点。她强作镇定：“那又怎样？"
        "创作需要灵感，需要情感，不是冷冰冰的数据分析！” "
        "老拐：“所以你会卡在这里。系统化的梳理可以解决这个问题。你的‘感觉’不可靠，"
        "但逻辑和数据可靠。”"
    )

    parts = split_prose_dialogue_block(text, alias_to_canonical=alias_to_canonical)
    assert [p["character"] for p in parts] == ["文闻", "老拐", "文闻", "老拐"]
    assert parts[0]["content"].startswith("你……你怎么知道")
    assert all(p["content"] != "卡文" for p in parts)


def test_split_prose_dialogue_block_skips_ui_screen_text_quotes() -> None:
    alias_to_canonical = {"文闻": "文闻", "老拐": "老拐"}
    text = (
        "文闻抱臂：“行啊，我倒要看看你的算法有多厉害。” "
        "老拐连接上文闻的电脑，开始运行修复程序，并同时启动了一个数据提取脚本，"
        "屏幕上代码滚动，显示“正在提取并分析文档结构数据……”"
    )

    parts = split_prose_dialogue_block(text, alias_to_canonical=alias_to_canonical)
    assert [p["character"] for p in parts] == ["文闻"]
    assert all("正在提取并分析" not in p["content"] for p in parts)


def test_repair_scene_dialogues_for_audio_splits_narrator_prose_block() -> None:
    alias_to_canonical = {"文闻": "文闻", "老拐": "老拐"}
    dialogues = [
        {
            "character": "旁白",
            "content": (
                "文闻：“你说你能帮我……优化它，是真的吗？” "
                "老拐点头：“真的。我的算法可以优化你的大纲结构。”"
            ),
        }
    ]

    repaired = repair_scene_dialogues_for_audio(
        dialogues, alias_to_canonical=alias_to_canonical
    )
    assert [d["character"] for d in repaired] == ["文闻", "老拐"]
    assert repaired[0]["content"].startswith("你说你能帮我")


def test_split_prose_dialogue_block_handles_chinese_single_quotes() -> None:
    alias_to_canonical = {"李总": "李总", "苏晴": "苏晴"}
    text = "李总追问：‘有具体标的吗？’ 苏晴回答：‘比如，科讯科技。’"

    parts = split_prose_dialogue_block(text, alias_to_canonical=alias_to_canonical)

    assert [p["character"] for p in parts] == ["李总", "苏晴"]
    assert [p["content"] for p in parts] == ["有具体标的吗？", "比如，科讯科技。"]


def test_sanitize_stage_directions_removes_ascii_single_quoted_dialogue() -> None:
    cleaned = sanitize_stage_directions_for_audio(
        [
            {
                "scene_number": 1,
                "content": "老拐抬头：'什么情况？' 他迅速切换屏幕。",
            }
        ]
    )

    assert cleaned[0]["content"] == "老拐抬头： 他迅速切换屏幕。"


def test_split_audio_dialogues_moves_fallback_narrator_prose_to_action() -> None:
    dialogues = [
        {
            "character": "旁白",
            "scene_number": 3,
            "fallback": True,
            "fallback_reason": "missing_dialogues",
            "content": (
                "冲突升级：面试现场。女主坐在长桌一侧。" "李总追问：‘有具体标的吗？’"
            ),
        }
    ]

    repaired, action_blocks = split_audio_dialogues_and_action_blocks(
        dialogues,
        alias_to_canonical={},
    )

    assert repaired == []
    assert action_blocks == [
        {
            "type": "action",
            "timing": "mid",
            "content": dialogues[0]["content"],
            "scene_number": 3,
            "source": "dialogue_fallback",
        }
    ]
    assert should_treat_dialogue_as_action_for_audio(dialogues[0]) is True
