from __future__ import annotations

from app.services.production_canvas.run_context import canvas_run_context


def _baseline() -> dict:
    return {
        "virtual_ip_id": 84,
        "environment_id": 13,
        "story_id": 61,
        "episode_id": 174,
        "script_id": 144,
        "timeline_id": 70,
        "timeline_version": 6,
        "clip_id": "old-clip",
        "task_id": 6357,
    }


def test_canvas_run_context_clears_stale_clip_when_timeline_changes():
    context = canvas_run_context(
        {
            "requested_asset_ids": _baseline(),
            "saved_state": {
                "nodes": [
                    {
                        "outputs": {
                            "timeline_id": 71,
                            "timeline_version": 1,
                        }
                    }
                ]
            },
        }
    )

    assert context == {
        "virtual_ip_id": 84,
        "environment_id": 13,
        "story_id": 61,
        "episode_id": 174,
        "script_id": 144,
        "timeline_id": 71,
        "timeline_version": 1,
    }


def test_canvas_run_context_keeps_story_when_only_environment_changes():
    context = canvas_run_context(
        {
            "requested_asset_ids": _baseline(),
            "saved_state": {"nodes": [{"outputs": {"environment_id": 14}}]},
        }
    )

    assert context == {
        "virtual_ip_id": 84,
        "environment_id": 14,
        "story_id": 61,
        "episode_id": 174,
        "script_id": 144,
        "timeline_id": 70,
        "timeline_version": 6,
        "clip_id": "old-clip",
    }


def test_canvas_run_context_reads_plural_asset_outputs_as_new_lineage():
    context = canvas_run_context(
        {
            "requested_asset_ids": _baseline(),
            "saved_state": {
                "nodes": [
                    {
                        "outputs": {
                            "virtual_ip_ids": [85],
                            "environment_ids": [14],
                        }
                    }
                ]
            },
        }
    )

    assert context == {"virtual_ip_id": 85, "environment_id": 14}


def test_canvas_run_context_treats_persisted_resolved_context_as_authoritative():
    baseline = _baseline()
    context = canvas_run_context(
        {
            "requested_asset_ids": baseline,
            "saved_state": {"nodes": [{"outputs": {"timeline_id": 71}}]},
            "resolved_context": baseline,
        }
    )

    assert context == baseline
