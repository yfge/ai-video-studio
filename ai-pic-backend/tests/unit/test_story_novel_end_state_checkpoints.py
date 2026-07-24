from types import SimpleNamespace

from app.services.story.story_novel_gate_support import premature_plan_violations


def test_end_state_only_date_is_ignored_but_key_event_date_is_gated():
    revision = SimpleNamespace(
        generation_plan={
            "canon": {"entities": []},
            "chapters": [
                {
                    "position": 1,
                    "key_events": ["公开移交风钥"],
                    "end_state": "8月3日傍晚，风钥完成交接。",
                },
                {
                    "position": 2,
                    "key_events": ["货列离开澄砂港"],
                    "end_state": "8月10日清晨，货列驶出港区。",
                },
                {
                    "position": 3,
                    "key_events": ["黎雁回顾此前行程"],
                    "end_state": "队伍继续前进。",
                },
            ],
        }
    )

    body = "8月10日清晨，货列已经驶出港区。"
    assert premature_plan_violations(revision, 1, body) == []

    revision.generation_plan["chapters"][1]["key_events"] = [
        "8月10日清晨，货列离开澄砂港"
    ]
    assert premature_plan_violations(revision, 1, body) == [
        {
            "code": "canon_violation",
            "message": "正文提前出现计划第 2 章日期: 8月10日",
        }
    ]
    assert premature_plan_violations(revision, 2, "8月10日清晨，货列驶出澄砂港。") == []
    assert (
        premature_plan_violations(revision, 3, "黎雁记得8月10日清晨货列驶出港区。")
        == []
    )
