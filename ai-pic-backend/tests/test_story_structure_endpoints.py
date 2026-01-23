from __future__ import annotations

from app.core.database import Base, get_db
from app.core.middleware import get_current_active_user
from app.main import app
from app.models.script import Episode, Script, Story
from app.models.user import User
from app.schemas.story_structure import SceneBeatCreate, SceneCreate, ShotCreate
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _create_test_user(db: Session) -> User:
    user = User(
        username="test_user",
        email="test_user@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _bootstrap_script(db: Session) -> Script:
    story = Story(title="Story", genre="g", theme="t", target_audience="all")
    episode = Episode(title="Ep1", story=story, episode_number=1)
    script = Script(title="Script", episode=episode, content="")
    db.add_all([story, episode, script])
    db.commit()
    db.refresh(script)
    return script


def test_scene_crud_with_children(db_session: Session):
    # ensure tables exist for this session
    Base.metadata.create_all(bind=db_session.get_bind())

    user = _create_test_user(db_session)
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_active_user] = lambda: user
    client = TestClient(app)

    script = _bootstrap_script(db_session)

    # create scene
    scene_payload = {
        "script_id": script.id,
        "scene_number": "1",
        "slug_line": "INT. TEST - DAY",
    }
    res = client.post(
        f"/api/v1/story-structure/scripts/{script.id}/scenes", json=scene_payload
    )
    assert res.status_code == 200
    scene_id = res.json()["id"]

    # update scene
    res = client.put(
        f"/api/v1/story-structure/scenes/{scene_id}", json={"location": "Office"}
    )
    assert res.status_code == 200
    assert res.json()["location"] == "Office"

    # add beat
    beat_payload = {
        "scene_id": scene_id,
        "order_index": 1,
        "beat_summary": "first",
    }
    res = client.post(
        f"/api/v1/story-structure/scenes/{scene_id}/beats", json=beat_payload
    )
    assert res.status_code == 200
    beat_id = res.json()["id"]

    # update beat
    res = client.put(
        f"/api/v1/story-structure/scene-beats/{beat_id}",
        json={"beat_summary": "updated"},
    )
    assert res.status_code == 200
    assert res.json()["beat_summary"] == "updated"

    # add shots via service helper path
    shot_payload = {
        "scene_id": scene_id,
        "shot_number": "1A",
    }
    res = client.post(
        f"/api/v1/story-structure/scenes/{scene_id}/shots", json=shot_payload
    )
    assert res.status_code == 200
    shot_id = res.json()["id"]

    # update shot
    res = client.put(
        f"/api/v1/story-structure/shots/{shot_id}", json={"shot_type": "WS"}
    )
    assert res.status_code == 200
    assert res.json()["shot_type"] == "WS"

    # delete shot
    res = client.delete(f"/api/v1/story-structure/shots/{shot_id}")
    assert res.status_code == 204

    # delete scene
    res = client.delete(f"/api/v1/story-structure/scenes/{scene_id}")
    assert res.status_code == 204


def test_scene_beat_order_conflict_returns_400(db_session: Session):
    Base.metadata.create_all(bind=db_session.get_bind())
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    script = _bootstrap_script(db_session)

    scene = client.post(
        f"/api/v1/story-structure/scripts/{script.id}/scenes",
        json=SceneCreate(
            script_id=script.id, scene_number="1", slug_line="INT"
        ).model_dump(),
    ).json()

    first = SceneBeatCreate(
        scene_id=scene["id"], order_index=1, beat_summary="first"
    ).model_dump()
    assert (
        client.post(
            f"/api/v1/story-structure/scenes/{scene['id']}/beats", json=first
        ).status_code
        == 200
    )

    conflict = SceneBeatCreate(
        scene_id=scene["id"], order_index=1, beat_summary="duplicate"
    ).model_dump()
    res = client.post(
        f"/api/v1/story-structure/scenes/{scene['id']}/beats", json=conflict
    )

    assert res.status_code == 400
    assert res.json()["detail"] == "order_index already exists for scene"


