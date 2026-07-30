from types import SimpleNamespace

from app.services.story.story_novel_resume_cursor import advance_resume_cursor


def test_ready_chapter_advances_resume_cursor_to_first_non_ready_position():
    revision = SimpleNamespace(
        continuity_ledger={
            "state_status": "failed",
            "stale_from_position": 1,
            "chapters": {
                "1": {"status": "ready"},
                "2": {"status": "audit"},
            },
        }
    )

    advance_resume_cursor(revision, [{"position": 1}, {"position": 2}])

    assert revision.continuity_ledger["stale_from_position"] == 2
    assert revision.continuity_ledger["state_status"] == "stale"


def test_all_ready_chapters_clear_resume_cursor():
    revision = SimpleNamespace(
        continuity_ledger={
            "state_status": "stale",
            "stale_from_position": 2,
            "chapters": {
                "1": {"status": "ready"},
                "2": {"status": "ready"},
            },
        }
    )

    advance_resume_cursor(revision, [{"position": 1}, {"position": 2}])

    assert "stale_from_position" not in revision.continuity_ledger
    assert revision.continuity_ledger["state_status"] == "ready"
