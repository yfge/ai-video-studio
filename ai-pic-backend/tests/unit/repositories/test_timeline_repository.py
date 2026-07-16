from sqlalchemy import event

from app.models.script import Episode, Script, Story
from app.models.timeline import Timeline
from app.repositories.timeline_repository import TimelineRepository


def test_episode_timeline_list_sorts_only_identifiers(db_session):
    story = Story(title="Story", genre="test", theme="t", target_audience="all")
    episode = Episode(title="Episode", story=story, episode_number=1)
    script = Script(title="Script", episode=episode, content="")
    older = Timeline(
        episode=episode,
        script=script,
        title="Older",
        status="draft",
        spec={"payload": "x" * 300_000},
        version=1,
    )
    latest = Timeline(
        episode=episode,
        script=script,
        title="Latest",
        status="draft",
        spec={"payload": "y" * 300_000},
        version=2,
    )
    db_session.add_all([story, episode, script, older, latest])
    db_session.commit()

    statements: list[str] = []

    def capture_statement(_conn, _cursor, statement, _params, _context, _many):
        if "FROM timelines" in statement:
            statements.append(statement)

    event.listen(db_session.bind, "before_cursor_execute", capture_statement)
    try:
        result = TimelineRepository(db_session).list_for_episode(episode.id)
    finally:
        event.remove(db_session.bind, "before_cursor_execute", capture_statement)

    assert [timeline.id for timeline in result] == [latest.id, older.id]
    ordered_statement = next(
        statement
        for statement in statements
        if "ORDER BY timelines.updated_at" in statement
    )
    ordered_projection = ordered_statement.split("FROM timelines", maxsplit=1)[0]
    assert "timelines.spec" not in ordered_projection
    assert "SELECT timelines.id" in ordered_projection


def test_latest_timeline_sorts_only_the_primary_key(db_session):
    story = Story(title="Story", genre="test", theme="t", target_audience="all")
    episode = Episode(title="Episode", story=story, episode_number=1)
    script = Script(title="Script", episode=episode, content="")
    older = Timeline(
        episode=episode,
        script=script,
        title="Older",
        status="draft",
        spec={"payload": "x" * 300_000},
        version=1,
    )
    latest = Timeline(
        episode=episode,
        script=script,
        title="Latest",
        status="draft",
        spec={"payload": "y" * 300_000},
        version=2,
    )
    db_session.add_all([story, episode, script, older, latest])
    db_session.commit()

    statements: list[str] = []

    def capture_statement(_conn, _cursor, statement, _params, _context, _many):
        if "FROM timelines" in statement:
            statements.append(statement)

    event.listen(db_session.bind, "before_cursor_execute", capture_statement)
    try:
        result = TimelineRepository(db_session).get_latest_for_episode_script(
            episode_id=episode.id,
            script_id=script.id,
        )
    finally:
        event.remove(db_session.bind, "before_cursor_execute", capture_statement)

    assert result is not None
    assert result.id == latest.id
    ordered_statement = next(
        statement
        for statement in statements
        if "ORDER BY timelines.version" in statement
    )
    ordered_projection = ordered_statement.split("FROM timelines", maxsplit=1)[0]
    assert "timelines.spec" not in ordered_projection
    assert "SELECT timelines.id" in ordered_projection
