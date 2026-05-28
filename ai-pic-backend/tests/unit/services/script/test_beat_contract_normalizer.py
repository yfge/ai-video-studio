import pytest
from app.schemas.script_beat_contract import StructuredScriptContract
from app.services.script.beat_contract_normalizer import (
    flatten_contract_to_script_payload,
    normalize_script_beat_contract,
)
from app.services.script.content_normalization import normalize_script_content
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


@pytest.mark.unit
def test_flatten_contract_to_legacy_script_payload():
    contract = normalize_script_beat_contract(_valid_contract())

    flattened = flatten_contract_to_script_payload(
        contract,
        format_type="screenplay",
        language="zh-CN",
        episode_number=1,
        template_style="commercial_vertical_drama",
        target_chars_per_episode=500,
        title="倒计时谜影",
    )

    assert flattened["scenes"][0]["beats"][0]["beat_type"] == "hook"
    assert flattened["dialogues"][0]["scene_number"] == 1
    assert flattened["dialogues"][0]["character"] == "小机"
    assert flattened["stage_directions"][0]["scene_number"] == 1
    assert "小机" in flattened["content"]
    assert flattened["metadata"]["structured_contract_version"] == "script-beat-v1"


@pytest.mark.unit
def test_legacy_script_conversion_marks_fallback_evidence():
    legacy = {
        "title": "旧结构",
        "scenes": [
            {
                "scene_number": 1,
                "slug_line": "内. 控制室 - 夜",
                "summary": "小机发现奖金清零。",
            }
        ],
        "dialogues": [
            {
                "scene_number": 1,
                "character": "旁白",
                "content": "小机发现奖金清零。",
                "fallback": True,
            }
        ],
        "stage_directions": [
            {
                "scene_number": 1,
                "content": "小机发现奖金清零。",
                "type": "action",
                "fallback": True,
            }
        ],
    }

    contract = normalize_script_beat_contract(legacy)

    assert contract.scenes[0].beats[0].beat_type == "setup"
    assert contract.scenes[0].beats[0].visible_event == "小机发现奖金清零。"
    assert contract.model_extra["fallback_detected"] is True


@pytest.mark.unit
def test_content_normalization_preserves_scene_beats():
    payload = _valid_contract()
    normalized = normalize_script_content(
        payload,
        format_type="screenplay",
        language="zh-CN",
        episode_number=1,
        template_style="commercial_vertical_drama",
        target_chars_per_episode=500,
        title="倒计时谜影",
    )

    assert normalized["scenes"][0]["beats"][0]["beat_type"] == "hook"
    assert normalized["scenes"][0]["summary"] == "谁清空了奖金？"
