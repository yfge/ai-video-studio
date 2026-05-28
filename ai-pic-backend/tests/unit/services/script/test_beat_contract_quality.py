import pytest
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
from app.services.script_quality_gate_checks import beat_contract_check
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_quality_gate_accepts_structured_contract():
    contract = normalize_script_beat_contract(_valid_contract())

    report = evaluate_beat_contract_quality(contract)

    assert report["passed"] is True
    assert report["failed_checks"] == []


@pytest.mark.unit
def test_quality_gate_rejects_thin_scene_with_too_few_beats():
    payload = _valid_contract()
    payload["scenes"][0]["beats"] = payload["scenes"][0]["beats"][:1]
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    assert report["passed"] is False
    assert "scene_min_beats" in {item["check_id"] for item in report["failed_checks"]}


@pytest.mark.unit
def test_quality_gate_rejects_missing_payoff_for_multi_scene_episode():
    payload = _valid_contract()
    second = dict(payload["scenes"][0])
    second["scene_number"] = 2
    second["dramatic_role"] = "cliffhanger"
    second["beats"] = [dict(beat) for beat in payload["scenes"][0]["beats"]]
    for beat in second["beats"]:
        beat["beat_type"] = "conflict"
        beat.pop("payoff_tag", None)
    second["beats"][-1]["beat_type"] = "cliffhanger"
    second["beats"][-1]["cliffhanger_tag"] = "new_threat"
    payload["scenes"].append(second)
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    assert report["passed"] is False
    assert "payoff_required" in {item["check_id"] for item in report["failed_checks"]}


@pytest.mark.unit
def test_quality_gate_rejects_fallback_detected_contract():
    contract = normalize_script_beat_contract(
        {
            "scenes": [{"scene_number": 1, "summary": "只有旁白"}],
            "dialogues": [
                {
                    "scene_number": 1,
                    "character": "旁白",
                    "content": "只有旁白",
                    "fallback": True,
                }
            ],
            "stage_directions": [],
        }
    )

    report = evaluate_beat_contract_quality(contract)

    assert report["passed"] is False
    assert "fallback_content" in {item["check_id"] for item in report["failed_checks"]}


@pytest.mark.unit
def test_quality_gate_check_reports_failed_beat_contract():
    contract = normalize_script_beat_contract(
        {
            "scenes": [{"scene_number": 1, "summary": "只有旁白"}],
            "dialogues": [
                {
                    "scene_number": 1,
                    "character": "旁白",
                    "content": "只有旁白",
                    "fallback": True,
                }
            ],
            "stage_directions": [],
        }
    )
    content = {"structured_script_contract": contract.model_dump(mode="json")}
    content["structured_script_contract"]["fallback_detected"] = True

    check = beat_contract_check(content)

    assert check is not None
    assert check["id"] == "script_beat_contract"
    assert check["passed"] is False
