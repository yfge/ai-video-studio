import pytest
from app.repositories.narrative_memory_repository import NarrativeMemoryRepository
from app.services.narrative_memory.source_hash import novel_chapter_source_hash
from app.services.story.story_novel_canon_service import (
    CANON_GATE_VERSION,
    content_hash,
)
from app.services.story.story_novel_length_service import generation_plan_hash
from fastapi import HTTPException
from tests.unit.test_story_novel_continuity_v3 import _ready_v2_revision


def test_v2_approval_rejects_report_from_another_canon(db_session):
    _user, service, revision, _chapter, _canon_value = _ready_v2_revision(db_session)
    report = dict(revision.continuity_report)
    report["canon_hash"] = "f" * 64
    report.pop("report_hash")
    report["report_hash"] = content_hash(report)
    revision.continuity_report = report
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        service.approve(revision.business_id)
    assert "连续性报告未使用当前 Canon" in str(exc.value.detail)


def test_v2_approval_rejects_tampered_report_hash(db_session):
    _user, service, revision, _chapter, _canon_value = _ready_v2_revision(db_session)
    report = dict(revision.continuity_report)
    report["summary"] = "hash 计算后被篡改"
    revision.continuity_report = report
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        service.approve(revision.business_id)
    assert "连续性报告 hash 不匹配" in str(exc.value.detail)


def test_v2_approval_rejects_plan_without_explicit_timeline_bindings(db_session):
    _user, service, revision, _chapter, _canon_value = _ready_v2_revision(db_session)
    snapshot = dict(revision.story_snapshot or {})
    story_seed = dict(snapshot.get("story_seed") or {})
    story_seed["structured_outline"] = {}
    snapshot["story_seed"] = story_seed
    revision.story_snapshot = snapshot
    plan = dict(revision.generation_plan)
    rows = [dict(item) for item in plan["chapters"]]
    rows[0].pop("timeline_event_bindings")
    plan.update(
        status="ready",
        story_seed_version=int(snapshot.get("story_seed_version") or 0),
        outline_hash=content_hash({}),
        canon_gate_version=CANON_GATE_VERSION,
        chapters=rows,
    )
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        service.approve(revision.business_id)

    assert "timeline_event_bindings" in str(exc.value.detail)


def test_v2_approval_rejects_missing_frozen_outline_evidence(db_session):
    _user, service, revision, _chapter, _canon_value = _ready_v2_revision(db_session)
    plan = dict(revision.generation_plan)
    plan.pop("outline_hash")
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        service.approve(revision.business_id)

    assert "冻结大纲 hash 已变化" in str(exc.value.detail)


def test_v2_approval_rejects_missing_hard_metric_evidence(db_session):
    _user, service, revision, _chapter, _canon_value = _ready_v2_revision(db_session)
    report = dict(revision.continuity_report)
    report["hard_metrics"] = {}
    report.pop("report_hash")
    report["report_hash"] = content_hash(report)
    revision.continuity_report = report
    db_session.commit()
    with pytest.raises(HTTPException) as exc:
        service.approve(revision.business_id)
    assert "确定性质量门禁不完整" in str(exc.value.detail)


def test_accepting_model_issue_cannot_bypass_hard_metrics(db_session):
    _user, service, revision, _chapter, _canon_value = _ready_v2_revision(db_session)
    report = dict(revision.continuity_report)
    report["issues"] = [
        {
            "id": "global-issue-1",
            "severity": "blocking",
            "chapter_business_ids": [],
            "message": "模型阻断项",
        }
    ]
    report["hard_metrics"] = {
        **report["hard_metrics"],
        "duplicate_milestone_count": 1,
    }
    report.pop("report_hash")
    report["report_hash"] = content_hash(report)
    revision.continuity_report = report
    revision.continuity_status = "failed"
    db_session.commit()
    service.accept_issue(
        revision.business_id,
        "global-issue-1",
        "编辑确认这是模型误报",
    )
    assert revision.continuity_status == "failed"
    assert (
        revision.continuity_report["issues"][0]["accepted_reason"]
        == "编辑确认这是模型误报"
    )
    stored = dict(revision.continuity_report)
    stored_hash = stored.pop("report_hash")
    assert stored_hash == content_hash(stored)
    with pytest.raises(HTTPException) as exc:
        service.approve(revision.business_id)
    assert "确定性质量门禁未通过" in str(exc.value.detail)


def test_v2_approval_rejects_ledger_candidate_without_claim_contract(db_session):
    _user, service, revision, chapter, _canon_value = _ready_v2_revision(db_session)
    repo = NarrativeMemoryRepository(db_session)
    source_hash = novel_chapter_source_hash(chapter)
    anchor = repo.create_anchor(
        story_id=revision.story_id,
        story_business_id=revision.story.business_id,
        canon_branch_id="main",
        anchor_type="chapter",
        chapter_business_id=chapter.business_id,
        narrative_sequence=1000,
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
    )
    repo.flush()
    quote = chapter.content_text[:8]
    event = repo.create_event(
        story_id=revision.story_id,
        story_business_id=revision.story.business_id,
        canon_branch_id="main",
        event_type="action",
        summary=quote,
        occurred_at_anchor_business_id=anchor.business_id,
        status="candidate",
        source_artifact_type="novel_chapter",
        source_artifact_business_id=chapter.business_id,
        source_version=1,
        source_hash=source_hash,
        candidate_evidence={
            "source_quote": quote,
            "source_quote_verified": True,
        },
    )
    repo.flush()
    ledger = dict(revision.continuity_ledger or {})
    rows = dict(ledger.get("chapters") or {})
    entry = dict(rows["1"])
    entry["event_ids"] = [event.business_id]
    rows["1"] = entry
    ledger["chapters"] = rows
    revision.continuity_ledger = ledger
    repo.commit()

    with pytest.raises(HTTPException) as exc:
        service.approve(revision.business_id)

    assert "候选证据或 ledger ID 不匹配" in str(exc.value.detail)
