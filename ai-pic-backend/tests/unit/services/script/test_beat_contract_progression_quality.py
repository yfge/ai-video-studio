import pytest
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_quality_gate_rejects_repeated_screen_beats():
    payload = _valid_contract()
    for beat in payload["scenes"][0]["beats"]:
        beat["visible_event"] = "小机按下红色确认键，屏幕弹出权限警报。"
        beat["action_lines"] = [{"content": "小机按住红色确认键，警报灯持续闪烁。"}]
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "beat_progression_repetition" in failed
