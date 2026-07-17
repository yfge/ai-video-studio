from __future__ import annotations

import pytest
from app.services.ai.scripts_continuity import _merge_rewrite
from app.services.script.beat_contract_flatten import contract_to_legacy_lines
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract


@pytest.mark.unit
def test_continuity_rewrite_updates_embedded_beat_contract() -> None:
    contract = {
        "contract_version": "script-beat-v1",
        "title": "办公室反转",
        "logline": "林玥用日志证明数据被篡改。",
        "scenes": [
            {
                "scene_number": 1,
                "slug_line": "内. 会议室 - 日",
                "location": "会议室",
                "time_of_day": "日",
                "estimated_duration_seconds": 60,
                "dramatic_role": "hook",
                "conflict": {
                    "question": "林玥能否找到篡改者？",
                    "stakes": "客户即将撤单。",
                    "opposition": "篡改者正在删日志。",
                    "turn": "日志锁定账号。",
                },
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": "hook",
                        "dramatic_purpose": "抛出撤单危机。",
                        "visible_event": "旧投影画面。",
                        "action_lines": [
                            {
                                "content": "AP举起来源不明的文件。",
                                "timing": "intro",
                                "type": "action",
                            }
                        ],
                        "dialogue_lines": [
                            {
                                "character": "林玥",
                                "content": "数字不会撒谎。",
                            }
                        ],
                        "duration_seconds": 3,
                    }
                ],
            }
        ],
    }
    payload = {
        "structured_script_contract": contract,
        "metadata": {"structured_script_contract": contract},
        "scenes": [],
        "dialogues": [],
        "stage_directions": [],
    }

    _merge_rewrite(
        payload,
        {
            "dialogues": [
                {
                    "scene_number": 1,
                    "beat_order_index": 1,
                    "character": "林玥",
                    "content": "看云端日志时间戳。",
                    "emotion": "坚定",
                }
            ],
            "stage_directions": [
                {
                    "scene_number": 1,
                    "beat_order_index": 1,
                    "timing": "visible",
                    "type": "visible_event",
                    "content": "小陈把云端修改日志投到屏幕上。",
                },
                {
                    "scene_number": 1,
                    "beat_order_index": 1,
                    "timing": "mid",
                    "type": "action",
                    "content": "林玥指向账号与修改时间。",
                },
            ],
        },
        issue_count=2,
    )

    normalized = normalize_script_beat_contract(payload)
    _scenes, dialogues, stage_directions = contract_to_legacy_lines(normalized)

    assert payload["metadata"]["continuity_rewrite"] == {
        "verdict": "fail",
        "issue_count": 2,
        "structured_contract_synced": True,
    }
    assert dialogues[0]["content"] == "看云端日志时间戳。"
    assert stage_directions[0]["content"] == "小陈把云端修改日志投到屏幕上。"
    assert stage_directions[1]["content"] == "林玥指向账号与修改时间。"
    assert "AP举起来源不明的文件" not in str(payload)
