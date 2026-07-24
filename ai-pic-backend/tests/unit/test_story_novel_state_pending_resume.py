import json

import anyio
import pytest
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
)
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_length_service import generation_plan_hash
from fastapi import HTTPException
from tests.unit.test_story_novel_longform import _setup

EVENT_QUOTE = (
    "我，褚蓝，澄砂港路线调度员，现依水议会第417号决议，"
    "将零号风钥移交予旱海路线工程师黎雁……移交完成"
)
INVALID_QUOTE = f"褚蓝双手捧着金属盒，递到黎雁面前……{EVENT_QUOTE}"


def _canon() -> dict:
    characters = (
        ("chu-lan", "褚蓝"),
        ("li-yan", "黎雁"),
        ("pei-heng", "裴衡"),
    )
    return normalize_canon(
        {
            "gate_version": CANON_GATE_VERSION,
            "timeline": [
                {
                    "id": "time-1",
                    "label": "2174年8月3日，褚蓝公开移交零号风钥",
                    "order": 1,
                    "story_time": "2174年8月3日",
                    "immutable": True,
                    "source_chapter_position": 1,
                    "source_key_event": "2174年8月3日，褚蓝公开移交零号风钥",
                }
            ],
            "entities": [
                *[
                    {
                        "id": item_id,
                        "kind": "character",
                        "name": name,
                        "aliases": [],
                        "attributes": {},
                    }
                    for item_id, name in characters
                ],
                {
                    "id": "zero-wind-key",
                    "kind": "object",
                    "name": "零号风钥",
                    "aliases": [],
                    "attributes": {},
                },
                {
                    "id": "sand-port",
                    "kind": "location",
                    "name": "澄砂港",
                    "aliases": [],
                    "attributes": {},
                },
            ],
            "world_rules": [],
            "milestones": [],
            "character_arcs": [],
            "initial_state": {
                **{
                    item_id: {
                        "location": "sand-port",
                        "knowledge": [],
                        "status": "在场",
                    }
                    for item_id, _name in characters
                },
                "zero-wind-key": {
                    "location": "sand-port",
                    "owner_id": None,
                    "status": "未移交",
                },
            },
        }
    )


def _plan_row() -> dict:
    grants = [
        {
            "character_id": character_id,
            "fact_id": fact_id,
            "source_event_id": "event-1-1",
        }
        for character_id, fact_id in (
            ("chu-lan", "fact-transfer-recorded"),
            ("li-yan", "fact-custody-received"),
            ("pei-heng", "fact-transfer-witnessed"),
        )
    ]
    return {
        "position": 1,
        "title": "第一章",
        "goal": "完成零号风钥公开移交",
        "key_events": ["2174年8月3日，褚蓝公开移交零号风钥"],
        "character_focus": ["褚蓝", "黎雁", "裴衡"],
        "open_threads": [],
        "end_state": "黎雁接管零号风钥",
        "min_chars": 3000,
        "target_chars": 3600,
        "max_chars": 5000,
        "length_source": "profile_default",
        "preconditions": [],
        "required_event_ids": ["event-1-1"],
        "state_transitions": [
            {
                "subject_id": "zero-wind-key",
                "field": "status",
                "from_value": "未移交",
                "to_value": "已移交",
                "reason": "公开移交完成",
            },
            {
                "subject_id": "zero-wind-key",
                "field": "owner_id",
                "from_value": None,
                "to_value": "li-yan",
                "reason": "黎雁接收保管",
            },
        ],
        "knowledge_grants": grants,
        "location_transitions": [],
        "milestones_consumed": [],
        "forbidden_event_ids": [],
        "payoffs_due": [],
        "canon_refs": [
            "time-1",
            "chu-lan",
            "li-yan",
            "pei-heng",
            "zero-wind-key",
        ],
        "timeline_event_bindings": {"time-1": "event-1-1"},
    }


def _fixture(db_session):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    canon = _canon()
    row = _plan_row()
    plan = {
        "schema": "story_novel_generation_plan.v2",
        "version": 4,
        "status": "ready",
        "phase": "ready",
        "outline_hash": "frozen-outline",
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "canon_gate_version": CANON_GATE_VERSION,
        "chapter_count": 1,
        "target_chars": 3600,
        "chapters": [row],
    }
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    revision.chapter_count = 1
    db_session.commit()
    return service, revision, task, row


