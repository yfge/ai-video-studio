from tests.factories import EpisodeFactory, ScriptFactory, StoryFactory, setup_factories


def test_scoring_endpoints_work_with_script_id(client, db_session, mock_ai_service):
    setup_factories(db_session)

    story = StoryFactory(
        extra_metadata={"market_region": "NA", "micro_genre": "test-micro-genre"}
    )
    episode = EpisodeFactory(story=story, episode_number=1)
    script = ScriptFactory(
        episode=episode,
        content="INT. ROOM - DAY\nA: Hello.",
        scenes=[
            {"scene_number": 1, "location": "Room", "time": "Day", "description": "Mock"}
        ],
        dialogues=[{"scene_number": 1, "character": "A", "content": "Hello"}],
        extra_metadata={"hook_plan": {"opening_hook": "mock"}},
    )
    db_session.commit()

    score_res = client.get(f"/api/v1/scoring/score/{script.id}")
    assert score_res.status_code == 200
    score = score_res.json()
    assert score.get("overall_score") is not None
    assert isinstance(score.get("dimension_scores"), dict)

    traffic_res = client.get(f"/api/v1/scoring/traffic-sheet/{script.id}")
    assert traffic_res.status_code == 200
    traffic = traffic_res.json()
    assert isinstance(traffic.get("assets"), list)
    assert traffic["assets"], "expected at least one traffic asset"

