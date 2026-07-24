import json

import anyio
import pytest
from app.services.story import story_novel_plan_parser, story_novel_planning_service
from app.services.story.story_novel_outline_merge import merge_frozen_chapters
from fastapi import HTTPException
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def test_merge_uses_frozen_thread_ids_and_rewrites_later_payoffs():
    generated = [_plan_row(1), _plan_row(2)]
    generated[0]["timeline_event_bindings"] = {"time-1": "event-1"}
    generated[0]["open_threads"] = ["thread-machine"]
    generated[1]["payoffs_due"] = ["thread-machine"]
    frozen = {"chapters": [_plan_row(1), _plan_row(2)]}
    frozen["chapters"][0]["open_threads"] = ["谁改写了邮路数据"]
    frozen["chapters"][0]["timeline_event_bindings"] = {"time-1": "wrong"}

    merged = merge_frozen_chapters(generated, frozen, _canon())

    assert merged[0]["open_threads"] == ["谁改写了邮路数据"]
    assert merged[1]["payoffs_due"] == ["谁改写了邮路数据"]
    assert merged[0]["timeline_event_bindings"] == {"time-1": "event-1"}


def test_merge_collapses_machine_threads_with_identical_payoff_chapters():
    generated = [_plan_row(1), _plan_row(2)]
    generated[0]["open_threads"] = ["thread-observer", "thread-audit-number"]
    generated[1]["payoffs_due"] = ["thread-observer", "thread-audit-number"]
    frozen = {"chapters": [_plan_row(1), _plan_row(2)]}
    frozen["chapters"][0]["open_threads"] = ["观测员下落；云井审计编号"]

    merged = merge_frozen_chapters(generated, frozen, _canon())

    assert merged[0]["open_threads"] == ["观测员下落；云井审计编号"]
    assert merged[1]["payoffs_due"] == ["观测员下落；云井审计编号"]


def test_merge_expands_one_machine_thread_to_multiple_frozen_threads():
    generated = [_plan_row(1), _plan_row(2)]
    generated[0]["open_threads"] = ["thread-composite"]
    generated[1]["payoffs_due"] = ["thread-composite"]
    generated[1]["required_event_ids"] = ["event-2-a", "event-2-b"]
    generated[1]["key_events"] = ["确认观测员下落", "核验云井审计编号"]
    frozen = {"chapters": [_plan_row(1), _plan_row(2)]}
    frozen["chapters"][0]["open_threads"] = ["观测员下落", "云井审计编号"]
    frozen["chapters"][1]["key_events"] = ["确认观测员下落", "核验云井审计编号"]

    merged = merge_frozen_chapters(generated, frozen, _canon())

    assert merged[0]["open_threads"] == ["观测员下落", "云井审计编号"]
    assert merged[1]["payoffs_due"] == ["观测员下落", "云井审计编号"]


def test_merge_rejects_reordered_machine_events_before_ids_can_be_misbound():
    generated = [_plan_row(1)]
    generated[0]["key_events"] = ["事件乙", "事件甲"]
    generated[0]["required_event_ids"] = ["event-b", "event-a"]
    generated[0]["knowledge_grants"] = [
        {
            "character_id": "char-a",
            "fact_id": "fact-from-b",
            "source_event_id": "event-b",
        }
    ]
    frozen = {"chapters": [_plan_row(1)]}
    frozen["chapters"][0]["key_events"] = ["事件甲", "事件乙"]

    with pytest.raises(ValueError, match="key_events 必须逐字、同序"):
        merge_frozen_chapters(generated, frozen, _canon())


def test_merge_accepts_quote_typography_and_restores_frozen_event_text():
    generated = [_plan_row(1)]
    generated[0]["key_events"] = ["老拐拼出外部势力代号'暗潮'"]
    frozen = {"chapters": [_plan_row(1)]}
    frozen["chapters"][0]["key_events"] = ["老拐拼出外部势力代号‘暗潮’"]

    merged = merge_frozen_chapters(generated, frozen, _canon(), validate=False)

    assert merged[0]["key_events"] == ["老拐拼出外部势力代号‘暗潮’"]
    assert merged[0]["required_event_ids"] == ["event-1"]


def test_merge_rejects_machine_threads_with_different_payoff_chapters():
    generated = [_plan_row(1), _plan_row(2), _plan_row(3)]
    generated[0]["open_threads"] = ["thread-observer", "thread-audit-number"]
    generated[1]["payoffs_due"] = ["thread-observer"]
    generated[2]["payoffs_due"] = ["thread-audit-number"]
    frozen = {"chapters": [_plan_row(1), _plan_row(2), _plan_row(3)]}
    frozen["chapters"][0]["open_threads"] = ["观测员下落；云井审计编号"]

    with pytest.raises(ValueError, match="无法确定性映射"):
        merge_frozen_chapters(generated, frozen, _canon())


@pytest.mark.parametrize(
    ("machine_threads", "frozen_threads"),
    [
        (["thread-a", "thread-b"], ["伏笔一", "伏笔二", "伏笔三"]),
        (["thread-a"], []),
        ([], ["伏笔一"]),
    ],
)
def test_merge_rejects_ambiguous_thread_count_mismatch(machine_threads, frozen_threads):
    generated = [_plan_row(1)]
    generated[0]["open_threads"] = machine_threads
    frozen = {"chapters": [_plan_row(1)]}
    frozen["chapters"][0]["open_threads"] = frozen_threads

    with pytest.raises(ValueError, match="伏笔数量.*不一致"):
        merge_frozen_chapters(generated, frozen, _canon())


def test_merge_failure_persists_failed_planning_checkpoint(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    revision.generation_plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "ready",
        "phase": "spec_ready",
        "outline_hash": "outline-hash",
        "chapters": [_plan_row(1)],
    }
    db_session.commit()

    calls = 0

    async def generate(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        payload = (
            _canon()
            if revision.generation_plan["phase"] == "canon"
            else {"chapters": [_plan_row(1)]}
        )
        return json.dumps(payload, ensure_ascii=False)

    def reject_merge(*_args, **_kwargs):
        raise ValueError("冻结大纲伏笔数量与规划不一致")

    monkeypatch.setattr(story_novel_plan_parser, "merge_frozen_chapters", reject_merge)

    with pytest.raises(HTTPException):
        anyio.run(
            story_novel_planning_service.ensure_generation_plan,
            service,
            revision,
            task,
            generate,
        )

    assert revision.generation_plan["status"] == "failed"
    assert revision.generation_plan["phase"] == "chapters"
    assert revision.generation_plan["error"] == "冻结大纲伏笔数量与规划不一致"
    assert calls == 3
