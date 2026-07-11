from types import SimpleNamespace

import pytest
from app.services.storyboard.video_generation_queue import _timeline_rework_contexts


def _timeline(version: int = 2):
    return SimpleNamespace(
        id=71,
        business_id="timeline-71",
        version=version,
        spec={
            "tracks": [
                {
                    "track_type": "video",
                    "clips": [{"clip_id": "stable-clip-1"}],
                }
            ]
        },
    )


def _frame(source_version: int):
    return {
        "source": {
            "timeline_id": 71,
            "timeline_version": source_version,
            "clip_id": "stable-clip-1",
        }
    }


def test_maps_stable_clip_from_an_older_timeline_version():
    contexts = _timeline_rework_contexts([_frame(1)], [0], _timeline())

    assert contexts["0"]["timeline_version"] == 2
    assert contexts["0"]["source_timeline_version"] == 1
    assert contexts["0"]["clip_id"] == "stable-clip-1"


def test_rejects_storyboard_frame_from_a_future_timeline_version():
    with pytest.raises(ValueError, match="timeline_clip_mapping_missing"):
        _timeline_rework_contexts([_frame(3)], [0], _timeline())
