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
def test_quality_gate_rejects_generic_conflict_and_abstract_beats():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["conflict"]["stakes"] = "主角面临重大危机。"
    scene["conflict"]["opposition"] = "神秘力量阻止他。"
    for beat in scene["beats"]:
        beat["visible_event"] = "剧情继续推进。"
        beat["action_lines"] = [{"content": "角色开始行动。"}]
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "scene_conflict_specificity" in failed
    assert "beat_visible_event_specificity" in failed
    assert "beat_action_specificity" in failed


@pytest.mark.unit
def test_quality_gate_rejects_symbolic_payoff_and_empty_cliffhanger():
    payload = _valid_contract()
    beats = payload["scenes"][0]["beats"]
    beats[1]["beat_type"] = "payoff"
    beats[1]["payoff_tag"] = "win"
    beats[1]["visible_event"] = "主角获得胜利。"
    beats[-1]["beat_type"] = "cliffhanger"
    beats[-1]["cliffhanger_tag"] = "suspense"
    beats[-1]["visible_event"] = "留下巨大悬念。"
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "payoff_specificity" in failed
    assert "cliffhanger_specificity" in failed


@pytest.mark.unit
def test_quality_gate_rejects_generic_dialogue_characters():
    payload = _valid_contract()
    for beat in payload["scenes"][0]["beats"]:
        for line in beat["dialogue_lines"]:
            line["character"] = "主角"
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "dialogue_character_specificity" in failed
    assert "scene_protagonist_presence" in failed


@pytest.mark.unit
def test_quality_gate_requires_recurring_named_character_in_scene():
    payload = _valid_contract()
    names = ["小机", "灰屏", "黑影"]
    for beat, name in zip(payload["scenes"][0]["beats"], names, strict=True):
        beat["dialogue_lines"][0]["character"] = name
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "scene_protagonist_presence" in failed
    assert "dialogue_character_specificity" not in failed


@pytest.mark.unit
def test_quality_gate_requires_beat_durations_for_timed_scene():
    payload = _valid_contract()
    for beat in payload["scenes"][0]["beats"]:
        beat.pop("duration_seconds", None)
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "beat_duration_required" in failed


@pytest.mark.unit
def test_quality_gate_rejects_scene_duration_mismatch():
    payload = _valid_contract()
    for beat in payload["scenes"][0]["beats"]:
        beat["duration_seconds"] = 2
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "scene_duration_alignment" in failed


@pytest.mark.unit
def test_quality_gate_rejects_internal_state_as_visible_action():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["beats"][0]["visible_event"] = "小机意识到真相正在改变命运。"
    scene["beats"][0]["action_lines"] = [{"content": "小机内心感到崩溃。"}]
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "beat_visible_event_specificity" in failed
    assert "beat_action_specificity" in failed


@pytest.mark.unit
def test_quality_gate_rejects_filler_dialogue_lines():
    payload = _valid_contract()
    for beat in payload["scenes"][0]["beats"]:
        for line in beat["dialogue_lines"]:
            line["content"] = "好的"
    contract = normalize_script_beat_contract(payload)

    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert report["passed"] is False
    assert "dialogue_substance" in failed


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
