import pytest
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_quality_gate_requires_scene_question_and_turn():
    payload = _valid_contract()
    payload["scenes"][0]["conflict"]["question"] = "   "
    payload["scenes"][0]["conflict"]["turn"] = "出现转折"
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "scene_conflict_question" in failed
    assert "scene_conflict_turn" in failed
