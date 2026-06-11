"""Integration: dynamic prompt bundles flow through the storyboard image task."""

from app.models.script import Script
from app.models.task import Task, TaskStatus, TaskType
from tests.factories import ScriptFactory, UserFactory, setup_factories


def _patch_session_local(monkeypatch, session_factory):
    import app.core.database as db_module

    monkeypatch.setattr(db_module, "SessionLocal", session_factory)


def _create_storyboard_task(db_session, user_id: int) -> Task:
    task = Task(
        title="Storyboard image generation",
        task_type=TaskType.IMAGE_GENERATION,
        status=TaskStatus.PENDING,
        user_id=user_id,
    )
    db_session.add(task)
    db_session.commit()
    return task


def test_dynamic_prompt_bundle_overrides_compiled_prompt_and_persists(
    db_session, test_db, mock_ai_service, monkeypatch
):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(
        extra_metadata={
            "storyboard": {
                "frames": [
                    {
                        "scene_number": 1,
                        "description": "主角醉步入场",
                        "shot_type": "中远景",
                    }
                ]
            }
        }
    )
    task = _create_storyboard_task(db_session, user.id)
    _patch_session_local(monkeypatch, test_db)

    import app.api.v1.endpoints.storyboard.image_task_processor as sb_image_task
    import app.services.storyboard.dynamic_prompt as dynamic_prompt_pkg
    import app.services.storyboard.storyboard_image_generation as sb_gen

    monkeypatch.setattr(sb_image_task, "ai_service", mock_ai_service)

    bundle = {
        "input_sha": "test-sha",
        "image_prompt": "LLM dynamic image prompt",
        "start_keyframe_prompt": "LLM start prompt",
        "end_keyframe_prompt": "LLM end prompt",
        "version": 1,
    }

    def _fake_build_bundles(script_obj, frames, target_indexes, ref_ctx, **kwargs):
        for idx in target_indexes:
            frames[idx]["llm_prompt_bundle"] = bundle
        return {idx: bundle for idx in target_indexes}

    monkeypatch.setattr(
        dynamic_prompt_pkg, "build_dynamic_prompt_bundles", _fake_build_bundles
    )

    captured = {}

    async def _fake_generate_storyboard_image_urls(**kwargs):  # noqa: ANN001
        captured["prompt"] = kwargs.get("prompt")
        return {
            "urls": ["https://example.com/generated.png"],
            "provider": "mock-provider",
            "model": "mock-model",
            "style_spec": None,
            "style_spec_resolution": None,
            "image_gen": {},
        }

    monkeypatch.setattr(
        sb_gen, "generate_storyboard_image_urls", _fake_generate_storyboard_image_urls
    )

    sb_image_task._process_storyboard_image_task(
        task.id,
        script.id,
        [0],
        keyframe_mode="single",
    )

    session = test_db()
    try:
        refreshed_task = session.query(Task).filter_by(id=task.id).first()
        assert refreshed_task.status == TaskStatus.COMPLETED
        refreshed_script = session.query(Script).filter_by(id=script.id).first()
        frames = refreshed_script.extra_metadata["storyboard"]["frames"]
        compiled = frames[0]["storyboard_prompt_v2"]
        assert compiled["image_prompt"] == "LLM dynamic image prompt"
        assert compiled["start_keyframe_prompt"] == "LLM start prompt"
        assert compiled["prompt_source"] == "llm_dynamic"
        assert frames[0]["llm_prompt_bundle"]["input_sha"] == "test-sha"
        assert "LLM dynamic image prompt" in captured["prompt"]
    finally:
        session.close()
