import json

import anyio
from app.services.story.story_novel_canon_service import normalize_canon
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from tests.unit.test_story_novel_canon_state import _v2_revision
from tests.unit.test_story_novel_longform import _canon, _plan_row, _setup


def _audit_payload(timeline_quote: str, event_quote: str = "主角在城门发现裂缝") -> str:
    return json.dumps(
        {
            "occurred_event_ids": ["event-1"],
            "premature_future_event_ids": [],
            "state_transitions": [],
            "knowledge_grants": [],
            "location_transitions": [],
            "milestones_consumed": [],
            "opened_thread_ids": [],
            "resolved_thread_ids": [],
            "world_rule_violations": [],
            "evidence": {"event-1": event_quote},
            "timeline_evidence": {"time-1": timeline_quote},
        },
        ensure_ascii=False,
    )


def test_invalid_audit_evidence_repairs_extraction_without_rewriting_body(
    db_session, monkeypatch
):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    source_event = "2174年8月3日，主角在城门发现裂缝"
    row["key_events"] = [source_event]
    row["canon_refs"] = ["time-1"]
    row["timeline_event_bindings"] = {"time-1": "event-1"}
    _v2_revision(revision, row)
    raw = _canon()
    raw["timeline"][0].update(
        story_time="2174年8月3日",
        label=source_event,
        source_key_event=source_event,
    )
    canon = normalize_canon(raw)
    revision.generation_plan = {
        **dict(revision.generation_plan),
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "chapters": [row],
    }
    db_session.commit()
    body = json.dumps(
        {
            "title": "第一章",
            "content_text": (
                "2174年8月3日，主角在城门发现裂缝。" + "守门记录仍然完整。" * 360
            ),
            "summary": "主角发现裂缝",
            "plot_delta": {},
        },
        ensure_ascii=False,
    )
    body_calls = 0
    audit_calls = 0
    audit_temperatures = []

    async def generate(_revision, prompt, **_kwargs):
        nonlocal body_calls, audit_calls
        if "从实际小说正文提取" not in prompt:
            body_calls += 1
            return body
        audit_calls += 1
        audit_temperatures.append(_kwargs.get("temperature"))
        if "上一次状态提取无效" not in prompt:
            return _audit_payload("发现裂缝……2174年8月3日")
        assert "typed state 已冻结" in prompt
        assert "只修复当前章逐字证据" in prompt
        assert "不得修改任何事件 ID 或状态" in prompt
        fixed = json.loads(_audit_payload("2174年8月3日，主角在城门发现裂缝。"))
        return json.dumps(
            {
                "evidence": fixed["evidence"],
                "timeline_evidence": fixed["timeline_evidence"],
            },
            ensure_ascii=False,
        )

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "NarrativeExtractionService.extract",
        extracted,
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )
    anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)

    entry = revision.continuity_ledger["chapters"]["1"]
    assert body_calls == 1
    assert audit_calls == 2
    assert audit_temperatures == [0.0, 0.0]
    assert entry["body_repair_count"] == 0
    assert entry["state_extraction_repair_count"] == 1
    assert entry["status"] == "ready"


def test_real_6584_audit_repair_keeps_only_exact_event_quote(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = _plan_row()
    row.update(
        {
            "key_events": ["2174年8月3日，褚蓝公开移交零号风钥"],
            "character_focus": ["褚蓝", "黎雁"],
            "canon_refs": ["time-1", "char-chulan", "char-liyan"],
            "timeline_event_bindings": {"time-1": "event-1"},
        }
    )
    _v2_revision(revision, row)
    raw = _canon()
    raw["timeline"][0].update(
        story_time="2174年8月3日",
        label="2174年8月3日，褚蓝公开移交零号风钥",
        source_key_event="2174年8月3日，褚蓝公开移交零号风钥",
    )
    raw["entities"].extend(
        [
            {
                "id": "char-chulan",
                "kind": "character",
                "name": "褚蓝",
                "aliases": [],
                "attributes": {},
            },
            {
                "id": "char-liyan",
                "kind": "character",
                "name": "黎雁",
                "aliases": [],
                "attributes": {},
            },
        ]
    )
    canon = normalize_canon(raw)
    revision.generation_plan = {
        **dict(revision.generation_plan),
        "canon": canon,
        "canon_hash": canon["canon_hash"],
        "chapters": [row],
    }
    db_session.commit()
    exact_quote = (
        "“我，褚蓝，澄砂港路线调度员，现依水议会第417号决议，"
        "将零号风钥移交予旱海路线工程师黎雁。”"
    )
    hallucinated_quote = f"褚蓝双手捧着金属盒，递到黎雁面前……{exact_quote}"
    body = json.dumps(
        {
            "title": "第一章",
            "content_text": (
                f"2174年8月3日，交接仪式开始。{exact_quote}"
                + "见证记录仍然完整。" * 360
            ),
            "summary": "褚蓝公开移交零号风钥",
            "plot_delta": {},
        },
        ensure_ascii=False,
    )
    body_calls = 0
    audit_calls = 0

    async def generate(_revision, prompt, **_kwargs):
        nonlocal body_calls, audit_calls
        if "从实际小说正文提取" not in prompt:
            body_calls += 1
            return body
        audit_calls += 1
        if "上一次状态提取无效" not in prompt:
            return _audit_payload(
                f"2174年8月3日……{hallucinated_quote}",
                hallucinated_quote,
            )
        assert "不得添加说话人、代词或概括" in prompt
        fixed = json.loads(
            _audit_payload(
                f"2174年8月3日……{exact_quote}",
                exact_quote,
            )
        )
        return json.dumps(
            {
                "evidence": fixed["evidence"],
                "timeline_evidence": fixed["timeline_evidence"],
            },
            ensure_ascii=False,
        )

    async def extracted(*_args, **_kwargs):
        return {"events": [], "memories": []}

    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "NarrativeExtractionService.extract",
        extracted,
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_candidate_checkpoint."
        "complete_novel_candidate_set",
        lambda *_args: True,
    )
    anyio.run(generate_or_resume_chapter, service, revision, task, row, generate)

    entry = revision.continuity_ledger["chapters"]["1"]
    assert body_calls == 1
    assert audit_calls == 2
    assert entry["body_repair_count"] == 0
    assert entry["state_extraction_repair_count"] == 1
    assert entry["state_delta"]["evidence"]["event-1"] == exact_quote
    assert entry["status"] == "ready"
