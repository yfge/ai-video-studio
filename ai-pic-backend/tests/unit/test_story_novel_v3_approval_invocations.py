import copy
import hashlib
import json

import pytest
from app.models.llm_invocation import LLMInvocation
from app.services.story.story_novel_v3_approval import require_v3_quality
from fastapi import HTTPException
from tests.unit.test_story_novel_v3_approval import _invocation, _ready_v3


def test_v3_quality_rejects_persisted_invocation_mismatch(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    invocation = db_session.get(LLMInvocation, 102)
    invocation.response_metadata = {
        "finish_reason": "length",
        "product_status": "rejected",
    }
    db_session.commit()

    with pytest.raises(HTTPException, match="持久化 invocation"):
        require_v3_quality(db_session, revision, chapters, ledger)


def test_v3_quality_accepts_raw_whitespace_with_product_content_hash(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    invocation = db_session.get(LLMInvocation, 102)
    invocation.response = f"\n{invocation.response} \n"
    attempt = ledger["1"]["stage_metrics"]["prose"]["attempts"][0]
    attempt["raw_response_hash"] = hashlib.sha256(
        invocation.response.encode()
    ).hexdigest()
    db_session.commit()

    require_v3_quality(db_session, revision, chapters, ledger)


def test_v3_quality_accepts_complete_blocks_recovered_after_length_finish(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    invocation = db_session.get(LLMInvocation, 102)
    metadata = dict(invocation.response_metadata or {})
    metadata.update(finish_reason="length", product_status="rejected")
    invocation.response_metadata = metadata
    attempt = ledger["1"]["stage_metrics"]["prose"]["attempts"][0]
    attempt.update(finish_reason="length", product_status="rejected")
    db_session.commit()

    require_v3_quality(db_session, revision, chapters, ledger)


def test_v3_quality_rejects_content_filtered_blocks_even_when_json_is_complete(
    db_session,
):
    revision, chapters, ledger = _ready_v3(db_session)
    invocation = db_session.get(LLMInvocation, 102)
    metadata = dict(invocation.response_metadata or {})
    metadata.update(finish_reason="content_filter", product_status="rejected")
    invocation.response_metadata = metadata
    attempt = ledger["1"]["stage_metrics"]["prose"]["attempts"][0]
    attempt.update(finish_reason="content_filter", product_status="rejected")
    db_session.commit()

    with pytest.raises(HTTPException, match="持久化 invocation"):
        require_v3_quality(db_session, revision, chapters, ledger)


@pytest.mark.parametrize("remove_telemetry", [False, True])
def test_v3_quality_rejects_deleted_length_control_activation(
    db_session, remove_telemetry
):
    revision, chapters, ledger = _ready_v3(db_session)
    revision_ledger = copy.deepcopy(revision.continuity_ledger)
    revision_ledger.pop("prose_length_control")
    if remove_telemetry:
        revision_ledger["chapters"]["1"]["stage_metrics"]["prose"].pop("length_control")
    revision.continuity_ledger = revision_ledger

    with pytest.raises(HTTPException, match="正文长度控制策略证据不完整"):
        require_v3_quality(db_session, revision, chapters, revision_ledger["chapters"])


def test_v3_quality_rejects_length_control_activation_past_the_plan(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    revision.continuity_ledger["prose_length_control"]["activated_from_position"] = 2

    with pytest.raises(HTTPException, match="正文长度控制策略证据不完整"):
        require_v3_quality(db_session, revision, chapters, ledger)


def test_v3_quality_rejects_chapter_scene_prefix_collision(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    invocation = db_session.get(LLMInvocation, 102)
    invocation.call_scene = f"story_novel.{revision.business_id}.prose.10"
    db_session.commit()

    with pytest.raises(HTTPException, match="持久化 invocation"):
        require_v3_quality(db_session, revision, chapters, ledger)


def test_v3_quality_requires_repair_invocation_when_body_was_repaired(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    tampered = copy.deepcopy(ledger)
    tampered["1"]["body_repair_count"] = 1

    with pytest.raises(HTTPException, match="v3 质量/hash/调用证据"):
        require_v3_quality(db_session, revision, chapters, tampered)


def test_v3_quality_detects_applied_repair_when_ledger_hides_it(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    entry = ledger["1"]
    first = entry["blocks"][0]
    content = chapters[0].content_text[first["start"] : first["end"]]
    response = json.dumps(
        {"replacements": [{"block_id": "B01", "content_text": content}]},
        ensure_ascii=False,
    )
    db_session.add(_invocation(301, revision, "local_repair.1", "prose", response))
    db_session.commit()

    with pytest.raises(HTTPException, match="持久化 invocation"):
        require_v3_quality(db_session, revision, chapters, ledger)


def test_v3_quality_recomputes_reservation_status_from_persisted_calls(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    tampered = copy.deepcopy(ledger)
    tampered["1"]["audit_reservations"][0]["status"] = "failed"

    with pytest.raises(HTTPException, match="v3 质量/hash/调用证据"):
        require_v3_quality(db_session, revision, chapters, tampered)


def test_v3_quality_rejects_reservation_without_invocation(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    tampered = copy.deepcopy(ledger)
    entry = tampered["1"]
    budget = entry["audit_budget_hash"]
    entry["audit_reservations"].append(
        {
            "reservation_id": "r02-missing",
            "budget_hash": budget,
            "stage": f"audit.1.{budget}.body.missing.r02-missing",
            "task_id": None,
            "status": "reserved",
        }
    )

    with pytest.raises(HTTPException, match="v3 质量/hash/调用证据"):
        require_v3_quality(db_session, revision, chapters, tampered)


def test_v3_quality_requires_prompt_fingerprint_at_invocation_start(db_session):
    revision, chapters, ledger = _ready_v3(db_session)
    row = db_session.query(LLMInvocation).filter(LLMInvocation.id == 80).one()
    row.input_references = []
    db_session.commit()

    with pytest.raises(HTTPException, match="持久化 invocation"):
        require_v3_quality(db_session, revision, chapters, ledger)
