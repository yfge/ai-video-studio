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
