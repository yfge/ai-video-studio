from types import SimpleNamespace

import pytest
from app.core.exceptions import ServiceError
from app.services.narrative_memory.candidate_verification import (
    complete_novel_candidate_set,
)
from app.services.narrative_memory.extraction_candidates import build_candidate_payload
from tests.unit.services.narrative_memory_claim_fixtures import anchor as _anchor
from tests.unit.services.narrative_memory_claim_fixtures import (
    characters as _characters,
)
from tests.unit.services.narrative_memory_claim_fixtures import (
    event_evidence as _event_evidence,
)
from tests.unit.services.narrative_memory_claim_fixtures import (
    memory_bindings as _memory_bindings,
)
from tests.unit.services.narrative_memory_claim_fixtures import (
    normalized as _normalized,
)


def test_strict_events_cover_each_typed_event_with_its_exact_evidence():
    normalized = _normalized()
    normalized["events"].append(
        {
            **normalized["events"][0],
            "summary": "模型概括可被覆盖",
            "typed_event_ids": ["event-second"],
            "evidence": "黎雁确认移交完成",
        }
    )

    payload = build_candidate_payload(
        normalized,
        [_anchor()],
        _characters(),
        strict=True,
        memory_character_bindings=_memory_bindings(),
        occurred_event_evidence={
            "event-current": "黎雁确认零号风钥移交完成",
            "event-second": "黎雁确认移交完成",
        },
    )

    assert [item.candidate_evidence["typed_event_ids"] for item in payload.events] == [
        ["event-current"],
        ["event-second"],
    ]

    normalized["events"][1]["evidence"] = "黎雁接过零号风钥"
    with pytest.raises(ServiceError, match="证据未绑定对应 typed event"):
        build_candidate_payload(
            normalized,
            [_anchor()],
            _characters(),
            strict=True,
            memory_character_bindings=_memory_bindings(),
            occurred_event_evidence={
                "event-current": "黎雁确认零号风钥移交完成",
                "event-second": "黎雁确认移交完成",
            },
        )


def test_strict_events_reject_multi_id_row_and_empty_row():
    normalized = _normalized()
    normalized["events"].append(
        {
            **normalized["events"][0],
            "typed_event_ids": [],
            "evidence": "黎雁确认移交完成",
        }
    )
    normalized["events"][0]["typed_event_ids"] = ["event-current", "event-second"]

    with pytest.raises(ServiceError, match="未逐项覆盖 typed event"):
        build_candidate_payload(
            normalized,
            [_anchor()],
            _characters(),
            strict=True,
            memory_character_bindings=_memory_bindings(),
            occurred_event_evidence={
                **_event_evidence(),
                "event-second": "黎雁确认移交完成",
            },
        )


def test_strict_memories_cover_each_typed_grant_for_same_character():
    normalized = _normalized()
    second_quote = "黎雁得知季风窗口将在九月二十日关闭"
    normalized["events"].append(
        {
            **normalized["events"][0],
            "typed_event_ids": ["event-second"],
            "evidence": second_quote,
        }
    )
    normalized["memories"].append(
        {
            **normalized["memories"][0],
            "typed_fact_id": "fact-window-deadline",
            "typed_source_event_id": "event-second",
            "evidence": second_quote,
        }
    )
    bindings = _memory_bindings()
    bindings["li-yan"]["grants"].append(
        {
            "character_id": "canon-li-yan",
            "fact_id": "fact-window-deadline",
            "source_event_id": "event-second",
            "evidence": second_quote,
        }
    )

    payload = build_candidate_payload(
        normalized,
        [_anchor()],
        _characters(),
        strict=True,
        memory_character_bindings=bindings,
        occurred_event_evidence={
            **_event_evidence(),
            "event-second": second_quote,
        },
    )

    assert {item.candidate_evidence["typed_fact_id"] for item in payload.memories} == {
        "fact-key-received",
        "fact-window-deadline",
    }
    normalized["memories"].pop()
    with pytest.raises(ServiceError, match="未逐项覆盖 typed grant"):
        build_candidate_payload(
            normalized,
            [_anchor()],
            _characters(),
            strict=True,
            memory_character_bindings=bindings,
            occurred_event_evidence={
                **_event_evidence(),
                "event-second": second_quote,
            },
        )


def test_complete_candidate_set_requires_event_and_knowledge_coverage():
    entry = {
        "state_delta": {
            "occurred_event_ids": ["event-a", "event-b"],
            "knowledge_grants": [
                {
                    "character_id": "char-a",
                    "fact_id": "fact-a",
                    "source_event_id": "event-a",
                },
                {
                    "character_id": "char-b",
                    "fact_id": "fact-b",
                    "source_event_id": "event-b",
                },
            ],
        }
    }
    events = [
        SimpleNamespace(candidate_evidence={"typed_event_ids": ["event-a"]}),
        SimpleNamespace(candidate_evidence={"typed_event_ids": ["event-b"]}),
    ]
    memories = [
        SimpleNamespace(
            candidate_evidence={
                "typed_character_id": "char-a",
                "typed_fact_id": "fact-a",
                "typed_source_event_id": "event-a",
            }
        )
    ]

    assert not complete_novel_candidate_set(entry, events, memories)
    memories.append(
        SimpleNamespace(
            candidate_evidence={
                "typed_character_id": "char-b",
                "typed_fact_id": "fact-b",
                "typed_source_event_id": "event-b",
            }
        )
    )
    assert complete_novel_candidate_set(entry, events, memories)
