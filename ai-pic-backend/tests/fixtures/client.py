import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.middleware import (
    get_current_active_user,
    get_current_admin_user,
    get_current_superuser,
)
from app.models.user import User
from main import app


@pytest.fixture
def client(db_session):
    """FastAPI test client with dependency overrides."""
    admin_user = db_session.query(User).filter(User.username == "test_admin").first()
    if not admin_user:
        admin_user = User(
            username="test_admin",
            email="test_admin@example.com",
            hashed_password="not-used-in-tests",
            full_name="Test Admin",
            is_active=True,
            is_approved=True,
            email_verified=True,
            is_admin=True,
            is_superuser=True,
        )
        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_active_user():
        return admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = override_active_user
    app.dependency_overrides[get_current_admin_user] = override_active_user
    app.dependency_overrides[get_current_superuser] = override_active_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Auth headers fixture (best-effort)."""
    login_data = {"username": "admin", "password": "Ai7dio"}
    response = client.post("/api/v1/auth/login", data=login_data)
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}


@pytest.fixture
def test_virtual_ip_data():
    return {
        "name": "测试IP",
        "description": "用于测试的虚拟IP",
        "tags": ["test", "ai"],
        "background_story": "这是一个测试用的虚拟IP角色",
        "style_prompt": "realistic, professional",
        "is_active": True,
        "is_public": False,
    }
