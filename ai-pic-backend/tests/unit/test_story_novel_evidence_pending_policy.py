import json

import anyio
import pytest
from app.services.narrative_memory.knowledge_evidence import (
    knowledge_evidence_violations,
)
from app.services.narrative_memory.source_evidence import (
    align_source_evidence,
    source_contains_evidence,
)
from app.services.story.story_novel_evidence_alignment import (
    normalize_extracted_evidence,
)
from app.services.story.story_novel_repair_safety import select_repair_evaluation
from app.services.story.story_novel_state_extraction import (
    StateExtractionError,
    extract_chapter_state,
)


def _evaluation(body: str, message: str, *, evidence_only: bool = False) -> dict:
    return {
        "passed": False,
        "result": {"content_text": body},
        "state_validation": {
            "status": "failed",
            "violations": [{"code": "canon_violation", "message": message}],
        },
        "state_extraction_evidence_only": evidence_only,
    }


def test_valid_length_repair_with_evidence_only_failure_is_preserved():
    short_first = _evaluation("短首稿", "章节长度为 2369，要求 3000–5000")
    valid_repair = _evaluation(
        "合格长度返修稿",
        "角色获知证据未明确对应角色获知关系",
        evidence_only=True,
    )

    assert select_repair_evaluation(short_first, valid_repair) is valid_repair


def test_knowledge_evidence_failure_is_extraction_only():
    body = "王明确认老拐检索断潮礁旧档案，发现潮时记录存在断档。"
    invalid_delta = {
        "occurred_event_ids": ["event-departure"],
        "future_event_audit": {},
        "knowledge_grants": [
            {
                "character_id": "char-wang",
                "fact_id": "fact-departure",
                "source_event_id": "event-departure",
            }
        ],
        "evidence": {"event-departure": body},
        "knowledge_evidence": {
            "char-wang|fact-departure|event-departure": "发现潮时记录存在断档。"
        },
    }

    async def generate(_revision, prompt, **_kwargs):
        if "typed state 已冻结" in prompt:
            return json.dumps(
                {
                    "evidence": invalid_delta["evidence"],
                    "knowledge_evidence": invalid_delta["knowledge_evidence"],
                    "timeline_evidence": {},
                },
                ensure_ascii=False,
            )
        return json.dumps(invalid_delta, ensure_ascii=False)

    async def run():
        return await extract_chapter_state(
            object(),
            chapter_plan={
                "required_event_ids": ["event-departure"],
                "knowledge_grants": invalid_delta["knowledge_grants"],
                "canon_refs": [],
                "timeline_event_bindings": {},
            },
            state_before={},
            content_text=body,
            future_event_catalog=[],
            current_timeline=[],
            canon={
                "entities": [{"id": "char-wang", "kind": "character", "name": "王明"}]
            },
            generate_text=generate,
        )

    with pytest.raises(StateExtractionError) as caught:
        anyio.run(run)

    assert caught.value.repair_count == 1
    assert caught.value.evidence_only is True


def test_normalizer_binds_exact_knowledge_sentences_to_the_source_event():
    event = "老拐检索断潮礁旧档案，发现潮时记录存在断档。"
    wang = "王明确认老拐检索断潮礁旧档案，发现潮时记录存在断档。"
    guai = "老拐确认老拐检索断潮礁旧档案，发现潮时记录存在断档。"
    body = f"{event}{wang}{guai}"
    grants = [
        {
            "character_id": character_id,
            "fact_id": "fact-gap",
            "source_event_id": "event-gap",
        }
        for character_id in ("char-wang", "char-guai")
    ]
    delta = {
        "occurred_event_ids": ["event-gap"],
        "knowledge_grants": grants,
        "evidence": {"event-gap": event},
        "knowledge_evidence": {
            "char-wang|fact-gap|event-gap": wang,
            "char-guai|fact-gap|event-gap": event,
        },
        "timeline_evidence": {},
    }
    canon = {
        "entities": [
            {"id": "char-wang", "kind": "character", "name": "王明"},
            {"id": "char-guai", "kind": "character", "name": "老拐"},
        ]
    }

    normalize_extracted_evidence(
        body,
        canon,
        {
            "required_event_ids": ["event-gap"],
            "key_events": [event.removesuffix("。")],
            "knowledge_grants": grants,
            "canon_refs": [],
        },
        delta,
    )

    assert wang.removesuffix("。") in delta["evidence"]["event-gap"]
    assert guai.removesuffix("。") in delta["evidence"]["event-gap"]
    assert delta["knowledge_evidence"][
        "char-guai|fact-gap|event-gap"
    ] == guai.removesuffix("。")
    assert knowledge_evidence_violations(body, delta, canon) == []


def test_aligner_drops_one_rewritten_lead_but_keeps_exact_action_clauses():
    body = (
        "他从背包里取出三根潮位标尺。"
        "标尺是碳纤维管体，底部自带膨胀螺栓。"
        "王明选定三个点并逐一校准标尺。"
    )
    rewritten = (
        "王明从背包里取出三根潮位标尺。"
        "标尺是碳纤维管体，底部自带膨胀螺栓。"
        "王明选定三个点并逐一校准标尺。"
    )

    aligned = align_source_evidence(body, rewritten)

    assert "王明从背包" not in aligned
    assert "标尺是碳纤维管体" in aligned
    assert "王明选定三个点" in aligned
    assert source_contains_evidence(body, aligned)
