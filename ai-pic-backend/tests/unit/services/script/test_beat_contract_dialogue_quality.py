import pytest
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_quality_gate_rejects_repeated_dialogue_lines():
    payload = _valid_contract()
    for beat in payload["scenes"][0]["beats"]:
        for line in beat["dialogue_lines"]:
            line["content"] = "证据在这里。"
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "dialogue_progression_repetition" in failed


@pytest.mark.unit
def test_quality_gate_rejects_long_dialogue_line():
    payload = _valid_contract()
    line = payload["scenes"][0]["beats"][0]["dialogue_lines"][0]
    line["content"] = "这条线索必须马上交给审计员核对签名"
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "dialogue_line_length" in failed
