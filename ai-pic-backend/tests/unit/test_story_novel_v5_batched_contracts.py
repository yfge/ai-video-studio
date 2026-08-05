from app.services.story.story_novel_v5_batched_contracts import causal_contract


def test_causal_contract_exposes_only_causal_predicates_to_planner():
    schema = {
        "predicates": [
            {"id": "state", "persistence": "causal"},
            {"id": "mood", "persistence": "observational"},
        ]
    }
    rows = [{"position": 1}]
    before = {
        "schema": "story_novel_fact_graph.v1",
        "entities": [],
        "facts": [],
        "snapshot_hash": "before",
    }
    partial = {"events": [], "obligations": []}

    contract = causal_contract(
        {"chapter_count": 1},
        rows,
        schema,
        before,
        partial,
        is_final=True,
    )

    assert [item["id"] for item in contract["consistency_schema"]["predicates"]] == [
        "state"
    ]
    assert [item["id"] for item in schema["predicates"]] == ["state", "mood"]
