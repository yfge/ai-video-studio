from types import SimpleNamespace

import pytest
from app.core.exceptions import ServiceError
from app.schemas.narrative_extraction import (
    NarrativeExtractionEnvelope,
    NarrativeExtractionRequest,
)
from app.services.narrative_memory import extraction_service as extraction_module
from app.services.narrative_memory.extraction_service import NarrativeExtractionService
from app.services.narrative_memory.source_evidence import source_contains_evidence
from tests.unit.services.test_narrative_memory_extraction_repair import (
    _Manager,
    _payload,
)


@pytest.mark.asyncio
async def test_invalid_evidence_patch_fails_without_ingest(monkeypatch):
    source = "褚蓝把零号风钥放在桌上。黎雁记住交接完成。"
    invalid = _payload(
        "褚蓝把零号风钥放在桌上",
        "裴衡说：“黎雁记住交接完成。”",
    )
    invalid_patch = {
        "repairs": [
            {
                "kind": "events|memories",
                "index": 0,
                "evidence": "不存在的证据",
            }
        ]
    }
    manager = _Manager([invalid, invalid_patch])
    monkeypatch.setattr(extraction_module.ai_service, "ai_manager", manager)
    ingested = []
    monkeypatch.setattr(
        extraction_module.CandidateService,
        "ingest",
        lambda _self, _story, payload, _user, **_kwargs: ingested.append(payload),
    )
    service = NarrativeExtractionService(
        SimpleNamespace(
            list_story_characters=lambda _story_id: [],
            commit=lambda: None,
        )
    )
    anchor = SimpleNamespace(
        business_id="anchor-a",
        source_artifact_type="novel_chapter",
        source_artifact_business_id="chapter-a",
        source_version=1,
        source_hash="source-hash",
    )
    monkeypatch.setattr(service, "_source", lambda *_args: ([anchor], source))

    with pytest.raises(ServiceError, match="正文证据无效"):
        await service.extract(
            SimpleNamespace(id=1),
            NarrativeExtractionRequest(
                source_scope="novel_chapter",
                source_artifact_business_id="chapter-a",
                model="deepseek:deepseek-v4-flash",
            ),
            SimpleNamespace(id=1),
        )

    assert len(manager.prompts) == 2
    assert ingested == []


@pytest.mark.parametrize("evidence", ["   ", "…… ", "..."])
def test_semantic_empty_evidence_is_rejected(evidence):
    payload = _payload(evidence, "黎雁记住交接完成")

    with pytest.raises(ValueError, match="semantic characters"):
        NarrativeExtractionEnvelope.model_validate(payload)

    assert source_contains_evidence("任意正文", evidence) is False


@pytest.mark.asyncio
@pytest.mark.parametrize("malformed_patch", [{}, "NOT JSON"])
async def test_malformed_dedicated_patch_cannot_delete_valid_candidates(
    monkeypatch, malformed_patch
):
    source = "褚蓝把零号风钥放在桌上。黎雁记住交接完成。"
    invalid = _payload(
        "褚蓝把零号风钥放在桌上",
        "不存在的记忆证据",
    )
    manager = _Manager([invalid, malformed_patch])
    monkeypatch.setattr(extraction_module.ai_service, "ai_manager", manager)
    ingested = []
    monkeypatch.setattr(
        extraction_module.CandidateService,
        "ingest",
        lambda _self, _story, payload, _user, **_kwargs: ingested.append(payload),
    )
    service, request = _service(monkeypatch, source)

    with pytest.raises(ServiceError, match="正文证据无效"):
        await service.extract(SimpleNamespace(id=1), request, SimpleNamespace(id=1))

    assert ingested == []


@pytest.mark.asyncio
async def test_only_explicit_null_can_quarantine_invalid_memory(monkeypatch):
    source = "褚蓝把零号风钥放在桌上。黎雁记住交接完成。"
    invalid = _payload(
        "褚蓝把零号风钥放在桌上",
        "不存在的记忆证据",
    )
    patch = {"repairs": [{"kind": "memories", "index": 0, "evidence": None}]}
    manager = _Manager([invalid, patch])
    monkeypatch.setattr(extraction_module.ai_service, "ai_manager", manager)
    monkeypatch.setattr(
        extraction_module.CandidateService,
        "ingest",
        lambda _self, _story, payload, _user, **_kwargs: payload,
    )
    service, request = _service(monkeypatch, source)

    payload = await service.extract(
        SimpleNamespace(id=1), request, SimpleNamespace(id=1)
    )

    assert len(payload.events) == 1
    assert payload.memories == []


@pytest.mark.asyncio
async def test_evidence_repair_preserves_valid_candidate_identity(monkeypatch):
    source = "褚蓝把零号风钥放在桌上。黎雁确认交接完成。"
    invalid = _payload("不存在的事件证据", "黎雁确认交接完成")
    valid_event = {
        **invalid["events"][0],
        "summary": "KEEP_VALID_EVENT",
        "evidence": "褚蓝把零号风钥放在桌上",
    }
    invalid["events"].append(valid_event)
    patch = {"repairs": [{"kind": "events", "index": 0, "evidence": None}]}
    manager = _Manager([invalid, patch])
    monkeypatch.setattr(extraction_module.ai_service, "ai_manager", manager)
    monkeypatch.setattr(
        extraction_module.CandidateService,
        "ingest",
        lambda _self, _story, payload, _user, **_kwargs: payload,
    )
    service, request = _service(monkeypatch, source)

    payload = await service.extract(
        SimpleNamespace(id=1), request, SimpleNamespace(id=1)
    )

    assert [item.summary for item in payload.events] == ["KEEP_VALID_EVENT"]
    assert len(manager.prompts) == 2
    assert "JSON Schema，请修复" not in manager.prompts[1]


@pytest.mark.asyncio
async def test_explicit_null_cannot_delete_all_objective_events(monkeypatch):
    source = "黎雁确认交接完成。"
    invalid = _payload("不存在的事件证据", "黎雁确认交接完成")
    patch = {"repairs": [{"kind": "events", "index": 0, "evidence": None}]}
    manager = _Manager([invalid, patch])
    monkeypatch.setattr(extraction_module.ai_service, "ai_manager", manager)
    ingested = []
    monkeypatch.setattr(
        extraction_module.CandidateService,
        "ingest",
        lambda _self, _story, payload, _user, **_kwargs: ingested.append(payload),
    )
    service, request = _service(monkeypatch, source)

    with pytest.raises(ServiceError, match="正文证据无效"):
        await service.extract(SimpleNamespace(id=1), request, SimpleNamespace(id=1))

    assert ingested == []


def _service(monkeypatch, source):
    service = NarrativeExtractionService(
        SimpleNamespace(
            list_story_characters=lambda _story_id: [],
            commit=lambda: None,
        )
    )
    anchor = SimpleNamespace(
        business_id="anchor-a",
        source_artifact_type="novel_chapter",
        source_artifact_business_id="chapter-a",
        source_version=1,
        source_hash="source-hash",
    )
    monkeypatch.setattr(service, "_source", lambda *_args: ([anchor], source))
    return service, NarrativeExtractionRequest(
        source_scope="novel_chapter",
        source_artifact_business_id="chapter-a",
        model="deepseek:deepseek-v4-flash",
    )
