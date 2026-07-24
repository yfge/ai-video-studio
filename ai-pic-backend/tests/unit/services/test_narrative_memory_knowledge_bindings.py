from types import SimpleNamespace

from app.services.narrative_memory.extraction_candidates import (
    build_candidate_payload,
    knowledge_character_bindings,
)
from app.services.narrative_memory.extraction_prompt import build_extraction_prompt
from app.services.narrative_memory.novel_extraction_contract import (
    novel_candidate_contract,
)
from tests.unit.services.narrative_memory_claim_fixtures import (
    anchor,
    event_evidence,
    normalized,
)


def test_knowledge_bindings_map_canon_ids_to_persisted_story_characters():
    quote = "黎雁确认零号风钥移交完成"
    bindings = knowledge_character_bindings(
        {"entities": [{"id": "li-yan", "kind": "character", "name": "黎雁"}]},
        {
            "knowledge_grants": [
                {
                    "character_id": "li-yan",
                    "fact_id": "fact-key-received",
                    "source_event_id": "event-current",
                }
            ],
            "knowledge_evidence": {"li-yan|fact-key-received|event-current": quote},
        },
        [{"character_business_id": "uuid-li-yan", "name": "黎雁-极昼邮路验收"}],
    )
    assert bindings["uuid-li-yan"]["grants"][0]["evidence"] == quote

    extracted = normalized()
    extracted["memories"][0].update(
        character_business_id="uuid-li-yan",
        virtual_ip_business_id="vip-li-yan",
        typed_character_id="li-yan",
    )
    extracted["events"][0]["participant_character_ids"] = []
    payload = build_candidate_payload(
        extracted,
        [anchor()],
        [
            {
                "character_business_id": "uuid-li-yan",
                "virtual_ip_business_id": "vip-li-yan",
                "name": "黎雁-极昼邮路验收",
            }
        ],
        strict=True,
        memory_character_bindings=bindings,
        occurred_event_evidence=event_evidence(),
    )
    assert payload.memories[0].candidate_evidence["typed_character_id"] == "li-yan"


def test_knowledge_bindings_skip_canon_npc_without_story_character():
    bindings = knowledge_character_bindings(
        {
            "entities": [
                {"id": "li-yan", "kind": "character", "name": "黎雁"},
                {"id": "harbor-supervisor", "kind": "character", "name": "港务监理"},
            ]
        },
        {
            "knowledge_grants": [
                {
                    "character_id": "li-yan",
                    "fact_id": "fact-a",
                    "source_event_id": "event-a",
                },
                {
                    "character_id": "harbor-supervisor",
                    "fact_id": "fact-b",
                    "source_event_id": "event-b",
                },
            ],
            "knowledge_evidence": {
                "li-yan|fact-a|event-a": "黎雁确认事实A",
                "harbor-supervisor|fact-b|event-b": "港务监理确认事实B",
            },
        },
        [{"character_business_id": "uuid-li", "name": "黎雁"}],
    )
    assert set(bindings) == {"uuid-li"}


def test_novel_contract_freezes_only_mapped_character_grant_keys():
    quote = "黎雁确认事实A"
    delta = {
        "occurred_event_ids": ["event-a"],
        "evidence": {"event-a": quote},
        "knowledge_grants": [
            {
                "character_id": "li-yan",
                "fact_id": "fact-a",
                "source_event_id": "event-a",
            },
            {
                "character_id": "harbor-supervisor",
                "fact_id": "fact-b",
                "source_event_id": "event-a",
            },
        ],
        "knowledge_evidence": {
            "li-yan|fact-a|event-a": quote,
            "harbor-supervisor|fact-b|event-a": "港务监理确认事实B",
        },
    }
    export = SimpleNamespace(
        generation_plan={
            "schema": "story_novel_generation_plan.v2",
            "canon": {
                "entities": [
                    {"id": "li-yan", "kind": "character", "name": "黎雁"},
                    {
                        "id": "harbor-supervisor",
                        "kind": "character",
                        "name": "港务监理",
                    },
                ]
            },
        },
        continuity_ledger={"chapters": {"1": {"state_delta": delta}}},
    )
    chapter = SimpleNamespace(position=1, novel_export=export)
    repo = SimpleNamespace(novel_chapter=lambda *_args: chapter)

    strict, bindings, events, keys = novel_candidate_contract(
        repo,
        object(),
        SimpleNamespace(
            source_scope="novel_chapter", source_artifact_business_id="chapter-a"
        ),
        [{"character_business_id": "character-li", "name": "黎雁"}],
    )

    assert strict is True
    assert events == {"event-a": quote}
    assert set(bindings) == {"character-li"}
    assert keys == [["li-yan", "fact-a", "event-a"]]


def test_memory_prompt_uses_each_grants_own_knowledge_evidence():
    prompt = build_extraction_prompt(
        "正文",
        [],
        [],
        {
            "event_evidence": {"event-a": "完整事件"},
            "required_memory_grants": {
                "character-a": {
                    "grants": [
                        {
                            "character_id": "char-a",
                            "fact_id": "fact-a",
                            "source_event_id": "event-a",
                            "evidence": "角色甲确认事实A",
                        }
                    ]
                }
            },
        },
    )

    assert "对应 grant 自己的 evidence" in prompt
    assert "而不是整段 source event" in prompt
