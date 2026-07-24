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
    "……褚蓝确认零号风钥交接记录已经生效"
    "……黎雁确认自己已经接管零号风钥"
    "……裴衡确认自己已经见证零号风钥移交"
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
            "knowledge_evidence": {
                "chu-lan|fact-transfer-recorded|event-1-1": (
                    "褚蓝确认零号风钥交接记录已经生效"
                ),
                "li-yan|fact-custody-received|event-1-1": (
                    "黎雁确认自己已经接管零号风钥"
                ),
                "pei-heng|fact-transfer-witnessed|event-1-1": (
                    "裴衡确认自己已经见证零号风钥移交"
                ),
            },
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
