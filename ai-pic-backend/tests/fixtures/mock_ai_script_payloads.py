"""Script payloads for the mock AI service fixture."""

from __future__ import annotations

from typing import Any


def mock_passing_script_payload() -> dict[str, Any]:
    from app.schemas.script_beat_contract import StructuredScriptContract
    from app.services.script.beat_contract_normalizer import (
        flatten_contract_to_script_payload,
    )

    contract = StructuredScriptContract.model_validate(
        {
            "contract_version": "script-beat-v1",
            "title": "证据背面的签名",
            "logline": "Hero必须在发布会后抢回证据，却发现签名指向更高层黑手。",
            "scenes": [
                {
                    "scene_number": 1,
                    "slug_line": "内. 发布会后台 - 日",
                    "location": "发布会后台",
                    "time_of_day": "日",
                    "estimated_duration_seconds": 15,
                    "dramatic_role": "hook",
                    "conflict": {
                        "question": "Hero能否在证据被锁进保险箱前抢回手机？",
                        "stakes": "30秒内失败，公开视频证据将被永久删除。",
                        "opposition": "对手和锁住的保险箱挡在Hero面前。",
                        "turn": "保险箱屏幕突然显示删除倒计时。",
                    },
                    "beats": [
                        {
                            "order_index": 1,
                            "beat_type": "hook",
                            "dramatic_purpose": "三秒内抛出证据被抢的损失。",
                            "visible_event": "保险箱亮起删除倒计时，Hero冲进后台。",
                            "action_lines": [
                                {"content": "Hero撞开门，手指死死扣住保险箱边缘。"}
                            ],
                            "dialogue_lines": [
                                {
                                    "character": "Hero",
                                    "content": "证据别删。",
                                    "emotion": "压住怒火",
                                }
                            ],
                            "duration_seconds": 3,
                            "hook_tag": "evidence_countdown",
                        },
                        {
                            "order_index": 2,
                            "beat_type": "reveal",
                            "dramatic_purpose": "用外部动作给出反击筹码。",
                            "visible_event": "Hero举起录音手机，对手手停在密码键上。",
                            "action_lines": [
                                {"content": "Hero把手机屏幕贴到镜头前，录音波形跳动。"}
                            ],
                            "dialogue_lines": [
                                {
                                    "character": "Hero",
                                    "content": "你已入镜。",
                                    "emotion": "冷静",
                                }
                            ],
                            "duration_seconds": 6,
                            "payoff_tag": "recording_proof",
                        },
                        {
                            "order_index": 3,
                            "beat_type": "cliffhanger",
                            "dramatic_purpose": "留下更高层黑手的未解威胁。",
                            "visible_event": "证据背面露出陌生新签名，对手突然变脸。",
                            "action_lines": [
                                {"content": "Hero翻过证据，指尖停在陌生签名上。"}
                            ],
                            "dialogue_lines": [
                                {
                                    "character": "Hero",
                                    "content": "这是谁？",
                                    "emotion": "压低声",
                                }
                            ],
                            "duration_seconds": 6,
                            "cliffhanger_tag": "unknown_signature",
                        },
                    ],
                }
            ],
        }
    )
    return flatten_contract_to_script_payload(
        contract,
        format_type="screenplay",
        language="zh-CN",
        episode_number=1,
        template_style="commercial_vertical_drama",
        target_chars_per_episode=1300,
        title="证据背面的签名",
    )