def _body(marker: str = "ORIGINAL") -> str:
    return json.dumps(
        {
            "title": "第一章",
            "content_text": (
                f"{marker}。2174年8月3日，公开交接仪式开始。"
                f"“{EVENT_QUOTE}。”见证人依次签字。"
                + "澄砂港的交接记录仍然完整。" * 280
            ),
            "summary": "褚蓝公开移交零号风钥",
            "plot_delta": {},
        },
        ensure_ascii=False,
    )


def _audit(quote: str) -> str:
    return json.dumps(
        {
            "occurred_event_ids": ["event-1-1"],
            "premature_future_event_ids": [],
            "state_transitions": _plan_row()["state_transitions"],
            "knowledge_grants": _plan_row()["knowledge_grants"],
            "location_transitions": [],
            "milestones_consumed": [],
            "opened_thread_ids": [],
            "resolved_thread_ids": [],
            "world_rule_violations": [],
            "evidence": {"event-1-1": quote},
            "timeline_evidence": {"time-1": f"2174年8月3日……{quote}"},
        },
        ensure_ascii=False,
    )


async def _empty_extraction(*_args, **_kwargs):
    return {"events": [], "memories": []}


def _enter_pending(service, revision, task, row) -> tuple[str, str]:
    async def invalid(_revision, prompt, **_kwargs):
        return _audit(INVALID_QUOTE) if "从实际小说正文提取" in prompt else _body()

    with pytest.raises(HTTPException, match="状态提取待恢复"):
        anyio.run(generate_or_resume_chapter, service, revision, task, row, invalid)
    chapter = revision.chapters[0]
    return chapter.content_text, chapter.content_hash


def test_evidence_only_failure_checkpoints_body_then_resumes_state_only(
    db_session, monkeypatch
):
    service, revision, task, row = _fixture(db_session)
    narrative_calls = 0

    async def extracted(*_args, **_kwargs):
        nonlocal narrative_calls
        narrative_calls += 1
        return await _empty_extraction()

    monkeypatch.setattr(
        "app.services.story.story_novel_chapter_service."
        "NarrativeExtractionService.extract",
        extracted,
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )
    saved_body, saved_hash = _enter_pending(service, revision, task, row)
    pending = revision.continuity_ledger["chapters"]["1"]
    assert pending["status"] == "state_pending"
    assert pending["state_pending_reason"] == "source_evidence"
    assert pending["extraction_status"] == "blocked"
    assert all(
        pending[key] is None
        for key in (
            "state_delta",
            "state_after",
            "state_after_hash",
            "plot_delta",
            "plot_delta_source",
            "plot_delta_version",
        )
    )
    assert revision.continuity_ledger["recovery_from_position"] == 1
    assert "current_state" not in revision.continuity_ledger
    audit_calls = 0

    async def state_only(_revision, prompt, **_kwargs):
        nonlocal audit_calls
        assert "从实际小说正文提取" in prompt
        audit_calls += 1
        return _audit(EVENT_QUOTE)

    chapter = anyio.run(
        generate_or_resume_chapter, service, revision, task, row, state_only
    )
    entry = revision.continuity_ledger["chapters"]["1"]
    assert (audit_calls, narrative_calls) == (1, 1)
    assert (chapter.content_text, chapter.content_hash) == (saved_body, saved_hash)
    assert entry["status"] == "ready"
    assert entry["state_validation"] == {"status": "passed", "violations": []}
    assert entry["state_after"]["subjects"]["zero-wind-key"] == {
        "location": "sand-port",
        "owner_id": "li-yan",
        "status": "已移交",
    }
    assert {
        key: value["knowledge"]
        for key, value in entry["state_after"]["subjects"].items()
        if key in {"chu-lan", "li-yan", "pei-heng"}
    } == {
        "chu-lan": ["fact-transfer-recorded"],
        "li-yan": ["fact-custody-received"],
        "pei-heng": ["fact-transfer-witnessed"],
    }
    assert entry["plot_delta"]["character_states"]["zero-wind-key"] == {
        "status": "已移交",
        "owner_id": "li-yan",
    }
    assert "recovery_from_position" not in revision.continuity_ledger
