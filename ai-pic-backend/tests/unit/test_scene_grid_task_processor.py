"""Integration: scene grid sheet/video task processors persist results."""

from __future__ import annotations

from types import SimpleNamespace

import anyio

from app.models.script import Script
from app.models.task import Task, TaskStatus, TaskType
from tests.factories import ScriptFactory, UserFactory, setup_factories


class FakeRefContext:
    def __init__(self):
        self.scene_by_number = {}
        self.scene_char_ids = {}
        self.vip_map = {}
        self.char_image_map = {}
        self.name_to_vip_id = {}
        self.env_images_by_scene = {1: ["https://example.com/env.png"]}


def _create_task(db_session, user_id: int, task_type=TaskType.IMAGE_GENERATION) -> Task:
    task = Task(
        title="Scene grid",
        task_type=task_type,
        status=TaskStatus.PENDING,
        user_id=user_id,
    )
    db_session.add(task)
    db_session.commit()
    return task


def _fake_ai_service():
    async def _persist(**kwargs):
        return {"oss_url": "https://oss.example.com/grid.png"}

    return SimpleNamespace(ai_manager=None, _persist_generated_image=_persist)


def test_scene_grid_sheet_task_persists_grid(db_session, monkeypatch):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(
        scenes=[{"scene_number": 1, "location": "酒馆外", "description": "醉态迎敌"}],
        extra_metadata={
            "storyboard": {
                "frames": [
                    {"scene_number": 1, "description": "醉步入场", "duration_seconds": 1.0},
                    {"scene_number": 1, "description": "仰头喝酒", "duration_seconds": 0.9},
                    {"scene_number": 2, "description": "其他场景"},
                ]
            }
        },
    )
    task = _create_task(db_session, user.id)

    import app.services.ai_service as ai_service_module
    import app.services.storyboard.scene_grid.processor as processor
    import app.services.storyboard.storyboard_image_generation as sb_gen

    monkeypatch.setattr(ai_service_module, "ai_service", _fake_ai_service())
    monkeypatch.setattr(
        processor, "load_ref_context", lambda db, script, script_id: FakeRefContext()
    )

    captured = {}

    async def _fake_generate(**kwargs):
        captured["prompt"] = kwargs.get("prompt")
        captured["refs"] = kwargs.get("refs")
        return {
            "urls": ["https://provider.example.com/raw.png"],
            "provider": "mock",
            "model": "mock-image",
        }

    monkeypatch.setattr(sb_gen, "generate_storyboard_image_urls", _fake_generate)

    payload = {
        "script_id": script.id,
        "scene_number": 1,
        "grid_size": 12,
        "aspect_ratio": "16:9",
        "character_refs": [],
        "environment_refs": [],
    }
    anyio.run(processor.process_scene_grid_sheet_task, db_session, task.id, payload, user.id)

    db_session.expire_all()
    refreshed_task = db_session.query(Task).filter_by(id=task.id).first()
    assert refreshed_task.status == TaskStatus.COMPLETED
    refreshed = db_session.query(Script).filter_by(id=script.id).first()
    grid = refreshed.extra_metadata["storyboard"]["scene_grids"]["1"]
    assert grid["image_url"] == "https://oss.example.com/grid.png"
    assert grid["panel_count"] == 12
    assert len(grid["cells"]) == 12
    assert grid["cells"][0]["duration"] == 1.0
    assert "【整体版式】" in captured["prompt"]
    assert "https://example.com/env.png" in captured["refs"]
    assert any(r["type"] == "environment" for r in grid["refs_used"])


def test_scene_grid_video_task_persists_video(db_session, monkeypatch):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(
        scenes=[{"scene_number": 1, "location": "酒馆外"}],
        extra_metadata={
            "storyboard": {
                "frames": [],
                "scene_grids": {
                    "1": {
                        "scene_number": 1,
                        "image_url": "https://oss.example.com/grid.png",
                        "aspect_ratio": "16:9",
                        "cells": [
                            {"panel_index": 1, "title": "醉步入场", "caption": "醉步入场", "duration": 6.0},
                            {"panel_index": 2, "title": "重拳轰尘", "caption": "重拳轰尘", "duration": 6.0},
                        ],
                    }
                },
            }
        },
    )
    task = _create_task(db_session, user.id, TaskType.VIDEO_GENERATION)

    import app.services.ai_service as ai_service_module
    import app.services.storyboard.scene_grid.processor as processor
    import app.services.storyboard.scene_grid.video_processor as video_processor
    import app.services.video.video_generation_service as video_module

    monkeypatch.setattr(ai_service_module, "ai_service", _fake_ai_service())
    monkeypatch.setattr(
        video_processor,
        "load_ref_context",
        lambda db, script, script_id: FakeRefContext(),
    )
    monkeypatch.setattr(video_processor, "abs_url", lambda url: url)

    captured = {}

    class FakeVideoService:
        def __init__(self, ai_manager=None):
            pass

        async def generate_video(self, **kwargs):
            captured.update(kwargs)
            return {
                "success": True,
                "video_url": "https://oss.example.com/video.mp4",
                "thumbnail_url": "https://oss.example.com/thumb.png",
                "provider_used": "volcengine",
                "model_used": "doubao-seedance-2-0",
            }

    monkeypatch.setattr(video_module, "VideoGenerationService", FakeVideoService)

    payload = {
        "script_id": script.id,
        "scene_number": 1,
        "model": "seedance-2.0",
        "resolution": "720p",
    }
    anyio.run(processor.process_scene_grid_video_task, db_session, task.id, payload, user.id)

    db_session.expire_all()
    refreshed_task = db_session.query(Task).filter_by(id=task.id).first()
    assert refreshed_task.status == TaskStatus.COMPLETED
    refreshed = db_session.query(Script).filter_by(id=script.id).first()
    grid = refreshed.extra_metadata["storyboard"]["scene_grids"]["1"]
    assert grid["video_url"] == "https://oss.example.com/video.mp4"
    assert grid["video_model"] == "doubao-seedance-2-0"
    assert grid["image_url"] == "https://oss.example.com/grid.png"
    assert captured["image_url"] == "https://oss.example.com/grid.png"
    assert captured["duration"] == 12
    assert "不得出现分镜格子" in captured["prompt"]


def test_scene_grid_video_task_fails_without_sheet(db_session, monkeypatch):
    setup_factories(db_session)
    user = UserFactory()
    script = ScriptFactory(extra_metadata={"storyboard": {"frames": []}})
    task = _create_task(db_session, user.id, TaskType.VIDEO_GENERATION)

    import app.services.storyboard.scene_grid.processor as processor

    payload = {"script_id": script.id, "scene_number": 1}
    anyio.run(processor.process_scene_grid_video_task, db_session, task.id, payload, user.id)

    db_session.expire_all()
    refreshed_task = db_session.query(Task).filter_by(id=task.id).first()
    assert refreshed_task.status == TaskStatus.FAILED
    assert "尚未生成宫格分镜图" in refreshed_task.error_message
