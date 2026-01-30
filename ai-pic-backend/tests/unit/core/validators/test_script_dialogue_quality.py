from app.core.validators.script_dialogue_quality import (
    find_reused_short_dialogues,
    looks_like_writer_note,
    validate_scene_dialogues,
)


def test_looks_like_writer_note_detects_meta_instruction():
    assert looks_like_writer_note("明白，这里可以突出冲突或情绪。") is True
    assert looks_like_writer_note("注：此处建议加强冲突。") is True


def test_looks_like_writer_note_allows_in_world_suggestion():
    assert looks_like_writer_note("我建议你现在就走。") is False


def test_find_reused_short_dialogues_flags_cross_scene_duplicates():
    dialogues = [
        {"scene_number": 1, "character": "老拐", "content": "等一下……让我再确认一下。"},
        {"scene_number": 2, "character": "老拐", "content": "等一下……让我再确认一下。"},
        {"scene_number": 1, "character": "阿盖儿", "content": "明白，我们继续。"},
        {"scene_number": 3, "character": "阿盖儿", "content": "明白，我们继续。"},
    ]
    reps = find_reused_short_dialogues(dialogues, max_chars=40, min_repeats=2)
    assert "等一下让我再确认一下" in reps
    assert "明白我们继续" in reps


def test_validate_scene_dialogues_reports_quality_issues():
    repeated = {"明白我们继续"}
    scene_dialogues = [
        {"scene_number": 1, "character": "阿盖儿", "content": "明白，我们继续。"},
        {
            "scene_number": 1,
            "character": "阿盖儿",
            "content": "明白，这里可以突出冲突或情绪。",
        },
    ]
    issues = validate_scene_dialogues(
        scene_dialogues, min_lines=2, repeated_short_norms=repeated
    )
    codes = {i.code for i in issues}
    assert "writer_note" in codes
    assert "reused_filler" in codes


def test_validate_scene_dialogues_enforces_min_lines():
    issues = validate_scene_dialogues(
        [{"scene_number": 1, "character": "A", "content": "你好"}],
        min_lines=2,
        repeated_short_norms=set(),
    )
    assert any(i.code == "too_few_lines" for i in issues)
