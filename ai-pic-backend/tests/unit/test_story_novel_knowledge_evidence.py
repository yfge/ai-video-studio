import json
from types import SimpleNamespace

import anyio
from app.services.narrative_memory.candidate_verification import (
    complete_novel_candidate_set,
)
from app.services.narrative_memory.knowledge_evidence import (
    knowledge_evidence_violations,
)
from app.services.story.story_novel_ai_prompts import chapter_prompt
from app.services.story.story_novel_state_evidence_repair import repair_state_evidence
from app.services.story.story_novel_state_extraction import _validation_result

BODY = (
    "港务监理把潮汐测针交给王明。"
    "王明确认自己已经成为潮汐测针的持有人。"
    "老拐确认终端已将潮汐测针持有人改为王明。"
)
EVENT_QUOTE = (
    "港务监理把潮汐测针交给王明。"
    "……王明确认自己已经成为潮汐测针的持有人。"
    "……老拐确认终端已将潮汐测针持有人改为王明。"
)
CANON = {
    "entities": [
        {"id": "char-wang", "kind": "character", "name": "王明"},
        {"id": "char-guai", "kind": "character", "name": "老拐"},
    ]
}


def _delta() -> dict:
    return {
        "occurred_event_ids": ["event-transfer"],
        "future_event_audit": {},
        "knowledge_grants": [
            {
                "character_id": "char-wang",
                "fact_id": "fact-owner",
                "source_event_id": "event-transfer",
            },
            {
                "character_id": "char-guai",
                "fact_id": "fact-owner",
                "source_event_id": "event-transfer",
            },
        ],
        "evidence": {"event-transfer": EVENT_QUOTE},
        "knowledge_evidence": {
            "char-wang|fact-owner|event-transfer": (
                "王明确认自己已经成为潮汐测针的持有人。"
            ),
            "char-guai|fact-owner|event-transfer": (
                "老拐确认终端已将潮汐测针持有人改为王明。"
            ),
        },
    }


def test_knowledge_evidence_is_continuous_and_bound_to_event_fragment():
    assert knowledge_evidence_violations(BODY, _delta(), CANON) == []

    invalid = _delta()
    invalid["knowledge_evidence"][
        "char-guai|fact-owner|event-transfer"
    ] = "港务监理把潮汐测针交给王明。"
    messages = [
        item["message"] for item in knowledge_evidence_violations(BODY, invalid, CANON)
    ]
    assert any("未明确对应角色获知关系" in item for item in messages)


def test_state_parse_requires_every_planned_knowledge_quote_with_canon():
    invalid = _delta()
    invalid["knowledge_evidence"].pop("char-guai|fact-owner|event-transfer")

    normalized, error, issues = _validation_result(
        json.dumps(invalid, ensure_ascii=False),
        chapter_plan={"canon_refs": [], "timeline_event_bindings": {}},
        content_text=BODY,
        current_timeline=[],
        future_event_catalog=[],
        canon=CANON,
    )

    assert normalized is not None
    assert "角色获知证据必须逐项等于 knowledge_grants" in error
    assert issues


def test_chapter_prompt_requires_explicit_per_grant_acquisition_sentence():
    prompt = chapter_prompt(
        context_pack={"chapter_contract": {"knowledge_grants": []}},
        target_chars=4000,
    )
    assert "每一项都必须在正文里有一条连续、独立的获知句" in prompt
    assert "不要用省略拼接、隐含在场或旁人对话代替" in prompt


def test_candidate_completeness_uses_frozen_persisted_character_grants():
    entry = {
        "memory_grant_keys": [["char-wang", "fact-owner", "event-transfer"]],
        "state_delta": _delta(),
    }
    events = [
        SimpleNamespace(candidate_evidence={"typed_event_ids": ["event-transfer"]})
    ]
    memories = [
        SimpleNamespace(
            candidate_evidence={
                "typed_character_id": "char-wang",
                "typed_fact_id": "fact-owner",
                "typed_source_event_id": "event-transfer",
            }
        )
    ]

    assert complete_novel_candidate_set(entry, events, memories)


def test_evidence_only_repair_can_replace_knowledge_quote_without_state_changes():
    delta = _delta()
    delta["state_transitions"] = [
        {
            "subject_id": "object-probe",
            "field": "owner_id",
            "from_value": None,
            "to_value": "char-wang",
            "reason": "正文交接",
        }
    ]

    async def generate(_revision, _prompt, **_kwargs):
        return json.dumps(
            {
                "evidence": delta["evidence"],
                "knowledge_evidence": delta["knowledge_evidence"],
                "timeline_evidence": {},
            },
            ensure_ascii=False,
        )

    async def run():
        return await repair_state_evidence(
            object(),
            chapter_plan={
                "knowledge_grants": delta["knowledge_grants"],
                "canon_refs": [],
                "timeline_event_bindings": {},
            },
            content_text=BODY,
            current_timeline=[],
            delta=delta,
            diagnostics=[],
            error="证据错误",
            generate_text=generate,
        )

    repaired = anyio.run(run)
    normalized = json.loads(repaired)

    assert normalized["state_transitions"] == delta["state_transitions"]
    assert normalized["knowledge_evidence"] == delta["knowledge_evidence"]
