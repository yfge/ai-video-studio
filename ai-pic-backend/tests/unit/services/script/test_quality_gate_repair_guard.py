from app.services.script_quality_gate_repair_guard import (
    repair_preserves_script_structure,
)
from tests.unit.services.script.test_beat_contract_normalizer import _valid_contract


def _payload(character: str, content: str) -> dict:
    return {
        "content": content,
        "scenes": [{"scene_number": 1}],
        "dialogues": [
            {
                "scene_number": 1,
                "character": character,
                "content": "这才叫落地。",
            }
        ],
        "stage_directions": [
            {"scene_number": 1, "content": f"{character}把结果投到大屏。"}
        ],
    }


def test_repair_guard_rejects_same_shape_generic_story_replacement():
    before = _payload(
        "林妹妹",
        "林妹妹使用 gpt-img-2 生图，再用 seedance 2.0 完成 AI 落地样片。",
    )
    repaired = _payload(
        "现场负责人",
        "现场负责人移动关键物件，确认状态变化，阻力仍未解决。",
    )

    passed, details = repair_preserves_script_structure(
        before=before,
        repaired=repaired,
    )

    assert passed is False
    assert details["dominant_character"] == "林妹妹"
    assert details["dominant_character_lost"] is True
    assert details["anchor_terms_lost"] is True


def test_repair_guard_allows_structural_repair_that_keeps_story_identity():
    before = _payload(
        "林妹妹",
        "林妹妹使用 gpt-img-2 生图，再用 seedance 2.0 完成 AI 落地样片。",
    )
    repaired = _payload(
        "林妹妹",
        "林妹妹展示 gpt-img-2 图片与 seedance 2.0 视频，证明 AI 已真实落地。",
    )
    repaired["scenes"][0]["summary"] = "补齐具体冲突与结果。"

    passed, details = repair_preserves_script_structure(
        before=before,
        repaired=repaired,
    )

    assert passed is True
    assert details["dominant_character_lost"] is False
    assert details["anchor_terms_lost"] is False


def test_repair_guard_rejects_contract_that_drops_beat_line_coverage():
    contract = _valid_contract()
    before = _payload("林妹妹", "林妹妹用 seedance 2.0 交付视频。")
    before["structured_script_contract"] = contract
    repaired = _payload("林妹妹", "林妹妹用 seedance 2.0 交付视频。")
    repaired_contract = _valid_contract()
    for scene in repaired_contract["scenes"]:
        for beat in scene["beats"]:
            beat["action_lines"] = []
            beat["dialogue_lines"] = []
    repaired["structured_script_contract"] = repaired_contract

    passed, details = repair_preserves_script_structure(
        before=before,
        repaired=repaired,
    )

    assert passed is False
    assert details["contract_action_coverage_lost"] is True
    assert details["contract_dialogue_coverage_lost"] is True


def test_repair_guard_rejects_invalid_contract_when_original_was_valid():
    before = _payload("林妹妹", "林妹妹用 seedance 2.0 交付视频。")
    before["structured_script_contract"] = _valid_contract()
    repaired = _payload("林妹妹", "林妹妹用 seedance 2.0 交付视频。")
    repaired["structured_script_contract"] = {
        "contract_version": "script-beat-v1",
        "scenes": [{"scene_number": 1}],
    }

    passed, details = repair_preserves_script_structure(
        before=before,
        repaired=repaired,
    )

    assert passed is False
    assert details["contract_invalid"] is True
