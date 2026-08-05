import pytest
from tests.unit.test_story_novel_plan_execution_contract import _run_with_issues
from tests.unit.test_story_novel_plan_semantic_audit import _canon, _chapter


@pytest.mark.parametrize(
    ("action_phase", "reported_severity", "blocked"),
    [
        ("complete", "advisory", True),
        ("progress", "blocking", False),
        ("progress", "advisory", False),
    ],
)
def test_semantic_audit_classifies_action_phase_conflict_by_risk(
    action_phase, reported_severity, blocked
):
    issues = {
        "evt-ch8-1": [
            {
                "code": "action_phase_conflict",
                "severity": reported_severity,
                "message": "冻结事件只开始修渠却被标记为完工",
            }
        ]
    }
    if blocked:
        with pytest.raises(ValueError, match="不可执行.*action_phase_conflict"):
            _run_with_issues(issues, action_phase)
    else:
        chapter = _run_with_issues(issues, action_phase)[0]
        assert chapter["semantic_audit"]["status"] == "passed"


def test_audit_prompt_treats_same_chapter_end_state_as_event_completion():
    from app.services.story.story_novel_plan_semantic_audit import _audit_prompt

    prompt = _audit_prompt({}, _canon(), [], [_chapter()])

    assert "可将 action_phase 标为 complete，这不是冲突" in prompt
    assert "普通行动词与其同章结果" in prompt
    assert "不得因为 chapter_end_state 更强" not in prompt
