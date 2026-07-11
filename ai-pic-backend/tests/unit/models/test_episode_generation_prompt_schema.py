from app.models.script import Episode
from sqlalchemy.dialects import mysql


def test_episode_generation_prompt_uses_mysql_longtext():
    column = Episode.__table__.columns["generation_prompt"]

    mysql_type = column.type.dialect_impl(mysql.dialect())

    assert isinstance(mysql_type, mysql.LONGTEXT)
