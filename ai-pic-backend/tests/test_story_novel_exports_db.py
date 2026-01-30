import pytest
from app.models.script import Story
from app.models.story_novel_export import StoryNovelExport
from app.models.task import Task, TaskStatus, TaskType
from app.models.user import User


@pytest.mark.integration
def test_story_novel_download_falls_back_to_db(client, db_session):
    user = db_session.query(User).filter(User.username == "test_admin").first()
    assert user is not None

    story = Story(title="Test Story", genre="Romance", user_id=user.id)
    db_session.add(story)
    db_session.commit()
    db_session.refresh(story)

    task = Task(
        title="Export Novel",
        description="Done",
        task_type=TaskType.IMAGE_GENERATION,
        status=TaskStatus.COMPLETED,
        prompt="noop",
        parameters="{}",
        result_file_path="novel_file:exports/novels/missing.txt",
        user_id=user.id,
        target_business_id=story.business_id,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    export_row = StoryNovelExport(
        story_id=story.id,
        story_business_id=story.business_id,
        task_id=task.id,
        user_id=user.id,
        style="zhihu",
        target_words=20000,
        chapter_count=10,
        total_words=20000,
        model="openai:gpt-4o-mini",
        temperature=0.7,
        file_relative_path="exports/novels/missing.txt",
        content_text="Hello from DB export",
    )
    db_session.add(export_row)
    db_session.commit()

    response = client.get(f"/api/v1/stories/novel/tasks/{task.id}/download")
    assert response.status_code == 200, response.text
    assert "Hello from DB export" in response.text
    assert response.headers.get("content-disposition", "").startswith("attachment;")
