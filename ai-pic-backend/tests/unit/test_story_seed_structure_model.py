import json
from types import SimpleNamespace

import pytest
from app.api.v1.endpoints.stories import novel_task_queue
from app.schemas.story_seed import StorySeedStructureRequest
from app.services.story import story_novel_task_processor as processor
from app.services.story.story_seed_service import StorySeedService
from app.services.story.story_seed_structure_service import structure_story_seed


@pytest.mark.parametrize(
    ("configured", "requested", "expected"),
    [
        (None, None, "deepseek:deepseek-v4-flash"),
        ("codex:gpt-5.4", None, "codex:gpt-5.4"),
        ("deepseek:deepseek-v4-pro", "codex:gpt-5.6", "codex:gpt-5.6"),
    ],
)
def test_structure_seed_uses_selected_planning_model(
    monkeypatch, configured, requested, expected
):
    captured = {}

    async def fake_structure(*args, **kwargs):
        captured["model"] = args[3].model
        captured["chapter_count"] = kwargs["requested_chapter_count"]

    monkeypatch.setattr(processor, "structure_story_seed", fake_structure)
    repo = SimpleNamespace(
        accessible_story=lambda business_id, user: SimpleNamespace(ai_model=configured)
    )

    processor._structure_seed(
        repo,
        db=None,
        task=None,
        payload={
            "story_business_id": "story-1",
            "story_seed_version": 1,
            "chapter_count": 48,
            "model": requested,
        },
        user=object(),
    )

    assert captured["model"] == expected
    assert captured["chapter_count"] == 48


def test_structure_request_has_no_application_chapter_cap():
    request = StorySeedStructureRequest(chapter_count=480, model="codex:gpt-5.6")
    assert request.chapter_count == 480


def test_structure_queue_freezes_story_default_model(monkeypatch):
    captured = {}
    story = SimpleNamespace(
        id=9,
        title="冻结模型",
        business_id="story-9",
        story_seed_version=3,
        ai_model="codex:gpt-5.6",
    )
    monkeypatch.setattr(
        novel_task_queue,
        "StoryNovelRepository",
        lambda _db: SimpleNamespace(
            accessible_story_by_id=lambda *_args, **_kwargs: story
        ),
    )
    monkeypatch.setattr(
        novel_task_queue,
        "StoryNovelRevisionService",
        lambda *_args: SimpleNamespace(_ensure_story_idle=lambda _story: None),
    )
    monkeypatch.setattr(
        novel_task_queue,
        "Task",
        lambda **kwargs: SimpleNamespace(id=17, status="PENDING", **kwargs),
    )
    monkeypatch.setattr(
        novel_task_queue.celery_app,
        "send_task",
        lambda _name, args: captured.update(payload=args[1]),
    )
    db = SimpleNamespace(
        add=lambda task: captured.update(task=task),
        commit=lambda: None,
        refresh=lambda _task: None,
    )

    novel_task_queue.queue_story_seed_structure(
        db,
        SimpleNamespace(id=1),
        story,
        StorySeedStructureRequest(chapter_count=48),
    )

    assert json.loads(captured["task"].parameters)["model"] == "codex:gpt-5.6"
    assert captured["payload"]["model"] == "codex:gpt-5.6"


@pytest.mark.asyncio
async def test_requested_count_overrides_plain_outline_and_is_persisted(monkeypatch):
    output = {
        "structured_outline": {
            "status": "draft",
            "version": 1,
            "thread_schedule_version": 1,
            "thread_payoffs": [],
            "chapters": [
                {
                    "position": position,
                    "title": f"第{position}章",
                    "goal": "推进冲突",
                    "key_events": [f"事件{position}"],
                    "character_focus": [],
                    "open_threads": [],
                    "end_state": "继续",
                }
                for position in range(1, 3)
            ],
        }
    }
    captured = {}

    async def generate_text(_carrier, prompt, **kwargs):
        captured["prompt"] = prompt
        captured["max_tokens"] = kwargs["max_tokens"]
        return json.dumps(output, ensure_ascii=False)

    monkeypatch.setattr(
        StorySeedService, "apply_local_update", lambda *args, **kwargs: None
    )
    story = SimpleNamespace(
        story_seed={
            "schema": "story_seed_v1",
            "title": "两章测试",
            "premise": "测试章节数",
            "outline": "原文字段曾写第1章至第3章",
            "protagonists": [
                {
                    "virtual_ip_business_id": "vip-1",
                    "initial_state": "等待出发",
                }
            ],
            "world_constraints": [],
            "central_conflict": "完成验证",
            "content_constraints": [],
        }
    )
    db = SimpleNamespace(commit=lambda: None, refresh=lambda _value: None)
    task = SimpleNamespace(id=7, status="pending", description="")
    upgraded = await structure_story_seed(
        db,
        story,
        task,
        SimpleNamespace(model="codex:gpt-5.6"),
        generate_text,
        expected_version=1,
        requested_chapter_count=2,
    )

    assert "必须完整返回2章" in captured["prompt"]
    assert captured["max_tokens"] == 6000
    assert len(upgraded.structured_outline.chapters) == 2
    assert upgraded.structured_outline.requested_chapter_count == 2
    assert upgraded.structured_outline.planning_model == "codex:gpt-5.6"
