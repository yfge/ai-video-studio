import pytest
from fastapi.routing import APIRoute

from app.main import create_app
from app.models.script import Story
from app.models.story_structure import StoryTreatment


@pytest.mark.unit
def test_story_structure_routes_present():
    app = create_app()
    paths = {r.path for r in app.routes if isinstance(r, APIRoute)}

    # Minimal presence checks (no DB required)
    assert "/api/v1/story-structure/scripts/{script_id}/scenes" in paths
    assert "/api/v1/story-structure/scenes/{scene_id}/beats" in paths
    assert "/api/v1/story-structure/scenes/{scene_id}/shots" in paths
    assert "/api/v1/story-structure/stories/{story_id}/treatments" in paths
    # creation endpoints present
    assert any(
        p
        for p in paths
        if p == "/api/v1/story-structure/scripts/{script_id}/scenes"
        and any(
            r.methods and "POST" in r.methods
            for r in app.routes
            if isinstance(r, APIRoute) and r.path == p
        )
    )
    assert any(
        p
        for p in paths
        if p == "/api/v1/story-structure/scenes/{scene_id}/shots"
        and any(
            r.methods and "POST" in r.methods
            for r in app.routes
            if isinstance(r, APIRoute) and r.path == p
        )
    )
    assert "/api/v1/story-structure/treatments/{treatment_id}/step-outlines" in paths
    assert any(
        p
        for p in paths
        if p == "/api/v1/story-structure/treatments/{treatment_id}/step-outlines"
        and any(
            r.methods and "POST" in r.methods
            for r in app.routes
            if isinstance(r, APIRoute) and r.path == p
        )
    )
    # seed endpoint present
    assert "/api/v1/story-structure/scripts/{script_id}/seed-from-json" in paths


def test_create_step_outline_requires_matching_story(client, db_session):
    story = Story(title="Story", genre="drama")
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    treatment = StoryTreatment(
        id=1,
        story_id=story.id,
        revision_number=1,
        status="draft",
        title="Treatment 1",
    )
    db_session.add(treatment)
    db_session.commit()
    db_session.refresh(treatment)

    payload = {
        "story_id": story.id,
        "story_treatment_id": treatment.id,
        "sequence_number": 1,
        "beat_title": "Opening",
        "beat_summary": "Intro beat",
        "act_label": "ACT I",
        "metadata": {"source": "test"},
    }

    ok_resp = client.post(
        f"/api/v1/story-structure/treatments/{treatment.id}/step-outlines",
        json=payload,
    )
    assert ok_resp.status_code == 200
    ok_data = ok_resp.json()
    assert ok_data["story_id"] == story.id
    assert ok_data["sequence_number"] == 1

    mismatched_story = Story(title="Another", genre="drama")
    db_session.add(mismatched_story)
    db_session.commit()
    db_session.refresh(mismatched_story)

    bad_payload = {**payload, "story_id": mismatched_story.id, "sequence_number": 2}
    bad_resp = client.post(
        f"/api/v1/story-structure/treatments/{treatment.id}/step-outlines",
        json=bad_payload,
    )
    assert bad_resp.status_code == 400

    list_resp = client.get(
        f"/api/v1/story-structure/treatments/{treatment.id}/step-outlines"
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
