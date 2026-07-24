from types import SimpleNamespace

import anyio
import pytest
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_gate_support import (
    future_event_catalog,
    premature_plan_violations,
)
from app.services.story.story_novel_state_extraction import (
    StateExtractionError,
    extract_chapter_state,
)
from app.services.story.story_novel_state_service import initial_story_state
from tests.unit.story_novel_future_audit_fixtures import (
    body_with_current_timeline as _body_with_current_timeline,
)
from tests.unit.story_novel_future_audit_fixtures import (
    delta_with_current_timeline as _delta_with_current_timeline,
)
from tests.unit.story_novel_future_audit_fixtures import (
    plan_without_timeline as _plan_without_timeline,
)
from tests.unit.story_novel_future_audit_fixtures import (
    typed_audit_payload as _typed_audit_payload,
)
from tests.unit.test_story_novel_canon_state import _v2_revision
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def test_future_event_catalog_is_visible_only_to_state_audit(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    current = _plan_row(1)
    future = {
        **_plan_row(2),
        "title": "FUTURE_CHAPTER_TITLE",
        "goal": "FUTURE_EVENT_SECRET",
        "key_events": ["FUTURE_EVENT_SECRET"],
        "required_event_ids": ["event-2"],
        "milestones_consumed": ["mile-future-secret"],
    }
    _v2_revision(revision, current)
    canon_raw = _canon()
    canon_raw["milestones"] = [
        {
            "id": "mile-future-secret",
            "label": "FUTURE_MILESTONE_SECRET",
            "planned_position": 2,
            "repeatable": False,
            "outcomes": [
                {
                    "subject_id": "char-a",
                    "field": "status",
                    "value": "FUTURE_OUTCOME_SECRET",
                }
            ],
        }
    ]
    canon = normalize_canon(canon_raw)
    revision.generation_plan = {
        **dict(revision.generation_plan),
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "chapter_count": 2,
        "target_chars": 6000,
        "chapters": [current, future],
    }
    revision.chapter_count = 2
    db_session.commit()
    prompts = []

    async def generate(_revision, prompt, **_kwargs):
        prompts.append(prompt)
        return (
            _delta_with_current_timeline()
            if "从实际小说正文提取" in prompt
            else _body_with_current_timeline()
        )

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service.NarrativeExtractionService.extract",
        extracted,
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )
    anyio.run(
        generate_or_resume_chapter,
        service,
        revision,
        task,
        current,
        generate,
    )
    prose_prompts = [item for item in prompts if "从实际小说正文提取" not in item]
    audit_prompts = [item for item in prompts if "从实际小说正文提取" in item]
    assert len(prose_prompts) == 1
    assert len(audit_prompts) == 1
    assert "FUTURE_EVENT_SECRET" not in prose_prompts[0]
    assert "FUTURE_CHAPTER_TITLE" not in prose_prompts[0]
    assert "FUTURE_MILESTONE_SECRET" not in prose_prompts[0]
    assert "FUTURE_OUTCOME_SECRET" not in prose_prompts[0]
    assert "FUTURE_EVENT_SECRET" in audit_prompts[0]
    assert "FUTURE_MILESTONE_SECRET" in audit_prompts[0]
    assert "FUTURE_OUTCOME_SECRET" in audit_prompts[0]
    assert "future_event_catalog_for_audit_only" in audit_prompts[0]
    assert "确定安排或必然行动" in audit_prompts[0]
    assert revision.continuity_ledger["current_state"] == {
        **initial_story_state(canon),
        "occurred_event_ids": ["event-1"],
    }


def test_deterministic_gate_catches_future_character_without_date_false_positive(
    db_session,
):
    _user, _story, _service, revision, _task, *_ = _setup(db_session)
    current = _plan_row(1)
    future = {
        **_plan_row(4),
        "title": "九月二十一日的来客",
        "goal": "取得三级权限",
        "key_events": ["岑野以向导身份提出合作"],
        "character_focus": ["岑野"],
    }
    canon_raw = _canon()
    canon_raw["entities"].append(
        {
            "id": "char-cenye",
            "kind": "character",
            "name": "岑野",
            "aliases": [],
            "attributes": {},
        }
    )
    canon = normalize_canon(canon_raw)
    revision.generation_plan = {
        "schema": "story_novel_generation_plan.v2",
        "canon": canon,
        "chapters": [current, future],
    }

    violations = premature_plan_violations(
        revision,
        1,
        "九月二十一日之前至少需要三级权限。岑野敲门说想谈路线。",
    )

    messages = [item["message"] for item in violations]
    assert messages == ["正文提前出现计划第 4 章角色: 岑野"]

    current["character_focus"] = ["岑野"]
    current["key_events"] = ["岑野在本章合法出场"]
    assert premature_plan_violations(revision, 1, "岑野在门口等候。") == []


def test_future_catalog_keeps_all_key_events_when_mapping_is_uneven():
    current = _plan_row(1)
    future = {
        **_plan_row(2),
        "required_event_ids": ["event-2-a", "event-2-b"],
        "key_events": ["事件甲", "事件乙", "事件丙"],
    }
    revision = SimpleNamespace(
        generation_plan={"canon": _canon(), "chapters": [current, future]}
    )

    catalog = future_event_catalog(revision, 1)

    assert catalog[0]["events"] == [
        {"event_id": "event-2-a", "description": "事件甲"},
        {"event_id": "event-2-b", "description": "事件乙；事件丙"},
    ]


def test_unknown_premature_event_id_repairs_audit_without_touching_body():
    content_text = "主角在城门发现裂缝，并把发现写入守门记录。"
    quote = "主角在城门发现裂缝"
    catalog = [
        {
            "position": 2,
            "events": [{"event_id": "event-2", "description": "未来才发生的核验"}],
        }
    ]
    responses = [
        _typed_audit_payload(quote, ["hallucinated-future-id"]),
        _typed_audit_payload(quote, []),
    ]
    prompts = []

    async def generate(_revision, prompt, **_kwargs):
        prompts.append(prompt)
        return responses.pop(0)

    async def run():
        return await extract_chapter_state(
            SimpleNamespace(),
            chapter_plan=_plan_without_timeline(),
            state_before={},
            content_text=content_text,
            future_event_catalog=catalog,
            generate_text=generate,
        )

    delta, repair_count = anyio.run(run)

    assert delta["premature_future_event_ids"] == []
    assert repair_count == 1
    assert len(prompts) == 2
    assert "hallucinated-future-id" in prompts[1]


def test_repeated_unknown_premature_id_remains_audit_only_failure():
    content_text = "主角在城门发现裂缝，并把发现写入守门记录。"
    quote = "主角在城门发现裂缝"
    response = _typed_audit_payload(quote, ["hallucinated-future-id"])

    async def generate(*_args, **_kwargs):
        return response

    async def run():
        return await extract_chapter_state(
            SimpleNamespace(),
            chapter_plan=_plan_without_timeline(),
            state_before={},
            content_text=content_text,
            future_event_catalog=[
                {
                    "position": 2,
                    "events": [{"event_id": "event-2", "description": "未来事件"}],
                }
            ],
            generate_text=generate,
        )

    with pytest.raises(StateExtractionError) as exc:
        anyio.run(run)

    assert exc.value.repair_count == 1
    assert exc.value.evidence_only is True
