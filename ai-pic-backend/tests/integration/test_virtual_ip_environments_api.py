from __future__ import annotations

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.main import app
from app.models.story_structure import Environment
from app.models.user import User
from app.models.virtual_ip import VirtualIP, VirtualIPEnvironment
from fastapi.testclient import TestClient


def _user(db, username: str, *, admin: bool = False) -> User:
    user = User(
        username=username,
        email=f"{username}@example.com",
        hashed_password="x",
        is_active=True,
        is_approved=True,
        email_verified=True,
        is_admin=admin,
        is_superuser=admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _virtual_ip(db, user: User, name: str = "角色") -> VirtualIP:
    vip = VirtualIP(name=name, user_id=user.id, is_active=True)
    db.add(vip)
    db.commit()
    db.refresh(vip)
    return vip


def _environment(db, user: User, name: str = "环境") -> Environment:
    env = Environment(
        user_id=user.id,
        name=name,
        category="indoor",
        description="可复用场景资产",
    )
    db.add(env)
    db.commit()
    db.refresh(env)
    return env


def test_link_update_unlink_virtual_ip_environment(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    vip = _virtual_ip(db_session, user)
    env = _environment(db_session, user)

    response = client.post(
        f"/api/v1/virtual-ips/{vip.id}/environments",
        json={"environment_id": env.id, "usage_type": "home", "sort_order": 2},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["virtual_ip_id"] == vip.id
    assert payload["environment_id"] == env.id
    assert payload["environment"]["name"] == env.name

    duplicate = client.post(
        f"/api/v1/virtual-ips/{vip.id}/environments",
        json={"environment_id": env.id, "usage_type": "home", "sort_order": 3},
    )
    assert duplicate.status_code == 200
    assert db_session.query(VirtualIPEnvironment).count() == 1

    updated = client.put(
        f"/api/v1/virtual-ips/{vip.id}/environments/{env.id}",
        json={"usage_note": "主场景", "is_default": True},
    )
    assert updated.status_code == 200
    assert updated.json()["usage_note"] == "主场景"
    assert updated.json()["is_default"] is True

    listed = client.get(f"/api/v1/virtual-ips/{vip.business_id}/environments")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    removed = client.delete(f"/api/v1/virtual-ips/{vip.id}/environments/{env.id}")
    assert removed.status_code == 204
    assert (
        db_session.query(VirtualIPEnvironment)
        .filter(VirtualIPEnvironment.is_deleted.is_(False))
        .count()
        == 0
    )
    assert db_session.query(Environment).filter(Environment.id == env.id).first()


def test_environment_response_includes_linked_virtual_ips(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    vip = _virtual_ip(db_session, user, "林雪")
    env = _environment(db_session, user, "公寓")

    response = client.post(
        f"/api/v1/virtual-ips/{vip.id}/environments",
        json={"environment_id": env.id},
    )
    assert response.status_code == 200

    env_response = client.get(f"/api/v1/story-structure/environments/{env.id}")
    assert env_response.status_code == 200
    payload = env_response.json()
    assert payload["linked_virtual_ip_count"] == 1
    assert payload["linked_virtual_ips"][0]["name"] == "林雪"


def test_virtual_ip_environment_user_isolation(db_session):
    user_a = _user(db_session, "env_owner_a")
    user_b = _user(db_session, "env_owner_b")
    vip_a = _virtual_ip(db_session, user_a, "A")
    env_b = _environment(db_session, user_b, "B Env")

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: user_a
    try:
        with TestClient(app) as client:
            response = client.post(
                f"/api/v1/virtual-ips/{vip_a.id}/environments",
                json={"environment_id": env_b.id},
            )
            assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
