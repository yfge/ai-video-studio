import json
from types import SimpleNamespace

import pytest
from app.schemas.narrative_extraction import NarrativeExtractionRequest
from app.services.narrative_memory import extraction_service as extraction_module
from app.services.narrative_memory.extraction_service import NarrativeExtractionService


@pytest.mark.asyncio
async def test_strict_extraction_repairs_extra_untyped_candidates(monkeypatch):
    source = "黎雁确认交接完成"
    event = {
        "event_type": "action",
        "summary": source,
        "typed_event_ids": ["event-current"],
        "participant_character_ids": [],
        "occurred_at_anchor_business_id": "anchor-a",
        "presentation": "on_screen",
        "audience_disclosure": "revealed",
        "evidence": source,
    }
    untyped_event = {**event, "typed_event_ids": []}
    untyped_memory = {
        "character_business_id": "character-a",
        "virtual_ip_business_id": "vip-a",
        "typed_character_id": None,
        "typed_fact_id": None,
        "typed_source_event_id": None,
        "memory_type": "witnessed",
        "content": source,
        "belief": None,
        "belief_confidence": None,
        "perception": None,
        "emotional_impact": [],
        "salience": 0.8,
        "occurred_at_anchor_business_id": "anchor-a",
        "learned_at_anchor_business_id": "anchor-a",
        "effective_from_anchor_business_id": "anchor-a",
        "invalidated_at_anchor_business_id": None,
        "growth_delta": None,
        "evidence": source,
    }
    manager = _Manager(
        [
            {"events": [event, untyped_event], "memories": [untyped_memory]},
            {"events": [event], "memories": []},
        ]
    )
    monkeypatch.setattr(extraction_module.ai_service, "ai_manager", manager)
    monkeypatch.setattr(
        extraction_module.CandidateService,
        "ingest",
        lambda _self, _story, payload, _user, **_kwargs: payload,
    )
    service = NarrativeExtractionService(
        SimpleNamespace(list_story_characters=lambda _story_id: [], commit=lambda: None)
    )
    anchor = SimpleNamespace(
        business_id="anchor-a",
        source_artifact_type="novel_chapter",
        source_artifact_business_id="chapter-a",
        source_version=1,
        source_hash="source-hash",
    )
    monkeypatch.setattr(service, "_source", lambda *_args: ([anchor], source))
    monkeypatch.setattr(
        service,
        "_candidate_contract",
        lambda *_args: (True, {}, {"event-current": source}),
    )

    payload = await service.extract(
        SimpleNamespace(id=1),
        NarrativeExtractionRequest(
            source_scope="novel_chapter",
            source_artifact_business_id="chapter-a",
            model="deepseek:deepseek-v4-pro",
        ),
        SimpleNamespace(id=1),
    )

    assert len(manager.prompts) == 2
    assert "客观事件未逐项覆盖 typed event" in manager.prompts[1]
    assert "角色知识未逐项覆盖 typed grant" in manager.prompts[1]
    assert len(payload.events) == 1
    assert payload.memories == []


class _Manager:
    def __init__(self, outputs):
        self.outputs = outputs
        self.prompts = []

    async def generate_text(self, prompt, **_kwargs):
        self.prompts.append(prompt)
        return SimpleNamespace(
            success=True,
            data=json.dumps(self.outputs[len(self.prompts) - 1], ensure_ascii=False),
            provider="deepseek",
            model="deepseek-v4-pro",
            usage={},
            metadata={},
        )
