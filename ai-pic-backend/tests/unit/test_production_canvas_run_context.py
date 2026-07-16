from app.services.production_canvas.run_context import (
    canvas_run_context,
    merge_canvas_node_context_outputs,
)


def test_global_context_does_not_overwrite_scoped_media_lineage():
    outputs = merge_canvas_node_context_outputs(
        {
            "skill": "video.candidates",
            "outputs": {
                "frame_indexes": [2],
                "story_id": 60,
                "episode_id": 170,
                "script_id": 140,
                "timeline_id": 501,
                "timeline_version": 7,
                "clip_id": "clip-b",
                "selected_output_clip_id": "clip-b",
            },
        },
        {
            "story_id": 61,
            "episode_id": 175,
            "script_id": 301,
            "timeline_id": 502,
            "timeline_version": 1,
            "clip_id": "clip-a",
        },
        authoritative=True,
    )

    assert outputs["story_id"] == 60
    assert outputs["episode_id"] == 170
    assert outputs["script_id"] == 140
    assert outputs["timeline_id"] == 501
    assert outputs["timeline_version"] == 7
    assert outputs["clip_id"] == "clip-b"
    assert outputs["selected_output_clip_id"] == "clip-b"


def test_scoped_media_node_cannot_override_global_run_clip_by_node_order():
    context = canvas_run_context(
        {
            "saved_state": {
                "nodes": [
                    {
                        "skill": "timeline.render",
                        "outputs": {
                            "script_id": 301,
                            "timeline_id": 502,
                            "timeline_version": 1,
                            "clip_id": "clip-a",
                        },
                    },
                    {
                        "skill": "video.candidates",
                        "outputs": {
                            "frame_indexes": [2],
                            "script_id": 140,
                            "timeline_id": 501,
                            "timeline_version": 7,
                            "clip_id": "clip-b",
                        },
                    },
                ]
            }
        }
    )

    assert context == {
        "script_id": 301,
        "timeline_id": 502,
        "timeline_version": 1,
        "clip_id": "clip-a",
    }


def test_scoped_media_drops_marker_that_disagrees_with_its_canonical_clip():
    outputs = merge_canvas_node_context_outputs(
        {
            "skill": "video.candidates",
            "outputs": {
                "frame_indexes": [2],
                "timeline_id": 501,
                "clip_id": "clip-b",
                "selected_output_clip_id": "stale-clip",
            },
        },
        {"timeline_id": 502, "clip_id": "clip-a"},
        authoritative=True,
    )

    assert outputs["timeline_id"] == 501
    assert outputs["clip_id"] == "clip-b"
    assert "selected_output_clip_id" not in outputs
