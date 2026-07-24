import json

import anyio
from app.services.story.story_novel_chapter_service import generate_or_resume_chapter
from app.services.story.story_novel_generation_context import build_chapter_context
from tests.unit.test_story_novel_canon_state import _body, _delta, _v2_revision
from tests.unit.test_story_novel_longform import _plan_row, _setup


def test_runtime_checkpoint_fields_do_not_change_prompt_contract(db_session):
    _user, _story, service, revision, _task, *_ = _setup(db_session)
    row = _plan_row(1)
    _v2_revision(revision, row)
    before = build_chapter_context(service, revision, 1, row)

    runtime = {
        **row,
        "actual_chars": 3217,
        "generation_status": "ready",
        "context_hash": "old-context",
        "body_hash": "old-body",
        "source_hash": "old-source",
        "extraction_status": "ready",
        "event_ids": ["own-event"],
        "fact_ids": ["own-fact"],
        "memory_ids": ["own-memory"],
    }
    plan = dict(revision.generation_plan)
    plan["chapters"] = [runtime]
    revision.generation_plan = plan
    db_session.commit()

    after = build_chapter_context(service, revision, 1, runtime)
    assert after["context"] == before["context"]
    assert after["evidence"]["context_hash"] == before["evidence"]["context_hash"]
    assert after["evidence"]["chapter_contract_hash"] == (
        before["evidence"]["chapter_contract_hash"]
    )


def test_untyped_character_arc_start_state_is_not_in_prose_context(db_session):
    _user, _story, service, revision, _task, *_ = _setup(db_session)
    row = _plan_row(1)
    canon = _v2_revision(revision, row)
    canon["character_arcs"][0]["start_state"] = "FUTURE_ARC_SECRET"
    plan = dict(revision.generation_plan)
    plan["canon"] = canon
    revision.generation_plan = plan

    context = build_chapter_context(service, revision, 1, row)

    assert "FUTURE_ARC_SECRET" not in json.dumps(context["context"], ensure_ascii=False)


def test_runtime_checkpoint_ids_are_absent_from_state_audit(db_session, monkeypatch):
    _user, _story, service, revision, task, *_ = _setup(db_session)
    row = {
        **_plan_row(1),
        "event_ids": ["own-event"],
        "fact_ids": ["own-fact"],
        "memory_ids": ["own-memory"],
        "body_hash": "own-body",
    }
    _v2_revision(revision, row)
    prompts = []

    async def generate(_revision, prompt, **_kwargs):
        prompts.append(prompt)
        return _delta() if "从实际小说正文提取" in prompt else _body()

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
        row,
        generate,
    )
    audit = next(item for item in prompts if "从实际小说正文提取" in item)
    for secret in ("own-event", "own-fact", "own-memory", "own-body"):
        assert secret not in audit
