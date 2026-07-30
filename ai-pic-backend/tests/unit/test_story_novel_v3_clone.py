from app.services.story.story_novel_v3_clone import clone_generation_plan


def test_v3_clone_drops_runtime_status_without_mutating_source():
    source = {
        "schema": "story_novel_generation_plan.v3",
        "chapters": [
            {
                "position": 1,
                "title": "春耕",
                "generation_status": "ready",
                "actual_chars": 2400,
                "body_hash": "body",
                "source_hash": "source",
                "context_hash": "context",
                "length_status": "ready",
                "state_compiler": {"version": 1},
            }
        ],
    }

    cloned = clone_generation_plan(source)

    assert cloned["chapters"] == [
        {"position": 1, "title": "春耕", "state_compiler": {"version": 1}}
    ]
    assert source["chapters"][0]["generation_status"] == "ready"
