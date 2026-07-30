from app.services.story.story_novel_v3_audit_semantics import current_state_contract


def test_audit_includes_mentioned_canon_subject_and_immutable_identity():
    canon = {
        "entities": [
            {
                "id": "char-shenhe",
                "kind": "character",
                "name": "沈禾",
                "aliases": [],
                "attributes": {
                    "gender": "female",
                    "pronouns": "她",
                    "occupation": "农学试验员",
                },
            },
            {
                "id": "obj-ruler",
                "kind": "object",
                "name": "木尺",
                "aliases": [],
            },
        ]
    }
    state = {
        "subjects": {
            "char-shenhe": {"location": "loc-field"},
            "obj-ruler": {"owner_id": "char-shenhe", "location": "loc-field"},
        },
        "threads": {},
    }

    result = current_state_contract(
        canon,
        {"position": 7, "canon_refs": [], "execution_contracts": []},
        {
            "state_before_hash": "state-hash",
            "state_transitions": [],
            "location_transitions": [],
            "knowledge_grants": [],
        },
        state,
        "沈禾把木尺交给顾砚，请他代为保管。",
    )
    by_id = {item["subject_id"]: item for item in result["subjects"]}

    assert by_id["char-shenhe"]["immutable_attributes"] == {
        "gender": "female",
        "pronouns": "她",
        "occupation": "农学试验员",
    }
    assert by_id["obj-ruler"]["state"]["owner_id"] == "char-shenhe"


def test_audit_prompt_requires_semantic_checks_without_literal_dates():
    prompt = open(
        "app/prompts/templates/story_novel_proof_audit_v3.txt",
        encoding="utf-8",
    ).read()

    assert "性别、称谓、家庭角色" in prompt
    assert "参与者数量、身份与动作是否前后回滚" in prompt
    assert "观察、怀疑、推断还是已确认事实" in prompt
    assert "不得要求正文逐字复述日期" in prompt
