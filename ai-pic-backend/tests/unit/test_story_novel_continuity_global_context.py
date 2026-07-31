from types import SimpleNamespace

import pytest

from app.services.story.story_novel_continuity_global_context import (
    GLOBAL_PAYLOAD_CHAR_BUDGET,
    build_global_context,
    global_context_chars,
)
from app.services.story.story_novel_continuity_grounding import (
    payload_evidence_catalog,
)


def _chapter(position: int):
    return SimpleNamespace(
        business_id=f"chapter-{position}",
        content_hash=f"body-{position}",
        position=position,
        title=f"第{position}章",
        summary=("本章推动认知、能力、资源或活动范围之一。" * 30),
        cliffhanger="新的选择出现。",
    )


def _ledger(position: int) -> dict:
    return {
        "body_hash": f"body-{position}",
        "source_hash": f"source-{position}",
        "context_hash": f"context-{position}",
        "canon_hash": "canon-hash",
        "state_before_hash": f"state-{position - 1}",
        "state_after_hash": f"state-{position}",
        "sentence_index_hash": f"sentences-{position}",
        "plot_delta": {"key_events": [f"推进事件{position}"]},
        "state_delta": {
            "occurred_event_ids": [f"event-{position}"],
            "entity_introductions": [
                {"id": f"location-{position}", "kind": "location"}
            ],
            "evidence": {f"event-{position}": "不得进入全局包的重复 quote"},
        },
        "proof_spans": [
            {
                "contract_id": f"event:event-{position}",
                "sentence_ids": ["S0001"],
                "quote": "不得重复保存的证据句",
                "spans": [
                    {
                        "sentence_id": "S0001",
                        "text": f"第{position}章发生了推进事件。",
                        "start": 0,
                        "end": 12,
                        "source_hash": f"source-{position}",
                    }
                ],
            },
            {
                "contract_id": f"knowledge:{position}",
                "sentence_ids": ["S0001"],
                "spans": [{"sentence_id": "S0001", "text": "重复句不应重复进入上下文"}],
            },
        ],
        "future_audit": {"future_hits": [], "world_rule_hits": []},
    }


def _revision():
    return SimpleNamespace(
        story_snapshot={
            "title": "长篇",
            "story_seed": {
                "structured_outline": {
                    "progression_arcs": [
                        {
                            "arc_id": "arc-1",
                            "growth": {
                                "cognition": "看见更大的世界",
                                "capability": "获得新能力",
                                "resources": "资源扩大",
                                "scope": "从村到县",
                            },
                        }
                    ]
                }
            },
        },
        generation_plan={
            "schema": "story_novel_generation_plan.v3",
            "version": 4,
            "plan_hash": "plan-hash",
            "canon_hash": "canon-hash",
            "chapter_count": 48,
            "model_policy": {"audit_model": "codex:gpt-5.6-sol"},
            "canon": {"entities": [{"id": "hero", "kind": "character"}]},
        },
        continuity_ledger={"current_state": {"subjects": {"hero": {}}}},
    )


def test_global_context_preserves_full_coverage_without_duplicate_raw_payloads():
    chapters = [_chapter(position) for position in range(1, 49)]
    ledgers = {str(row.position): _ledger(row.position) for row in chapters}
    events = [
        {
            "business_id": f"fact-{position}",
            "source_chapter_business_id": f"chapter-{position}",
            "summary": "事件语义" * 200,
            "source_quote": "不应进入全局包",
            "source_hash": f"fact-source-{position}",
        }
        for position in range(1, 49)
    ]
    memories = [
        {
            "business_id": f"memory-{position}",
            "source_chapter_business_id": f"chapter-{position}",
            "character_business_id": "hero",
            "content": "人物认知变化" * 200 + "，但结论尚未确认。",
            "source_quote": "不应进入全局包",
            "source_hash": f"memory-source-{position}",
            "typed_fact_id": f"typed-fact-{position}",
            "typed_source_event_id": f"event-{position}",
        }
        for position in range(1, 49)
    ]

    payload = build_global_context(
        _revision(), chapters, ledgers, events, memories, [], ["canon:entity:hero"]
    )
    serialized = str(payload)

    assert global_context_chars(payload) <= GLOBAL_PAYLOAD_CHAR_BUDGET
    assert payload["input_manifest"]["chapter_positions"] == list(range(1, 49))
    assert payload["input_manifest"]["fact_count"] == 48
    assert payload["input_manifest"]["memory_count"] == 48
    assert set(payload["facts"]["chapter-1"]) == {"fact-1"}
    assert set(payload["character_memories"]["chapter-1"]) == {"memory-1"}
    assert "generation_plan" not in payload
    assert "source_quote" not in serialized
    assert "proof_spans" not in serialized
    assert payload["plan_binding"]["plan_hash"] == "plan-hash"
    assert payload["progression_arcs"][0]["growth"]["scope"] == "从村到县"
    assert payload["chapters"][0]["state_delta"]["entity_introductions"]
    assert payload["chapters"][0]["proof_refs"] == {
        "event:event-1": ["S0001"],
        "knowledge:1": ["S0001"],
    }
    assert payload["chapters"][0]["sentence_index"] == [
        {"sentence_id": "S0001", "text": "第1章发生了推进事件。"}
    ]
    assert payload["character_memories"]["chapter-1"]["memory-1"]["content"].endswith(
        "但结论尚未确认。"
    )
    assert (
        payload["character_memories"]["chapter-1"]["memory-1"]["typed_fact_id"]
        == "typed-fact-1"
    )
    assert payload["facts"]["chapter-1"]["fact-1"]["source_hash"] == "fact-source-1"
    assert payload_evidence_catalog(payload)["chapter-1"] == {"S0001"}


def test_global_context_fails_closed_when_nonredundant_state_exceeds_budget():
    revision = _revision()
    revision.continuity_ledger = {
        "current_state": {"subjects": {"hero": {"history": "状态" * 500_000}}}
    }

    with pytest.raises(ValueError, match="拒绝静默裁剪"):
        build_global_context(
            revision,
            [_chapter(1)],
            {"1": _ledger(1)},
            [],
            [],
            [],
            [],
        )


@pytest.mark.parametrize(
    "candidate",
    [
        {
            "business_id": "",
            "source_chapter_business_id": "chapter-1",
            "source_hash": "x",
        },
        {"business_id": "fact-1", "source_chapter_business_id": "", "source_hash": "x"},
        {"business_id": "fact-1", "source_chapter_business_id": "chapter-1"},
    ],
)
def test_global_context_rejects_incomplete_candidate_identity(candidate):
    with pytest.raises(ValueError, match="缺少 ID、来源章或 source hash"):
        build_global_context(
            _revision(),
            [_chapter(1)],
            {"1": _ledger(1)},
            [candidate],
            [],
            [],
            [],
        )


def test_global_context_rejects_duplicate_candidate_ids():
    candidate = {
        "business_id": "fact-1",
        "source_chapter_business_id": "chapter-1",
        "source_hash": "source-1",
    }
    with pytest.raises(ValueError, match="候选 ID 重复"):
        build_global_context(
            _revision(),
            [_chapter(1)],
            {"1": _ledger(1)},
            [candidate, dict(candidate)],
            [],
            [],
            [],
        )
