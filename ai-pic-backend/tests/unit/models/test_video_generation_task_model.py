from app.models.video_generation_task import VideoGenerationTask
from sqlalchemy import String
from sqlalchemy.types import JSON


def test_video_provider_task_id_column_length_is_safe():
    col = VideoGenerationTask.__table__.columns["provider_task_id"]
    assert isinstance(col.type, String)
    assert (col.type.length or 0) >= 512


def test_video_generation_task_has_generation_metadata_column():
    col = VideoGenerationTask.__table__.columns["generation_metadata"]
    assert isinstance(col.type, JSON)
