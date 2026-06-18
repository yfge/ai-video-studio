import json

from app.models.task import Task, TaskStatus
from app.services.task_agent_run import persist_task_agent_run
from fastapi import HTTPException
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
    import app.services.timeline_pipeline_runner as timeline_pipeline_runner

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
                "batch_index": 2,
                "batch_count": 7,
                "clip_ids": ["video_clip_009"],
                "provider": "deepseek",
                "model": "deepseek-v4-flash",
                "usage": {"completion_tokens": 12003},
                "finish_reason": "length",
                "max_tokens": 12000,
                "repair_attempts": 2,
                "prompt": "must not be persisted",
                "content": "must not be persisted",
            },
        )

    monkeypatch.setattr(
        timeline_pipeline_runner,
        "generate_dialogue_with_duration_control",
        _fake_generate_dialogue_with_duration_control,
    )
    monkeypatch.setattr(
        timeline_pipeline_runner,
        "generate_episode_audio_timeline",
        _fake_generate_episode_audio_timeline,
    )
    monkeypatch.setattr(
        timeline_pipeline_runner,
        "generate_timeline_shot_plan_from_current_version",
        _fake_generate_timeline_shot_plan_from_current_version,
    )
    _patch_session_local(monkeypatch, test_db)

    timeline_pipeline_endpoint._process_timeline_pipeline_task(
        task.id, {"script_id": script.id, "use_duration_control": True}, user.id
    )

    session = test_db()
    try:
        persist_task_agent_run(
            task_id=task.id,
            user_id=user.id,
            kind="timeline_pipeline",
            db_session=session,
        )
        refreshed = session.query(Task).filter(Task.id == task.id).first()
        assert refreshed is not None
        assert refreshed.status == TaskStatus.FAILED
        assert refreshed.error_message
        assert "timeline shot plan JSON invalid" in refreshed.error_message
        assert "流水线失败：timeline shot plan JSON invalid" in refreshed.description
        params = json.loads(refreshed.parameters)
        pipeline_error = params["pipeline_error"]
        assert pipeline_error["message"] == "timeline shot plan JSON invalid"
        assert pipeline_error["stage"] == "timeline_shot_plan"
        assert pipeline_error["batch_index"] == 2
        assert pipeline_error["clip_ids"] == ["video_clip_009"]
        assert pipeline_error["usage"] == {"completion_tokens": 12003}
        assert pipeline_error["finish_reason"] == "length"
        assert "prompt" not in pipeline_error
        assert "content" not in pipeline_error
        agent_error = params["agent_run"]["error"]
        assert agent_error["message"] == "timeline shot plan JSON invalid"
        assert agent_error["batch_count"] == 7
        assert agent_error["provider"] == "deepseek"
        assert agent_error["max_tokens"] == 12000
    finally:
        session.close()
