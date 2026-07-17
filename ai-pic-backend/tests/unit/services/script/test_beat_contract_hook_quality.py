import pytest
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_quality_gate_rejects_slow_opening_hook():
    payload = _valid_contract()
    for beat, duration in zip(payload["scenes"][0]["beats"], [5, 5, 5], strict=True):
        beat["duration_seconds"] = duration
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "opening_hook_duration" in failed


@pytest.mark.unit
def test_quality_gate_rejects_opening_hook_without_immediate_threat():
    payload = _valid_contract()
    first_beat = payload["scenes"][0]["beats"][0]
    first_beat["visible_event"] = "小机推开玻璃门，灯带依次亮起。"
    first_beat["action_lines"] = [{"content": "小机把背包放到桌面，整理袖口。"}]
    first_beat["dialogue_lines"] = [{"character": "小机", "content": "我到了。"}]
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "opening_hook_substance" in failed


@pytest.mark.unit
def test_quality_gate_accepts_visible_claim_and_workload_contradiction():
    payload = _valid_contract()
    first_beat = payload["scenes"][0]["beats"][0]
    first_beat["visible_event"] = "两块屏幕闪出“AI落地”，旁边堆着仍待人工填写的表格。"
    first_beat["action_lines"] = [
        {"content": "林妹妹把工牌拍在表格旁，屏幕继续轮播“智能提效”。"}
    ]
    first_beat["dialogue_lines"] = [
        {"character": "林妹妹", "content": "技术升级，还是PPT升级？"}
    ]
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert "opening_hook_substance" not in failed
