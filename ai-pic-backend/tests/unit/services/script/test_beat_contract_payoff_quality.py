import pytest
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_quality_gate_requires_payoff_for_single_scene_script():
    payload = _valid_contract()
    for beat in payload["scenes"][0]["beats"]:
        beat["beat_type"] = (
            "conflict" if beat["order_index"] == 2 else beat["beat_type"]
        )
        beat.pop("payoff_tag", None)
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "payoff_required" in failed
