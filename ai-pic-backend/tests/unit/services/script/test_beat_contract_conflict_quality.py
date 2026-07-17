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


@pytest.mark.unit
def test_quality_gate_rejects_abstract_scene_stakes_and_opposition():
    payload = _valid_contract()
    payload["scenes"][0]["conflict"]["stakes"] = "小机压力越来越大。"
    payload["scenes"][0]["conflict"]["opposition"] = "混乱局面阻止小机继续查。"
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "scene_conflict_stakes" in failed
    assert "scene_conflict_opposition" in failed


@pytest.mark.unit
def test_quality_gate_accepts_concrete_publication_deadline_as_stakes():
    payload = _valid_contract()
    payload["scenes"][0]["conflict"][
        "stakes"
    ] = "她的表达会被复制进下周全员播放模板，个人形象将被长期占用。"
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert "scene_conflict_stakes" not in failed
