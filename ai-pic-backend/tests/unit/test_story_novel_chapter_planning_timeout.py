import asyncio
from types import SimpleNamespace

import anyio
import pytest
from app.services.story import story_novel_task_generation as generation
from app.services.story.story_novel_v3_prompts import prose_blocks_prompt
from fastapi import HTTPException


def _revision():
    return SimpleNamespace(
        business_id="revision-timeout",
        model="deepseek:deepseek-v4-pro",
        temperature=0.7,
        generation_plan={
            "model_policy": {
                "planning_model": "deepseek:deepseek-v4-pro",
                "prose_model": "deepseek:deepseek-v4-pro",
                "audit_model": "codex:gpt-5.6-sol",
            }
        },
    )


def test_planning_timeout_allows_deepseek_keepalive_window():
    assert generation._CHAPTER_PLANNING_TIMEOUT_SECONDS >= 600


@pytest.mark.parametrize("stage", ["planning", "chapter_planning.2"])
def test_planning_has_total_timeout_and_one_transport_retry(monkeypatch, stage):
    calls = []

    async def slow_call(**kwargs):
        calls.append(kwargs)
        await asyncio.sleep(1)
        return "late"

    monkeypatch.setattr(generation, "generate_story_novel_text", slow_call)
    monkeypatch.setattr(generation, "_CHAPTER_PLANNING_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(generation, "_retry_pause", _no_wait)

    async def run():
        return await generation.generate_task_text(
            _revision(),
            prose_blocks_prompt({"test": True}),
            max_tokens=12_000,
            stage=stage,
        )

    with pytest.raises(HTTPException, match="连续两次模型调用") as exc:
        anyio.run(run)

    assert exc.value.status_code == 504
    assert len(calls) == 2
    assert all(call["call_scene"].endswith(stage) for call in calls)


def test_non_planning_stage_is_not_wrapped_in_chapter_timeout(monkeypatch):
    async def generate(**_kwargs):
        return "ok"

    monkeypatch.setattr(generation, "generate_story_novel_text", generate)

    async def run():
        return await generation.generate_task_text(
            _revision(),
            prose_blocks_prompt({"test": True}),
            max_tokens=12_000,
            stage="prose.2",
        )

    result = anyio.run(run)

    assert result == "ok"


def test_planning_retries_incomplete_chunked_transport_once(monkeypatch):
    calls = []
    sleeps = []

    async def generate(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise HTTPException(
                status_code=500,
                detail=(
                    "AI生成失败: peer closed connection without sending "
                    "complete message body (incomplete chunked read)"
                ),
            )
        return "ok"

    monkeypatch.setattr(generation, "generate_story_novel_text", generate)

    async def pause():
        sleeps.append("waited")

    monkeypatch.setattr(generation, "_retry_pause", pause)

    async def run():
        return await generation.generate_task_text(
            _revision(),
            prose_blocks_prompt({"test": True}),
            max_tokens=12_000,
            stage="chapter_planning.7",
        )

    assert anyio.run(run) == "ok"
    assert len(calls) == 2
    assert sleeps == ["waited"]


def test_managed_prose_retries_incomplete_chunked_transport_once(monkeypatch):
    calls = []

    async def generate(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise HTTPException(
                status_code=500,
                detail="AI生成失败: Server disconnected without sending a response.",
            )
        return "ok"

    monkeypatch.setattr(generation, "generate_story_novel_text", generate)
    monkeypatch.setattr(generation, "_retry_pause", _no_wait)

    async def run():
        return await generation.generate_task_text(
            _revision(),
            prose_blocks_prompt({"test": True}),
            max_tokens=12_000,
            stage="prose.10",
        )

    assert anyio.run(run) == "ok"
    assert len(calls) == 2


def test_managed_prose_does_not_retry_non_transport_failure(monkeypatch):
    calls = []

    async def generate(**kwargs):
        calls.append(kwargs)
        raise HTTPException(status_code=500, detail="正文 blocks schema 无效")

    monkeypatch.setattr(generation, "generate_story_novel_text", generate)

    async def run():
        return await generation.generate_task_text(
            _revision(),
            prose_blocks_prompt({"test": True}),
            max_tokens=12_000,
            stage="prose.10",
        )

    with pytest.raises(HTTPException, match="schema 无效"):
        anyio.run(run)
    assert len(calls) == 1


def test_managed_local_repair_retries_empty_model_content_once(monkeypatch):
    calls = []

    async def generate(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise HTTPException(
                status_code=502,
                detail=(
                    "AI生成返回空内容，未写入小说 checkpoint: "
                    "finish_reason=unknown reason=empty_model_content"
                ),
            )
        return "ok"

    monkeypatch.setattr(generation, "generate_story_novel_text", generate)
    monkeypatch.setattr(generation, "_retry_pause", _no_wait)

    async def run():
        return await generation.generate_task_text(
            _revision(),
            prose_blocks_prompt({"test": True}),
            max_tokens=4_000,
            stage="local_repair.18",
        )

    assert anyio.run(run) == "ok"
    assert len(calls) == 2


@pytest.mark.parametrize("code", ["server_error", "server_is_overloaded"])
def test_managed_local_repair_retries_codex_server_failure_once(monkeypatch, code):
    calls = []

    async def generate(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise HTTPException(
                status_code=500,
                detail=(
                    "AI生成失败: codex 错误: Codex response error: "
                    f"code={code} message=Please retry later"
                ),
            )
        return "ok"

    monkeypatch.setattr(generation, "generate_story_novel_text", generate)
    monkeypatch.setattr(generation, "_retry_pause", _no_wait)

    async def run():
        return await generation.generate_task_text(
            _revision(),
            prose_blocks_prompt({"test": True}),
            max_tokens=4_000,
            stage="local_repair.18",
        )

    assert anyio.run(run) == "ok"
    assert len(calls) == 2


async def _no_wait():
    return None
