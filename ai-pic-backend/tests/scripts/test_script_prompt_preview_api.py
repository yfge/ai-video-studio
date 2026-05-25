from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from tests.factories import EpisodeFactory, setup_factories


def test_preview_script_prompt(client: TestClient, db_session: Session):
    setup_factories(db_session)

    episode = EpisodeFactory()

    response = client.post(
        "/api/v1/scripts/prompt/preview",
        json={
            "episode_id": episode.id,
            "format_type": "screenplay",
            "language": "zh-CN",
            "dialogue_style": "natural",
            "scene_detail_level": "medium",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["data"]["prompt"]