def test_shot_duplicate_number_and_beat_mismatch(db_session: Session):
    Base.metadata.create_all(bind=db_session.get_bind())
    app.dependency_overrides[get_db] = lambda: db_session
    client = TestClient(app)
    script = _bootstrap_script(db_session)

    # scene A with beat
    scene_a = client.post(
        f"/api/v1/story-structure/scripts/{script.id}/scenes",
        json=SceneCreate(
            script_id=script.id, scene_number="1", slug_line="INT"
        ).model_dump(),
    ).json()
    beat = client.post(
        f"/api/v1/story-structure/scenes/{scene_a['id']}/beats",
        json=SceneBeatCreate(
            scene_id=scene_a["id"], order_index=1, beat_summary="first"
        ).model_dump(),
    ).json()

    # duplicate shot number in same scene
    first_shot = ShotCreate(scene_id=scene_a["id"], shot_number="1A").model_dump()
    assert (
        client.post(
            f"/api/v1/story-structure/scenes/{scene_a['id']}/shots", json=first_shot
        ).status_code
        == 200
    )
    res_dup = client.post(
        f"/api/v1/story-structure/scenes/{scene_a['id']}/shots", json=first_shot
    )
    assert res_dup.status_code == 400
    assert res_dup.json()["detail"] == "shot_number already exists for scene"

    # beat/scene mismatch
    scene_b = client.post(
        f"/api/v1/story-structure/scripts/{script.id}/scenes",
        json=SceneCreate(
            script_id=script.id, scene_number="2", slug_line="EXT"
        ).model_dump(),
    ).json()
    bad_shot = ShotCreate(
        scene_id=scene_b["id"], shot_number="2A", scene_beat_id=beat["id"]
    ).model_dump()
    res_mismatch = client.post(
        f"/api/v1/story-structure/scenes/{scene_b['id']}/shots", json=bad_shot
    )
    assert res_mismatch.status_code == 400
    assert res_mismatch.json()["detail"] == "beat does not belong to scene"


def test_environment_variants_pass_reference_images(db_session: Session, monkeypatch):
    Base.metadata.create_all(bind=db_session.get_bind())

    from app.api.v1.endpoints.story_structure import (
        environment_variants as environment_variants_module,
    )
    from app.core.middleware import get_current_active_user
    from app.models.story_structure import Environment
    from app.models.user import User

    user = User(
        username="env_test_user",
        email="env_test_user@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    env = Environment(
        user_id=user.id,
        name="Env",
        category="indoor",
        tags=[],
        description="Test environment",
        reference_images=["/uploads/base_env.png"],
    )
    db_session.add(env)
    db_session.commit()
    db_session.refresh(env)

    captured: dict[str, object] = {}

    class _DummyResp:
        def __init__(self) -> None:
            self.success = True
            self.data = {"images": ["https://example.com/mock-env-variant.png"]}
            self.provider = "mock-provider"
            self.model = "mock-model"
            self.usage = {}

    class _DummyAIManager:
        async def image_to_image(self, *args, **kwargs):
            captured["image_url"] = kwargs.get("image_url") or (
                args[0] if args else None
            )
            captured["extra_images"] = kwargs.get("extra_images")
            return _DummyResp()

    class _DummyAIService:
        def __init__(self) -> None:
            self.ai_manager = _DummyAIManager()

        async def _persist_generated_image(
            self,
            image_data: str,
            *,
            ip_name: str,
            category: str,
            prefix: str,
            metadata: dict | None = None,
            require_upload: bool = False,
        ) -> dict:
            return {
                "local_file_path": "/tmp/env_variant.png",
                "relative_path": "/uploads/env_variant.png",
                "file_size": 123,
                "filename": "env_variant.png",
                "oss_url": (
                    "https://oss.example.com/env_variant.png"
                    if require_upload
                    else None
                ),
                "oss_upload": {
                    "success": True,
                    "file_url": "https://oss.example.com/env_variant.png",
                },
            }

    dummy_service = _DummyAIService()
    monkeypatch.setattr(environment_variants_module, "ai_service", dummy_service)

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_active_user] = lambda: user
    client = TestClient(app)

    payload = {
        "base_image": "/uploads/base_env.png",
        "prompt": "variant",
        "reference_images": ["/uploads/ref_env.png"],
    }
    res = client.post(
        f"/api/v1/story-structure/environments/{env.id}/images/variants", json=payload
    )
    assert res.status_code == 200, res.text

    assert captured["extra_images"] == ["http://localhost:8000/uploads/ref_env.png"]
