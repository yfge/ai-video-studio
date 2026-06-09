import pytest
from app.services.script_missing_parts import populate_dialogues_and_stage_if_missing


@pytest.mark.unit
def test_no_missing_returns_original_lists():
    scenes = [{"scene_number": 1, "summary": "场景1"}]
    dialogues = [{"scene_number": 1, "character": "A", "content": "你好"}]
    stage = [{"scene_number": 1, "timing": "mid", "content": "动作", "type": "action"}]

    out_dialogues, out_stage = populate_dialogues_and_stage_if_missing(
        scenes, dialogues, stage, story=None
    )

    assert out_dialogues == dialogues
    assert out_stage == stage


@pytest.mark.unit
def test_missing_dialogue_adds_narration_from_summary():
    scenes = [
        {"scene_number": 1, "summary": "场景1摘要"},
        {"scene_number": 2, "summary": "场景2摘要"},
    ]
    dialogues = [{"scene_number": 2, "character": "A", "content": "你好"}]
    stage = [{"scene_number": 2, "timing": "mid", "content": "动作", "type": "action"}]

    out_dialogues, out_stage = populate_dialogues_and_stage_if_missing(
        scenes, dialogues, stage, story=None
    )

    # Scene 1 gets a narration fallback (no generic fake dialogue)
    scene1 = [d for d in out_dialogues if d.get("scene_number") == 1]
    assert len(scene1) == 1
    assert scene1[0].get("character") == "旁白"
    assert scene1[0].get("content") == "场景1摘要"
    assert scene1[0].get("fallback") is True

    # Stage directions are also filled for missing scenes
    scene1_stage = [s for s in out_stage if s.get("scene_number") == 1]
    assert len(scene1_stage) == 1
    assert scene1_stage[0].get("type") == "action"
    assert scene1_stage[0].get("fallback") is True


@pytest.mark.unit
def test_missing_dialogue_extracts_quoted_scene_lines_before_narration():
    scenes = [
        {
            "scene_number": 1,
            "characters": ["老拐", "文闻"],
            "description": (
                "老拐坐在电脑前，屏幕滚动着代码。他微微一笑：'又一个自动化完成了。'"
                "警报声大作，'什么情况？'他皱眉自言自语。"
            ),
        }
    ]

    out_dialogues, _ = populate_dialogues_and_stage_if_missing(
        scenes, [], [], story=None
    )

    assert [
        (item.get("character"), item.get("content"), item.get("fallback"))
        for item in out_dialogues
    ] == [
        ("老拐", "又一个自动化完成了。", None),
        ("老拐", "什么情况？", None),
    ]


@pytest.mark.unit
def test_missing_dialogue_keeps_speakers_when_quotes_are_adjacent():
    scenes = [
        {
            "scene_number": 3,
            "characters": ["老拐", "文闻"],
            "description": (
                "文闻注意到了老拐的代码屏幕。'这些是什么？'她指着一串数据问。"
                "老拐耸肩：'生存算法，计算每个人的价值。'"
                "文闻皱眉：'你是在给人贴标签吗？'"
                "老拐无奈：'效率至上。'"
                "文闻坚定：'我会留下，帮你加点人性化。'"
            ),
        }
    ]

    out_dialogues, _ = populate_dialogues_and_stage_if_missing(
        scenes, [], [], story=None
    )

    assert [(item.get("character"), item.get("content")) for item in out_dialogues] == [
        ("文闻", "这些是什么？"),
        ("老拐", "生存算法，计算每个人的价值。"),
        ("文闻", "你是在给人贴标签吗？"),
        ("老拐", "效率至上。"),
        ("文闻", "我会留下，帮你加点人性化。"),
    ]
