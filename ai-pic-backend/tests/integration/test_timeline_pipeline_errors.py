from fastapi import HTTPException

from app.models.task import Task, TaskStatus
from tests.integration.test_timeline_pipeline_import_api import (
    _create_script_with_scenes,
    _create_task,
    _create_user,
    _patch_session_local,
)


def test_process_timeline_pipeline_persists_http_exception_detail(
    db_session, test_db, monkeypatch
):
    import app.api.v1.endpoints.scripts.timeline_pipeline as timeline_pipeline_endpoint

    user = _create_user(db_session, username="pipeline_http_error_admin")
    script, scene_ids = _create_script_with_scenes(db_session, user=user)
    task = _create_task(db_session, user_id=user.id)

    async def _fake_generate_dialogue_with_duration_control(
        db_session,  # noqa: ANN001
        **_: object,
    ) -> dict:
        return {"success": True, "statistics": {"duration_ratio": 1.0}}

    async def _fake_generate_episode_audio_timeline(
        db_session,  # noqa: ANN001
        **kwargs: object,
    ) -> dict:
        return {
            "script_id": kwargs["script"].id,
            "episode_audio": {
                "oss_url": "https://cdn.example.com/pipeline.mp3",
                "duration_seconds": 1.2,
                "version": 7,
            },
            "beats": [
                {
                    "scene_id": scene_ids[0],
                    "scene_number": 1,
                    "beat_id": 501,
                    "beat_type": "dialogue",
                    "text": "hello",
                    "start_ms": 0,
                    "end_ms": 1200,
                }
            ],
        }

    async def _fake_generate_timeline_shot_plan_from_current_version(
        db_session,  # noqa: ANN001
        timeline,
        *,
        user_id: int,
    ):
        raise HTTPException(
            status_code=502,
            detail={
                "message": "timeline shot plan JSON invalid",
                "errors": [{"loc": ["shots", 1, "plot"], "msg": "too short"}],
            },
        )

    monkeypatch.setattr(
        timeline_pipeline_endpoint,
        "generate_dialogue_with_duration_control",
        _fake_generate_dialogue_with_duration_control,
    )
    monkeypatch.setattr(
        timeline_pipeline_endpoint,
        "generate_episode_audio_timeline",
        _fake_generate_episode_audio_timeline,
    )
    monkeypatch.setattr(
        timeline_pipeline_endpoint,
        "generate_timeline_shot_plan_from_current_version",
        _fake_generate_timeline_shot_plan_from_current_version,
    )
    _patch_session_local(monkeypatch, test_db)

    timeline_pipeline_endpoint._process_timeline_pipeline_task(
        task.id, {"script_id": script.id, "use_duration_control": True}, user.id
    )

    session = test_db()
    try:
        refreshed = session.query(Task).filter(Task.id == task.id).first()
        assert refreshed is not None
        assert refreshed.status == TaskStatus.FAILED
        assert refreshed.error_message
        assert "timeline shot plan JSON invalid" in refreshed.error_message
        assert "流水线失败：timeline shot plan JSON invalid" in refreshed.description
    finally:
        session.close()
