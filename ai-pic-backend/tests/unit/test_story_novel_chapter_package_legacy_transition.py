from app.services.story.story_novel_chapter_package_normalization import (
    normalize_missing_contract_fields,
    strip_invalid_model_fields,
)
from app.services.story.story_novel_plan_state_compiler import compile_plan_state


def test_predicate_shaped_eq_transition_uses_explicit_state_before():
    contract = _contract(
        {
            "subject_id": "obj-book",
            "field": "owner_id",
            "operator": "eq",
            "value": "char-new",
            "preconditions": [],
        }
    )

    result = normalize_missing_contract_fields(
        contract,
        {"entities": []},
        state_before={"subjects": {"obj-book": {"owner_id": "char-old"}}},
    )

    assert result["state_transitions"] == [
        {
            "subject_id": "obj-book",
            "field": "owner_id",
            "from_value": "char-old",
            "to_value": "char-new",
        }
    ]


def test_predicate_shaped_transition_does_not_guess_an_unknown_origin():
    raw = {
        "subject_id": "obj-book",
        "field": "owner_id",
        "operator": "eq",
        "value": "char-new",
        "preconditions": [],
    }

    result = normalize_missing_contract_fields(
        _contract(raw), {"entities": []}, state_before={"subjects": {}}
    )

    assert result["state_transitions"] == [raw]


def test_predicate_shaped_transition_does_not_discard_model_preconditions():
    raw = {
        "subject_id": "obj-book",
        "field": "owner_id",
        "operator": "eq",
        "value": "char-new",
        "preconditions": [{"operator": "eq", "value": "char-other"}],
    }

    result = normalize_missing_contract_fields(
        _contract(raw),
        {"entities": []},
        state_before={"subjects": {"obj-book": {"owner_id": "char-old"}}},
    )

    assert result["state_transitions"] == [raw]


def test_add_shaped_transition_uses_explicit_list_state_without_guessing():
    contract = _contract(
        {
            "subject_id": "char-he",
            "field": "permissions",
            "operator": "add",
            "value": "perm-cooperative-stamp",
            "preconditions": [],
        }
    )

    result = normalize_missing_contract_fields(
        contract,
        {"entities": []},
        state_before={"subjects": {"char-he": {"permissions": ["perm-trial"]}}},
    )

    assert result["state_transitions"] == [
        {
            "subject_id": "char-he",
            "field": "permissions",
            "from_value": ["perm-trial"],
            "to_value": ["perm-trial", "perm-cooperative-stamp"],
        }
    ]


def test_add_shaped_transition_keeps_unknown_or_non_list_state_invalid():
    raw = {
        "subject_id": "char-he",
        "field": "permissions",
        "operator": "add",
        "value": "perm-cooperative-stamp",
        "preconditions": [],
    }

    unknown = normalize_missing_contract_fields(
        _contract(raw), {"entities": []}, state_before={"subjects": {}}
    )
    scalar = normalize_missing_contract_fields(
        _contract(raw),
        {"entities": []},
        state_before={"subjects": {"char-he": {"permissions": "perm-trial"}}},
    )

    assert unknown["state_transitions"] == [raw]
    assert scalar["state_transitions"] == [raw]


def test_observed_milestone_package_compiles_eq_and_add_effects_from_state():
    canon = {
        "entities": [
            {"id": "char-he", "kind": "character"},
            {"id": "org-cooperative", "kind": "organization"},
            {"id": "loc-hall", "kind": "location"},
        ],
        "initial_state": {
            "char-he": {"permissions": ["perm-trial"]},
            "org-cooperative": {"status": "not_founded", "location": None},
        },
        "milestones": [
            {
                "id": "mile-founded",
                "outcomes": [
                    {
                        "subject_id": "org-cooperative",
                        "field": "status",
                        "operator": "eq",
                        "value": "active",
                    },
                    {
                        "subject_id": "char-he",
                        "field": "permissions",
                        "operator": "contains",
                        "value": "perm-stamp",
                    },
                ],
            }
        ],
    }
    contract = strip_invalid_model_fields(
        {
            "state_transitions": [
                {
                    "subject_id": "org-cooperative",
                    "field": "status",
                    "operator": "eq",
                    "value": "active",
                },
                {
                    "subject_id": "org-cooperative",
                    "field": "location",
                    "operator": "eq",
                    "value": "loc-hall",
                },
                {
                    "subject_id": "char-he",
                    "field": "permissions",
                    "operator": "add",
                    "value": "perm-stamp",
                },
            ],
            "knowledge_grants": [],
            "location_transitions": [],
            "execution_contracts": [],
            "milestones_consumed": ["mile-founded"],
        }
    )

    normalized = normalize_missing_contract_fields(
        contract, canon, state_before={"subjects": canon["initial_state"]}
    )
    compiled = compile_plan_state(canon, [normalized])[0]

    assert compiled["state_transitions"] == [
        {
            "subject_id": "org-cooperative",
            "field": "status",
            "from_value": "not_founded",
            "to_value": "active",
        },
        {
            "subject_id": "char-he",
            "field": "permissions",
            "from_value": ["perm-trial"],
            "to_value": ["perm-trial", "perm-stamp"],
        },
    ]
    assert compiled["location_transitions"] == []


def _contract(transition):
    return {
        "state_transitions": [transition],
        "knowledge_grants": [],
        "location_transitions": [],
        "execution_contracts": [],
    }
