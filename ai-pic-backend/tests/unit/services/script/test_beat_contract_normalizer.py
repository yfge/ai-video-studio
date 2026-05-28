import pytest
from app.schemas.script_beat_contract import StructuredScriptContract
from pydantic import ValidationError


def _valid_contract():
    return {
        "contract_version": "script-beat-v1",
        "title": "倒计时谜影",
        "logline": "机器人发现奖金清零，必须找出谁改了时间轴。",
        "scenes": [
            {
                "scene_number": 1,
                "slug_line": "内. 控制室 - 夜",
                "location": "控制室",
                "time_of_day": "夜",
                "estimated_duration_seconds": 15,
                "dramatic_role": "hook",
                "conflict": {
                    "question": "谁清空了奖金？",
                    "stakes": "60秒内找不到就永久丢失奖金。",
                    "opposition": "被篡改的时间轴系统。",
                    "turn": "倒计时突然启动。",
                },
                "beats": [
                    {
                        "order_index": 1,
                        "beat_type": "hook",
                        "dramatic_purpose": "直接抛出损失和时间压力。",
                        "visible_event": "屏幕显示奖金归零，警报亮起。",
                        "action_lines": [
                            {"content": "小机冲到控制台，红色倒计时开始跳动。"}
                        ],
                        "dialogue_lines": [
                            {
                                "character": "小机",
                                "content": "奖金清零？",
                                "emotion": "惊慌",
                            }
                        ],
                        "duration_seconds": 5,
                        "hook_tag": "countdown_loss",
                    },
                    {
                        "order_index": 2,
                        "beat_type": "conflict",
                        "dramatic_purpose": "让主角遇到阻力。",
                        "visible_event": "修改日志被锁定，权限被拒绝。",
                        "action_lines": [{"content": "控制台弹出红色权限拒绝提示。"}],
                        "dialogue_lines": [
                            {"character": "小机", "content": "权限也没了？"}
                        ],
                        "duration_seconds": 5,
                    },
                    {
                        "order_index": 3,
                        "beat_type": "cliffhanger",
                        "dramatic_purpose": "留下未解威胁。",
                        "visible_event": "黑影从日志里删除最后一条记录。",
                        "action_lines": [{"content": "日志末行被黑色光标吞掉。"}],
                        "dialogue_lines": [
                            {"character": "小机", "content": "谁还在线？"}
                        ],
                        "duration_seconds": 5,
                        "cliffhanger_tag": "hidden_operator",
                    },
                ],
            }
        ],
    }


@pytest.mark.unit
def test_structured_script_contract_accepts_valid_payload():
    contract = StructuredScriptContract.model_validate(_valid_contract())

    assert contract.contract_version == "script-beat-v1"
    assert contract.scenes[0].beats[0].beat_type == "hook"
    assert contract.scenes[0].beats[-1].cliffhanger_tag == "hidden_operator"


@pytest.mark.unit
def test_structured_script_contract_rejects_unknown_role():
    payload = _valid_contract()
    payload["scenes"][0]["dramatic_role"] = "vibes"

    with pytest.raises(ValidationError):
        StructuredScriptContract.model_validate(payload)
