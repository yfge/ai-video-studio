from types import SimpleNamespace

from app.schemas.production_canvas import ProductionCanvasSkillExecuteRequest
from app.services.production_canvas import media_execution


def test_video_execution_persists_the_effective_default_frame(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        media_execution,
        "load_script",
        lambda _db, _user, _script_id: SimpleNamespace(id=140, episode_id=175),
    )
    monkeypatch.setattr(
        media_execution,
        "resolve_canvas_candidate_branch",
        lambda *_args, **_kwargs: None,
    )

    def queue(*_args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            task=SimpleNamespace(id=901, status=SimpleNamespace(value="pending")),
            reused=False,
            frame_count=1,
            selected_candidate_count=1,
            timeline_id=501,
            timeline_version=7,
            mapped_clip_count=1,
        )

    monkeypatch.setattr(
        media_execution,
        "queue_storyboard_video_generation_task",
        queue,
    )
    response = media_execution.execute_storyboard_video_candidates(
        SimpleNamespace(),
        SimpleNamespace(id=1),
        ProductionCanvasSkillExecuteRequest(
            prompt="生成默认首个镜头",
            skill="video.candidates",
            script_id=140,
        ),
    )

    assert captured["frame_indexes"] == [0]
    assert response.skill_result.outputs["frame_indexes"] == [0]
