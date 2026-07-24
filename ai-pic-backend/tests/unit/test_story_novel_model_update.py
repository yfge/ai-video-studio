import copy
from types import SimpleNamespace

from app.schemas.story_novel_export import (
    StoryNovelCreateRevisionRequest,
    StoryNovelLengthSpecUpdateRequest,
)
from app.services.story.story_novel_length_service import build_length_plan
from app.services.story.story_novel_revision_service import StoryNovelRevisionService


def _revision():
    outline = {
        "status": "confirmed",
        "version": 3,
        "chapters": [
            {
                "position": 1,
                "title": "第一章",
                "goal": "推进冲突",
                "key_events": ["发现线索"],
                "character_focus": ["主角"],
                "open_threads": [],
                "end_state": "继续追查",
            }
        ],
    }
    story_seed = {
        "schema": "story_seed_v2",
        "structured_outline": outline,
    }
    story = SimpleNamespace(
        story_seed=story_seed,
        story_seed_status="confirmed",
        story_seed_version=3,
    )
    plan = build_length_plan(story, StoryNovelCreateRevisionRequest())
    plan.update(
        {
            "status": "planning",
            "phase": "chapters",
            "canon": {"schema": "story_novel_canon.v1", "entities": []},
            "canon_hash": "a" * 64,
        }
    )
    return SimpleNamespace(
        generation_plan=plan,
        story_snapshot={"story_seed": story_seed, "story_seed_version": 3},
        model=None,
        chapters=[],
        continuity_ledger={"schema": "story_novel_continuity.v3", "chapters": {}},
        continuity_status="unchecked",
        continuity_report=None,
        chapter_count=1,
        target_words=4000,
    )


class _Db:
    committed = False
    refreshed = None

    def commit(self):
        self.committed = True

    def refresh(self, value):
        self.refreshed = value


def test_model_only_update_versions_plan_and_preserves_canon_checkpoint():
    revision = _revision()
    before = copy.deepcopy(revision.generation_plan)
    db = _Db()
    service = SimpleNamespace(
        revision=lambda _: revision,
        _ensure_draft=lambda _: None,
        ensure_no_active_task=lambda _: None,
        db=db,
    )

    result = StoryNovelRevisionService.update_length_spec(
        service,
        "revision-1",
        StoryNovelLengthSpecUpdateRequest(
            length_profile_id="standard_serial",
            expected_plan_version=4,
            model="deepseek:deepseek-v4-flash",
        ),
    )

    assert result is revision
    assert revision.model == "deepseek:deepseek-v4-flash"
    assert revision.generation_plan != before
    assert revision.generation_plan["version"] == 5
    assert revision.generation_plan["model"] == "deepseek:deepseek-v4-flash"
    assert revision.generation_plan["canon_hash"] == "a" * 64
    assert revision.generation_plan["canon"] == before["canon"]
    assert revision.continuity_status == "review_required"
    assert db.committed is True
    assert db.refreshed is revision
