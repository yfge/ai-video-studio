from sqlalchemy import String

from app.models.video_generation_task import VideoGenerationTask


def test_video_provider_task_id_column_length_is_safe():
    col = VideoGenerationTask.__table__.columns["provider_task_id"]
    assert isinstance(col.type, String)
    assert (col.type.length or 0) >= 512

