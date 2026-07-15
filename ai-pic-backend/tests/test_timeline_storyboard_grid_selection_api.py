import json

from app.models.task import Task
from tests.test_timeline_storyboard_grid_api import (
    _append_video_clips,
    _bootstrap_episode,
    _create_timeline,
    _timeline_spec,
)


def test_timeline_clip_storyboard_auto_selects_panel_count_when_omitted(
    client,
    db_session,
    monkeypatch,
):
    dispatched = {}
    monkeypatch.setattr(
        "app.services.storyboard.grid_storyboard_sheet_service."
        "dispatch_grid_storyboard_sheet_task",
        lambda task, payload, current_user: dispatched.update(payload=payload),
    )
    _, episode, script = _bootstrap_episode(db_session)
    timeline = _create_timeline(
        client,
        episode,
        script,
        _append_video_clips(_timeline_spec(episode, script)),
    )

    response = client.post(
        "/api/v1/timelines/"
        f"{timeline['id']}/clips/video_scene_001_beat_001_001/storyboard/generate",
        json={"expected_version": timeline["version"]},
    )

    assert response.status_code == 200, response.text
    params = json.loads(db_session.get(Task, response.json()["task_id"]).parameters)
    assert params["panel_count"] == 2
    assert params["panel_selection"] == {
        "panel_count": 2,
        "mode": "auto",
        "visual_beat_count": 0,
        "duration_ms": 1200,
        "reason": "duration_fallback_no_structured_beats",
    }
    assert len(params["panels"]) == 2
    assert dispatched["payload"]["panel_selection"] == params["panel_selection"]
