import json
from types import SimpleNamespace

import pytest
from app.schemas.narrative_extraction import NarrativeExtractionRequest
from app.services.narrative_memory import extraction_service as extraction_module
from app.services.narrative_memory.extraction_evidence import extraction_evidence_errors
from app.services.narrative_memory.extraction_service import NarrativeExtractionService
from app.services.narrative_memory.source_evidence import source_contains_evidence


@pytest.mark.asyncio
async def test_extraction_repairs_invalid_evidence_without_rewriting_source(
    monkeypatch,
):
    source = (
        "黎雁进入交接厅，发现褚蓝已经在了。“零号风钥完好。”她说。黎雁记住了交接完成。"
    )
    invalid = _payload(
        "黎雁进入交接厅，发现褚蓝已经在了。……褚蓝说……零号风钥完好。",
        "褚蓝说：“交接完成。”",
    )
    repaired_event = "黎雁进入交接厅，发现褚蓝已经在了……零号风钥完好"
    repaired_memory = "黎雁记住了交接完成"
    manager = _Manager(
        [
            invalid,
            {
                "repairs": [
                    {"kind": "events", "index": 0, "evidence": repaired_event},
                    {"kind": "memories", "index": 0, "evidence": repaired_memory},
                ]
            },
        ]
    )
    service = _service(monkeypatch, manager, source)

    payload = await service.extract(
        SimpleNamespace(id=1),
        NarrativeExtractionRequest(
            source_scope="novel_chapter",
            source_artifact_business_id="chapter-a",
            model="deepseek:deepseek-v4-flash",
        ),
        SimpleNamespace(id=1),
    )

    assert len(manager.prompts) == 2
    repair_prompt = manager.prompts[1]
    assert "只为每个报错 kind/index 返回一条 repair" in repair_prompt
    assert '"kind": "events"' in repair_prompt
    assert '"kind": "memories"' in repair_prompt
    assert payload.events[0].candidate_evidence == {
        "source_quote": repaired_event,
        "source_quote_verified": True,
    }
    assert payload.memories[0].candidate_evidence == {
        "source_quote": repaired_memory,
        "source_quote_verified": True,
    }


@pytest.mark.asyncio
async def test_extraction_uses_dedicated_patch_after_generic_evidence_noop(
    monkeypatch,
):
    source = (
        "褚蓝把零号风钥放在桌上。"
        "黎雁问：谁篡改了季风窗口数据？"
        "黎雁注意到他说“原始记录可以调阅”时眼神闪烁。"
    )
    invalid = _payload(
        "褚蓝把零号风钥放在桌上",
        "谁篡改了季风窗口数据？……裴衡说‘原始记录可以调阅’时眼神闪烁",
    )
    evidence_patch = {
        "repairs": [
            {
                "kind": "memories",
                "index": 0,
                "evidence": (
                    "谁篡改了季风窗口数据？……黎雁注意到他说“原始记录可以调阅”时眼神闪烁"
                ),
            }
        ]
    }
    manager = _Manager([invalid, evidence_patch])
    service = _service(monkeypatch, manager, source)

    payload = await service.extract(
        SimpleNamespace(id=1),
        NarrativeExtractionRequest(
            source_scope="novel_chapter",
            source_artifact_business_id="chapter-a",
            model="deepseek:deepseek-v4-flash",
        ),
        SimpleNamespace(id=1),
    )

    assert len(manager.prompts) == 2
    assert "只为每个报错 kind/index 返回一条 repair" in manager.prompts[1]
    assert (
        payload.memories[0]
        .candidate_evidence["source_quote"]
        .startswith("谁篡改了季风窗口数据？")
    )


def test_evidence_validation_collects_all_errors_and_aligns_valid_items():
    source = (
        "黎雁进入交接厅，发现褚蓝已经在了。“零号风钥完好。”她说。黎雁记住了交接完成。"
    )
    normalized = _payload(
        "褚蓝说：“零号风钥完好。”",
        "褚蓝说：“交接完成。”",
    )
    valid_evidence = "黎雁进入交接厅，发现褚蓝已经在了。零号风钥完好。"
    normalized["events"].append(
        {
            **normalized["events"][0],
            "evidence": valid_evidence,
        }
    )

    errors = extraction_evidence_errors(normalized, source)

    assert [error["loc"] for error in errors or []] == [
        ["events", 0, "evidence"],
        ["memories", 0, "evidence"],
    ]
    assert all(error["type"] == "value_error.source_evidence" for error in errors or [])
    assert normalized["events"][1]["evidence"] != valid_evidence
    assert source_contains_evidence(
        source,
        normalized["events"][1]["evidence"],
    )


def test_evidence_errors_identify_rewritten_and_out_of_order_fragments():
    source = (
        "褚蓝从侧门走进来，手里托着金属盒。"
        "褚蓝走到长桌前，把金属盒放在桌面上。"
        "钥匙根部刻着数字0823。"
        "裴衡宣布九月二十日后窗口关闭。"
        "轮胎侧壁也写着数字0823。"
    )
    normalized = _payload(
        "褚蓝从侧门走进来，手里托着金属盒……他走到长桌前，把金属盒放在桌面上",
        "裴衡宣布九月二十日后窗口关闭……钥匙根部刻着数字0823……轮胎侧壁也写着数字0823",
    )

    errors = extraction_evidence_errors(normalized, source) or []
    messages = [error["msg"] for error in errors]

    assert '"fragment_index":2' in messages[0]
    assert '"failure_kind":"rewritten_or_missing"' in messages[0]
    assert '"verified_source_fragments"' in messages[0]
    assert "褚蓝从侧门走进来，手里托着金属盒" in messages[0]
    assert '"failure_kind":"out_of_order"' in messages[1]
    assert "按正文顺序重选该片段及其后片段" in messages[1]


def _service(monkeypatch, manager, source):
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
    return service


def _payload(event_evidence: str, memory_evidence: str) -> dict:
    return {
        "events": [
            {
                "event_type": "action",
                "summary": "黎雁进入交接厅并确认风钥完好",
                "participant_character_ids": [],
                "occurred_at_anchor_business_id": "anchor-a",
                "presentation": "on_screen",
                "audience_disclosure": "revealed",
                "evidence": event_evidence,
            }
        ],
        "memories": [
            {
                "character_business_id": "character-a",
                "virtual_ip_business_id": "vip-a",
                "memory_type": "witnessed",
                "content": "黎雁记住交接完成",
                "belief": None,
                "belief_confidence": 1.0,
                "perception": None,
                "emotional_impact": [],
                "salience": 0.8,
                "occurred_at_anchor_business_id": "anchor-a",
                "learned_at_anchor_business_id": "anchor-a",
                "effective_from_anchor_business_id": "anchor-a",
                "invalidated_at_anchor_business_id": None,
                "growth_delta": None,
                "evidence": memory_evidence,
            }
        ],
    }


class _Manager:
    def __init__(self, outputs: list[dict]):
        self.outputs = outputs
        self.prompts = []

    async def generate_text(self, prompt: str, **_kwargs):
        self.prompts.append(prompt)
        output = self.outputs[len(self.prompts) - 1]
        return SimpleNamespace(
            success=True,
            data=json.dumps(output, ensure_ascii=False),
            provider="deepseek",
            model="deepseek-v4-flash",
            usage={},
            metadata={},
        )
