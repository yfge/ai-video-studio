from __future__ import annotations

import asyncio
from types import SimpleNamespace

from app.services.story import story_novel_task_processor as processor


def test_adaptation_prompt_uses_only_canonical_novel_sources(monkeypatch):
    chapter = SimpleNamespace(
        business_id="chapter-approved",
        position=1,
        title="已审批章节",
        summary="已审批摘要",
        content_text="CANONICAL_NOVEL_BODY",
        content_hash="body-hash",
        cliffhanger="章末卡点",
    )
    revision = SimpleNamespace(
        business_id="revision-approved",
        content_hash="revision-hash",
        story_snapshot={"story_seed": "FORBIDDEN_STORY_SEED"},
        adaptation_plan=None,
        adaptation_plan_status="empty",
    )
    generation_plan = {"version": 7, "plan_hash": "generation-plan-hash"}
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        processor,
        "require_canonical_revision",
        lambda value: (generation_plan, [chapter]),
    )

    async def generate_text(value, prompt, *, max_tokens):
        captured["prompt"] = prompt
        captured["max_tokens"] = max_tokens
        return (
            '{"episodes":[{"episode_number":1,"title":"第一集",'
            '"source_chapter_business_ids":["chapter-approved"],'
            '"adaptation_goal":"改编目标","summary":"概要",'
            '"plot_points":[],"conflicts":[],"character_arcs":{}}]}'
        )

    def freeze_plan(value, *, version, rows):
        captured["version"] = version
        captured["rows"] = rows
        return {"version": version, "episodes": rows, "plan_hash": "frozen"}

    monkeypatch.setattr(processor, "_generate_text", generate_text)
    monkeypatch.setattr(processor, "freeze_adaptation_plan", freeze_plan)
    service = SimpleNamespace(db=SimpleNamespace(commit=lambda: None))

    asyncio.run(processor._generate_adaptation(service, revision))

    prompt = str(captured["prompt"])
    assert "FORBIDDEN_STORY_SEED" not in prompt
    assert "CANONICAL_NOVEL_BODY" in prompt
    assert "revision-approved" in prompt
    assert "generation-plan-hash" in prompt
    assert captured["max_tokens"] == 8000
    assert captured["version"] == 1
    assert revision.adaptation_plan_status == "draft"
