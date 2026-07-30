from app.services.story.story_novel_execution_normalization import (
    normalize_execution_aliases,
)


def test_execution_aliases_preserve_the_single_format_repair_for_real_errors():
    executions = [
        {"action_phase": "activity"},
        {"action_phase": "reaction"},
    ]

    normalize_execution_aliases(executions)

    assert [item["action_phase"] for item in executions] == ["progress", "instant"]
