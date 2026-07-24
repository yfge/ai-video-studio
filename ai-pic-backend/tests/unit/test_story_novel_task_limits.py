from app.services.task_worker import (
    STORY_NOVEL_GENERATE_SOFT_TIME_LIMIT,
    STORY_NOVEL_GENERATE_TIME_LIMIT,
    story_novel_generate_task,
)


def test_outline_driven_novel_task_uses_explicit_longform_window():
    assert story_novel_generate_task.soft_time_limit == (
        STORY_NOVEL_GENERATE_SOFT_TIME_LIMIT
    )
    assert story_novel_generate_task.time_limit == STORY_NOVEL_GENERATE_TIME_LIMIT
    assert story_novel_generate_task.soft_time_limit > 1500
    assert story_novel_generate_task.time_limit > 1800
