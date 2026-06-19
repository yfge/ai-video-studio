import pytest

from app.services.script.beat_contract_auto_repair import (
    auto_repair_script_beat_contract,
)
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_auto_repair_preserves_three_second_opening_hook_with_many_beats():
    payload = _valid_contract()
    first_scene = payload["scenes"][0]
    first_scene["beats"][0]["visible_event"] = "投影幕布亮起，显示并购尽调数据。"
    first_scene["beats"][0]["action_lines"] = [
        {"content": "全场目光聚焦AP。"},
    ]
    first_scene["beats"].insert(
        1,
        {
            "order_index": 2,
            "beat_type": "reversal",
            "dramatic_purpose": "AP发现原始文件和投影数字冲突。",
            "visible_event": "AP翻开原始文件，手指停在被改动的数字上。",
            "action_lines": [{"content": "AP把文件推到客户面前。"}],
            "dialogue_lines": [{"character": "小机", "content": "这里被改了。"}],
            "duration_seconds": 4,
        },
    )

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    first_beat = contract.scenes[0].beats[0]
    failed = {item["check_id"] for item in report["failed_checks"]}
    assert first_beat.duration_seconds <= 3
    assert "opening_hook_duration" not in failed
    assert "opening_hook_substance" not in failed


@pytest.mark.unit
def test_auto_repair_falls_back_to_top_level_contract_when_embedded_contract_invalid():
    payload = _valid_contract()
    bad_embedded_contract = {
        "contract_version": "script-beat-v1",
        "title": payload["title"],
        "scenes": [
            {
                "scene_number": 1,
                "beats": payload["scenes"][0]["beats"],
            }
        ],
    }

    repaired = auto_repair_script_beat_contract(
        {
            **payload,
            "metadata": {"structured_script_contract": bad_embedded_contract},
            "structured_script_contract": bad_embedded_contract,
        },
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)

    assert contract.scenes[0].slug_line == "内. 控制室 - 夜"
    assert repaired["structured_script_contract"]["scenes"][0]["slug_line"] == (
        "内. 控制室 - 夜"
    )


@pytest.mark.unit
def test_auto_repair_replaces_abstract_opposition_with_concrete_source():
    payload = _valid_contract()
    payload["scenes"][0]["conflict"]["opposition"] = "匿名短信透露的幕后黑手"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert "scene_conflict_opposition" not in failed
    assert "文件" in contract.scenes[0].conflict.opposition


@pytest.mark.unit
def test_auto_repair_replaces_thin_opposition_value():
    payload = _valid_contract()
    payload["scenes"][0]["conflict"]["opposition"] = "篡改者"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert "scene_conflict_specificity" not in failed
    assert contract.scenes[0].conflict.opposition != "篡改者"
    assert "30秒倒计时" in contract.scenes[0].conflict.opposition


@pytest.mark.unit
def test_auto_repair_injects_workplace_data_commercial_anchors():
    payload = _valid_contract()
    payload["title"] = "数据迷局"
    payload["logline"] = "AP在并购尽调会上发现客户合同数据被篡改。"
    payload["scenes"] = [
        {
            "scene_number": 1,
            "slug_line": "内. 会议室 - 日",
            "location": "会议室",
            "time_of_day": "日",
            "estimated_duration_seconds": 45,
            "dramatic_role": "hook",
            "conflict": {
                "question": "AP如何稳住客户质疑？",
                "stakes": "客户合同可能取消。",
                "opposition": "篡改者",
                "turn": "AP发现数据被篡改。",
            },
            "beats": [
                {
                    "order_index": 1,
                    "beat_type": "hook",
                    "dramatic_purpose": "引入冲突。",
                    "visible_event": "客户质疑数据。",
                    "action_lines": [{"content": "张总拍桌。"}],
                    "dialogue_lines": [{"character": "AP", "content": "我查。"}],
                    "duration_seconds": 3,
                }
            ],
        },
        {
            "scene_number": 2,
            "slug_line": "内. 会议室 - 日",
            "location": "会议室",
            "time_of_day": "日",
            "estimated_duration_seconds": 75,
            "dramatic_role": "escalation",
            "conflict": {
                "question": "AP如何揭露篡改者？",
                "stakes": "客户合同可能取消。",
                "opposition": "篡改者",
                "turn": "陈默试图删除文件。",
            },
            "beats": [],
        },
        {
            "scene_number": 3,
            "slug_line": "内. 会议室 - 日",
            "location": "会议室",
            "time_of_day": "日",
            "estimated_duration_seconds": 60,
            "dramatic_role": "cliffhanger",
            "conflict": {
                "question": "幕后主使是谁？",
                "stakes": "证据可能被删除。",
                "opposition": "匿名威胁",
                "turn": "新威胁出现。",
            },
            "beats": [],
        },
    ]

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=1300,
    )
    text = repaired["content"]
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    assert report["passed"] is True
    assert "60秒，合同作废" in text
    assert "日志已锁" in text
    assert "改完给你20万" in text
    assert "这只是第一层" in text
    assert "张总手机倒计时从60秒跳到59秒" in text
    assert text.index("陈默突然抢AP手机") < text.index("手机给我")


@pytest.mark.unit
def test_auto_repair_replaces_vague_cliffhanger_opposition():
    payload = _valid_contract()
    final_scene = payload["scenes"][-1]
    final_scene["conflict"]["stakes"] = "AP可能被幕后主使报复，项目仍存在风险。"
    final_scene["conflict"][
        "opposition"
    ] = "篡改者李明崩溃，但手机收到神秘短信，AP也收到匿名威胁。"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert "scene_conflict_specificity" not in failed
    assert "崩溃" not in contract.scenes[-1].conflict.opposition
    assert "30秒倒计时" in contract.scenes[-1].conflict.opposition


@pytest.mark.unit
def test_auto_repair_makes_turn_purpose_and_protagonist_screen_action_specific():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["conflict"]["turn"] = "AP发现数据被篡改，并意识到内部有人动手脚。"
    for beat in scene["beats"]:
        for line in beat["dialogue_lines"]:
            line["character"] = "AP回归角色-20260618T164912"
        beat["visible_event"] = beat["visible_event"].replace("小机", "AP")
        for action in beat["action_lines"]:
            action["content"] = action["content"].replace("小机", "AP")
    scene["beats"][-1]["dramatic_purpose"] = "新的威胁浮现，留下悬念。"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)

    failed = {item["check_id"] for item in report["failed_checks"]}
    assert "scene_conflict_turn" not in failed
    assert "scene_protagonist_screen_presence" not in failed
    assert "beat_dramatic_purpose_specificity" not in failed
    assert "AP回归角色-20260618T164912" in (
        contract.scenes[0].beats[0].action_lines[0].content
    )
