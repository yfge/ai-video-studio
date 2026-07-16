from app.services.task_result_context import build_task_result_context


def test_task_result_context_prefers_structured_agent_result() -> None:
    context = build_task_result_context(
        task_id=88,
        parameters={
            "episode_id": "3",
            "env_id": 5,
            "agent_run": {
                "result_ref": {
                    "story_id": 2,
                    "episode_id": 3,
                    "script_id": 4,
                    "timeline_id": 6,
                    "timeline_version": 7,
                    "clip_ids": ["clip-1"],
                }
            },
        },
        result_file_path="script:4",
    )

    assert context == {
        "task_id": 88,
        "environment_id": 5,
        "story_id": 2,
        "episode_id": 3,
        "script_id": 4,
        "timeline_id": 6,
        "timeline_version": 7,
        "clip_id": "clip-1",
    }


def test_task_result_context_understands_legacy_timeline_path() -> None:
    context = build_task_result_context(
        task_id=9,
        parameters={"script_id": 4},
        result_file_path="timeline_videos:12:v3:2",
    )

    assert context == {
        "task_id": 9,
        "script_id": 4,
        "timeline_id": 12,
        "timeline_version": 3,
    }


def test_task_result_context_keeps_structured_timeline_over_legacy_path() -> None:
    context = build_task_result_context(
        task_id=11,
        parameters={
            "agent_run": {"result_ref": {"timeline_id": 20, "timeline_version": 4}}
        },
        result_file_path="timeline:12:v3",
    )

    assert context == {
        "task_id": 11,
        "timeline_id": 20,
        "timeline_version": 4,
    }


def test_task_result_context_reads_production_canvas_context() -> None:
    context = build_task_result_context(
        task_id=90,
        parameters={
            "requested_asset_ids": {
                "virtual_ip_id": 2,
                "environment_id": 3,
            },
            "resolved_context": {
                "virtual_ip_id": 4,
                "environment_id": 5,
                "story_id": 6,
                "episode_id": 7,
                "script_id": 8,
                "timeline_id": 9,
                "timeline_version": 10,
                "clip_id": "clip-11",
            },
        },
        result_file_path="production_canvas:run-12",
    )

    assert context == {
        "task_id": 90,
        "virtual_ip_id": 4,
        "environment_id": 5,
        "story_id": 6,
        "episode_id": 7,
        "script_id": 8,
        "timeline_id": 9,
        "timeline_version": 10,
        "clip_id": "clip-11",
    }


def test_canvas_run_context_does_not_revive_legacy_descendants() -> None:
    context = build_task_result_context(
        task_id=93,
        parameters={
            "kind": "production_canvas_run",
            "requested_asset_ids": {
                "story_id": 60,
                "episode_id": 170,
                "script_id": 140,
            },
            "resolved_context": {"story_id": 61},
            "agent_run": {
                "result_ref": {
                    "story_id": 60,
                    "episode_id": 170,
                    "script_id": 140,
                    "timeline_id": 501,
                    "timeline_version": 7,
                    "clip_id": "old-clip",
                }
            },
        },
        result_file_path="timeline:501:v7",
    )

    assert context == {"task_id": 93, "story_id": 61}


def test_task_result_context_clears_old_clip_for_new_multi_clip_timeline() -> None:
    context = build_task_result_context(
        task_id=91,
        parameters={
            "resolved_context": {
                "story_id": 6,
                "episode_id": 7,
                "script_id": 8,
                "timeline_id": 9,
                "timeline_version": 1,
                "clip_id": "old-clip",
            },
            "agent_run": {
                "result_ref": {
                    "timeline_id": 10,
                    "timeline_version": 2,
                    "clip_ids": ["new-clip-1", "new-clip-2"],
                }
            },
        },
        result_file_path="timeline:9:v1",
    )

    assert context == {
        "task_id": 91,
        "story_id": 6,
        "episode_id": 7,
        "script_id": 8,
        "timeline_id": 10,
        "timeline_version": 2,
    }


def test_task_result_context_reads_plural_asset_and_clip_alias_outputs() -> None:
    context = build_task_result_context(
        task_id=92,
        parameters={
            "virtual_ip_ids": [84],
            "environment_ids": [13],
            "timeline_ids": [70],
            "timeline_versions": [6],
            "placed_timeline_clip_id": "placed-clip",
        },
        result_file_path=None,
    )

    assert context == {
        "task_id": 92,
        "virtual_ip_id": 84,
        "environment_id": 13,
        "timeline_id": 70,
        "timeline_version": 6,
        "clip_id": "placed-clip",
    }


def test_task_result_context_does_not_guess_between_multiple_episodes() -> None:
    context = build_task_result_context(
        task_id=10,
        parameters={},
        result_file_path="episodes:21,22",
    )

    assert context == {"task_id": 10}
