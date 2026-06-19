import pytest

from app.services.script.beat_contract_auto_repair import (
    auto_repair_script_beat_contract,
)
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
from tests.unit.services.script.test_beat_contract_auto_repair import _valid_contract


@pytest.mark.unit
def test_auto_repair_dedupes_screen_dialogue_and_hardens_payoff():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["beats"][1]["visible_event"] = scene["beats"][0]["visible_event"]
    scene["beats"][1]["action_lines"] = list(scene["beats"][0]["action_lines"])
    scene["beats"][1]["dialogue_lines"][0]["content"] = "证据在这。"
    scene["beats"][1]["beat_type"] = "payoff"
    scene["beats"][1]["payoff_tag"] = "客户信任"
    scene["beats"][1]["visible_event"] = "篡改者崩溃承认，客户信任AP回归"
    scene["beats"][1]["action_lines"] = [{"content": "篡改者崩溃，客户脸色缓和"}]
    scene["beats"][2]["dialogue_lines"][0]["content"] = "证据在这。"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert "beat_progression_repetition" not in failed
    assert "dialogue_progression_repetition" not in failed
    assert "beat_visible_event_specificity" not in failed
    assert "payoff_specificity" not in failed


@pytest.mark.unit
def test_auto_repair_shortens_dialogue_lines_for_short_drama_gate():
    payload = _valid_contract()
    long_lines = [
        "陈总，原始文件在我手上，数据差异我会查清。",
        "我记得原始数据是875万，对吗？",
        "云端数据是875万，投影上是920万。",
        "左边是云端原始数据，右边是投影数据。",
        "你签过字确认数据无误，现在怎么说？",
    ]
    first_scene = payload["scenes"][0]
    for idx, text in enumerate(long_lines):
        beat = first_scene["beats"][idx % len(first_scene["beats"])]
        beat.setdefault("dialogue_lines", [])
        beat["dialogue_lines"][0]["content"] = text

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    repaired_text = repaired["content"]
    assert "dialogue_line_length" not in failed
    assert "陈总，原始文件在我手上，数据差异我会查清。" not in repaired_text
    for scene in contract.scenes:
        for beat in scene.beats:
            for line in beat.dialogue_lines:
                assert len("".join(ch for ch in line.content if not ch.isspace())) <= 15


@pytest.mark.unit
def test_auto_repair_shortens_dialogue_to_complete_short_sentences():
    payload = _valid_contract()
    first_scene = payload["scenes"][0]
    lines = [
        "陈总，可能是版本同步问题。我让助理调取原始备份。",
        "这是你签的会议纪要，同意数据无误。",
        "AP，抱歉刚才误会了。你们内部要继续查。",
    ]
    for idx, text in enumerate(lines):
        beat = first_scene["beats"][idx % len(first_scene["beats"])]
        beat["dialogue_lines"][0]["content"] = text

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    repaired_text = repaired["content"]

    assert "我让助理调取" not in repaired_text
    assert "同意数据无" not in repaired_text
    assert "你们内部" not in repaired_text
    assert "可能是同步问题。" in repaired_text
    assert "纪要有你签字。" in repaired_text
    assert "刚才误会了。" in repaired_text


@pytest.mark.unit
def test_auto_repair_replaces_vague_stakes_and_purpose():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["conflict"]["stakes"] = "若不澄清，合同作废，团队信任崩溃。"
    scene["conflict"]["turn"] = "AP投屏原始数据与录音，陈默当场崩溃。"
    scene["beats"][0]["dramatic_purpose"] = "引入冲突，激发紧张感。"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert "scene_conflict_specificity" not in failed
    assert "scene_conflict_turn" not in failed
    assert "beat_dramatic_purpose_specificity" not in failed
    assert "300万项目合同" in contract.scenes[0].conflict.stakes


@pytest.mark.unit
def test_auto_repair_replaces_prompt_style_opening_purpose():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["beats"][0]["dramatic_purpose"] = "3秒内制造冲突：客户拍桌质问，数据异常。"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert "beat_dramatic_purpose_specificity" not in failed
    assert "制造冲突" not in contract.scenes[0].beats[0].dramatic_purpose


@pytest.mark.unit
def test_auto_repair_replaces_generic_scene_turn_key_line():
    payload = _valid_contract()
    payload["scenes"][0]["conflict"]["turn"] = "发现关键线索"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert "scene_conflict_turn" not in failed
    assert contract.scenes[0].conflict.turn != "发现关键线索"
    assert "原始文件" in contract.scenes[0].conflict.turn


@pytest.mark.unit
def test_auto_repair_replaces_vague_visual_language_in_actions():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["beats"][0]["visible_event"] = "会议室气氛紧张，所有人注视AP。"
    scene["beats"][1]["action_lines"][0][
        "content"
    ] = "电话上显示倒计时，紧张气氛再度升级。"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    repaired_text = repaired["content"]

    assert "气氛" not in repaired_text
    assert "云端日志时间戳" in repaired_text


@pytest.mark.unit
def test_auto_repair_coerces_malformed_embedded_contract_without_top_level_scenes():
    malformed_contract = {
        "contract_version": "script-beat-v1",
        "scenes": [
            {
                "scene_number": 1,
                "estimated_duration_seconds": 15,
                "beats": [
                    {"order_index": 1, "beat_type": "hook", "duration_seconds": 3},
                    {"order_index": 2, "beat_type": "conflict", "duration_seconds": 6},
                    {"order_index": 3, "beat_type": "reveal", "duration_seconds": 6},
                ],
            }
        ],
    }

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": malformed_contract},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    assert contract.scenes[0].slug_line == "内. 会议室 - 日"
    assert contract.scenes[0].beats[0].visible_event
    assert report["passed"] is True, report
