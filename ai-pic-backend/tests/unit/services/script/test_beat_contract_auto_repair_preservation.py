import pytest
from app.services.script.beat_contract_auto_repair import (
    auto_repair_script_beat_contract,
)
from app.services.script.beat_contract_normalizer import normalize_script_beat_contract
from app.services.script.beat_contract_quality import evaluate_beat_contract_quality
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


@pytest.mark.unit
def test_auto_repair_preserves_complete_provider_story_instead_of_ap_template():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["conflict"] = {
        "question": "林妹妹能否保住AI方案？",
        "stakes": "若演示失败，林妹妹将失去客户合同和核心素材库权限。",
        "opposition": "贾总利用职权冻结素材权限并阻止方案发布。",
        "turn": "林妹妹用生成日志证明陈默篡改了客户合同素材。",
    }
    scene["beats"] = [
        {
            "order_index": 1,
            "beat_type": "hook",
            "dramatic_purpose": "客户合同素材突然被标记为篡改版本。",
            "visible_event": "林妹妹打开客户合同，屏幕突然标红被篡改的素材编号。",
            "action_lines": [{"content": "林妹妹把原始提示词和生成日志并排展开。"}],
            "dialogue_lines": [{"character": "林妹妹", "content": "日志不对。"}],
            "duration_seconds": 3,
        },
        {
            "order_index": 2,
            "beat_type": "reveal",
            "dramatic_purpose": "林妹妹现场证明新方案可以稳定生成。",
            "visible_event": "gpt-img-2连续生成三张一致的3D卡通角色图。",
            "action_lines": [{"content": "林妹妹将三张角色图拖入客户演示页。"}],
            "dialogue_lines": [{"character": "林妹妹", "content": "角色稳住了。"}],
            "duration_seconds": 6,
            "payoff_tag": "AI方案通过现场验证",
        },
        {
            "order_index": 3,
            "beat_type": "cliffhanger",
            "dramatic_purpose": "贾总从总部冻结权限，暴露更高层阻力。",
            "visible_event": "林妹妹手机弹出红色提示：核心素材库访问权限已冻结，备注贾总（总部）。",
            "action_lines": [{"content": "林妹妹抬头看向仍在闪红的权限页面。"}],
            "dialogue_lines": [{"character": "林妹妹", "content": "他在总部。"}],
            "duration_seconds": 6,
            "cliffhanger_tag": "贾总冻结核心素材库权限",
        },
    ]

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=900,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)
    text = repaired["content"]

    assert report["passed"] is True
    assert (
        contract.scenes[0].conflict
        == normalize_script_beat_contract(payload).scenes[0].conflict
    )
    assert contract.scenes[0].beats[-1].visible_event == (
        "林妹妹手机弹出红色提示：核心素材库访问权限已冻结，备注贾总（总部）。"
    )
    assert "gpt-img-2连续生成三张一致的3D卡通角色图" in text
    assert "AP手机弹出匿名短信" not in text
    assert "张总手机倒计时" not in text
    assert "投影并购数据" not in text


@pytest.mark.unit
def test_auto_repair_adds_payoff_tag_without_replacing_provider_event():
    payload = _valid_contract()
    beats = payload["scenes"][0]["beats"]
    beats[1]["beat_type"] = "reveal"
    beats[1].pop("payoff_tag", None)
    original_event = beats[1]["visible_event"]

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=500,
    )
    contract = normalize_script_beat_contract(repaired)

    assert contract.scenes[0].beats[1].visible_event == original_event
    assert any(
        beat.beat_type == "payoff" or beat.payoff_tag
        for beat in contract.scenes[0].beats
    )


@pytest.mark.unit
def test_auto_repair_rejects_generic_contract_that_drops_story_identity():
    original = {
        "content": ("林妹妹在办公室展示 gpt-img-2 生图和 seedance 2.0 视频工程。"),
        "scenes": [{"scene_number": 1, "location": "办公室"}],
        "dialogues": [
            {"scene_number": 1, "character": "林妹妹", "content": "这才叫落地。"}
        ],
        "stage_directions": [
            {"scene_number": 1, "content": "林妹妹把视频时间线投到大屏。"}
        ],
        "structured_script_contract": {
            "contract_version": "script-beat-v1",
            "scenes": [{"scene_number": 1}],
        },
    }

    repaired = auto_repair_script_beat_contract(original)

    assert repaired == original
    assert "现场负责人" not in repaired["content"]


@pytest.mark.unit
def test_auto_repair_never_invents_a_named_character_when_none_was_provided():
    payload = _valid_contract()
    scene = payload["scenes"][0]
    scene["summary"] = None
    scene["conflict"] = {
        "question": "",
        "stakes": "风险上升。",
        "opposition": "幕后黑手",
        "turn": "出现转折。",
    }
    for beat in scene["beats"]:
        for line in beat["dialogue_lines"]:
            line["character"] = "旁白"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=600,
    )

    text = str(repaired)
    assert "现场负责人" not in text
    assert "None停下动作" not in text


@pytest.mark.unit
def test_auto_repair_keeps_episode_intent_and_repairs_only_structure():
    payload = _valid_contract()
    payload["title"] = "落地了个寂寞"
    payload["logline"] = "林妹妹拆穿办公室 AI 假落地，并用真实交付反转全场。"
    scene = payload["scenes"][0]
    scene["slug_line"] = "内. 办公室工位区 - 日"
    scene["location"] = "办公室工位区"
    scene["conflict"] = {
        "question": "林妹妹能否拆穿办公室 AI 假落地？",
        "stakes": "如果不说，旧流程会继续套新词。",
        "opposition": "同事举着方案页和未完成文件阻止她证明结果。",
        "turn": "林妹妹打开邮件和系统回执，展示真实交付。",
    }
    scene["beats"][0]["visible_event"] = "大屏写着“AI落地了”，桌上待办文件却原封不动。"
    scene["beats"][0]["dialogue_lines"] = [
        {"character": "林妹妹", "content": "活没动，词先落地？"}
    ]
    scene["beats"][1][
        "visible_event"
    ] = "林妹妹打开 gpt-img-2 展示图和 seedance 2.0 视频预览。"
    scene["beats"][1]["dialogue_lines"] = [
        {
            "character": "林妹妹",
            "content": "片，先看预览片段，用seedance 2.0做的。",
        }
    ]
    scene["beats"][2]["visible_event"] = "林妹妹停在原流程文件的下一页。"
    scene["beats"][2]["dialogue_lines"] = [
        {
            "character": "林妹妹",
            "content": "光看这封面和我刚才扫过的流程页，就不止一步。",
        }
    ]
    scene["beats"][2]["beat_type"] = "cliffhanger"
    scene["beats"][2]["cliffhanger_tag"] = "下一页还没有翻开"

    repaired = auto_repair_script_beat_contract(
        {"structured_script_contract": payload},
        target_chars_per_episode=600,
    )
    contract = normalize_script_beat_contract(repaired)
    report = evaluate_beat_contract_quality(contract)
    text = repaired["content"]

    assert report["passed"] is True, report
    assert "林妹妹" in text
    assert "gpt-img-2" in text
    assert "seedance 2.0" in text
    assert "现场负责人" not in text
    assert "现场状态突然变化" not in text
    assert all(
        len("".join(ch for ch in line.content if not ch.isspace())) <= 15
        for scene in contract.scenes
        for beat in scene.beats
        for line in beat.dialogue_lines
    )
