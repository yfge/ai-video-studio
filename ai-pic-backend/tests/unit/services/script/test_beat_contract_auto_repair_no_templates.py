import pytest
from app.services.script.beat_contract_auto_repair import (
    auto_repair_script_beat_contract,
)
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_auto_repair_does_not_inject_unrelated_workplace_template():
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
    text = str(repaired)

    assert repaired == {"structured_script_contract": payload}
    for unrelated_anchor in (
        "60秒，合同作废",
        "日志已锁",
        "改完给你20万",
        "这只是第一层",
        "张总手机倒计时从60秒跳到59秒",
        "陈默突然抢AP手机",
        "现场负责人",
        "当前场景",
    ):
        assert unrelated_anchor not in text
