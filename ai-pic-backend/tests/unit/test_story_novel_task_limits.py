from app.services.task_worker import story_novel_generate_task


def test_outline_driven_novel_task_has_no_fixed_worker_timeout():
    assert story_novel_generate_task.soft_time_limit == 0
    assert story_novel_generate_task.time_limit == 0
