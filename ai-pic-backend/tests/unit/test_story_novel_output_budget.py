from app.services.story.story_novel_ai_prompts import (
    chapter_gate_repair_prompt,
    chapter_prompt,
)
from app.services.story.story_novel_length_contract import chapter_output_tokens

PLAN = {"min_chars": 3000, "target_chars": 4000, "max_chars": 5000}


def test_deepseek_v4_pro_reserves_reasoning_headroom_beyond_16k():
    assert chapter_output_tokens(PLAN, "deepseek:deepseek-v4-pro") == 48000


def test_non_reasoning_model_keeps_standard_dynamic_budget():
    assert chapter_output_tokens(PLAN, "deepseek:deepseek-v4-flash") == 16000


def test_short_body_repair_requires_an_executable_paragraph_budget():
    prompt = chapter_gate_repair_prompt(
        context_pack={
            "hard_constraints": {
                "chapter_contract": {},
                "compiled_canon": {},
            }
        },
        prior_result={"content_text": "短正文"},
        actual_chars=2030,
        target_chars=4000,
        violations=[{"code": "canon_violation", "message": "章节长度不足"}],
    )

    assert "正文必须写满 42–45 个完整叙事段落" in prompt
    assert "每段 100–110 个非空白字符" in prompt


def test_chapter_prompt_locks_unplanned_canon_object_state():
    prompt = chapter_prompt(
        context_pack={
            "hard_constraints": {
                "chapter_contract": {
                    "canon_refs": ["char-a", "obj-probe"],
                    "location_transitions": [{"subject_id": "char-a"}],
                    "state_transitions": [],
                },
                "compiled_canon": {
                    "entities": [
                        {"id": "char-a", "kind": "character", "name": "王明"},
                        {"id": "obj-probe", "kind": "object", "name": "潮汐测针"},
                    ]
                },
                "current_state": {
                    "subjects": {
                        "char-a": {"location": "loc-ship"},
                        "obj-probe": {
                            "location": "loc-ship",
                            "owner_id": "char-a",
                            "status": "stored",
                        },
                    }
                },
            }
        },
        target_chars=4000,
    )

    assert '"subject_id":"obj-probe"' in prompt
    assert '"name":"潮汐测针"' in prompt
    assert '"status":"stored"' in prompt
    assert '"must_remain":{"owner_id":"char-a","status":"stored"}' in prompt
    assert '"location_rule":"随 owner 的已授权移动同行，不得部署或留下"' in prompt
    assert '"subject_id":"char-a","name"' not in prompt
    assert "名称相近的普通物件不得映射" in prompt
