import pytest
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.core.middleware import get_current_active_user
from app.models.script import Story
from app.models.story_novel_export import StoryNovelExport
from app.models.user import User
from main import app


@pytest.mark.integration
def test_list_story_novel_exports_filters_by_user(db_session):
    user1 = User(
        username="u1",
        email="u1@example.com",
        hashed_password="x",
        full_name="User 1",
        is_active=True,
        is_approved=True,
        email_verified=True,
        is_admin=False,
        is_superuser=False,
    )
    user2 = User(
        username="u2",
        email="u2@example.com",
        hashed_password="x",
        full_name="User 2",
        is_active=True,
        is_approved=True,
        email_verified=True,
        is_admin=False,
        is_superuser=False,
    )
    db_session.add_all([user1, user2])
    db_session.commit()
    db_session.refresh(user1)
    db_session.refresh(user2)

    story = Story(title="Story", genre="Romance", user_id=user1.id)
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    export1 = StoryNovelExport(
        story_id=story.id,
        story_business_id=story.business_id,
        task_id=101,
        user_id=user1.id,
        style="zhihu",
        target_words=20000,
        chapter_count=10,
        total_words=20000,
        model="mock",
        temperature=0.7,
        file_relative_path="exports/novels/one.txt",
        content_text="one",
    )
    export2 = StoryNovelExport(
        story_id=story.id,
        story_business_id=story.business_id,
        task_id=102,
        user_id=user1.id,
        style="zhihu",
        target_words=20000,
        chapter_count=10,
        total_words=20000,
        model="mock",
        temperature=0.7,
        file_relative_path="exports/novels/two.txt",
        content_text="two",
    )
    other_user_export = StoryNovelExport(
        story_id=story.id,
        story_business_id=story.business_id,
        task_id=103,
        user_id=user2.id,
        style="zhihu",
        target_words=20000,
        chapter_count=10,
        total_words=20000,
        model="mock",
        temperature=0.7,
        file_relative_path="exports/novels/other.txt",
        content_text="other",
    )
    db_session.add_all([export1, export2, other_user_export])
    db_session.commit()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_active_user] = lambda: user1

    try:
        with TestClient(app) as client:
            resp = client.get(
                f"/api/v1/stories/business/{story.business_id}/novel/exports"
            )
            assert resp.status_code == 200, resp.text
            payload = resp.json()
            items = payload.get("items") or []
            assert len(items) == 2
            assert {item["task_id"] for item in items} == {101, 102}
            assert items[0]["id"] > items[1]["id"]
    finally:
        app.dependency_overrides.clear()

