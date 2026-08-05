from types import SimpleNamespace

import pytest
from app.services.story.story_novel_context_utils import value_hash
from app.services.story.story_novel_invocation_evidence import GeneratedNovelText
from app.services.story.story_novel_v3_generation import _generate_with_format_repair
from app.services.story.story_novel_v4_call_snapshot import (
    archive_regenerated_chapter_calls,
    freeze_v4_call_input,
    frozen_prompt_and_replay,
)


class _DB:
    def commit(self):
        pass

    def rollback(self):
        pass


class _Repo:
    def __init__(self, revision):
        self.revision = revision

    def revision_by_id(self, _revision_id, for_update=False):
        assert for_update
        return self.revision


def test_first_frozen_call_preserves_managed_prompt_object():
    class ManagedPrompt(str):
        pass

    prompt = ManagedPrompt("managed")
    selected, replay = frozen_prompt_and_replay(
        lambda _stage, text: {"normalized_input": str(text)}, "prose.1", prompt
    )
    assert selected is prompt
    assert replay is None

    selected, _replay = frozen_prompt_and_replay(
        lambda _stage, text: {
            "normalized_input": str(text),
            "input_hash": value_hash(str(text)),
            "_reuse_existing_input": True,
        },
        "prose.1",
        prompt,
    )
    assert selected is prompt


@pytest.mark.asyncio
async def test_resume_replays_result_with_original_frozen_input(monkeypatch):
    revision = SimpleNamespace(
        id=1,
        business_id="revision-v4",
        continuity_ledger={
            "chapters": {
                "3": {
                    "body_hash": "body",
                    "planner_snapshot_hash": "planner",
                    "model_call_snapshots": {},
                }
            }
        },
    )
    service = SimpleNamespace(db=_DB(), repo=_Repo(revision))
    entry = {
        "body_hash": "body",
        "planner_snapshot_hash": "planner",
    }
    freeze_v4_call_input(service, revision, 3, entry, "local_repair.3", "ORIGINAL")
    replay = GeneratedNovelText(
        '{"ok":true}',
        {"invocation_id": 3968, "input_tokens": 10, "output_tokens": 5},
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_v4_call_snapshot._replay_model_result",
        lambda *_args: replay,
    )
    provider_calls = 0

    async def provider(*_args, **_kwargs):
        nonlocal provider_calls
        provider_calls += 1
        return "unexpected"

    before_call = lambda stage, prompt: freeze_v4_call_input(
        service,
        revision,
        3,
        entry,
        stage,
        prompt,
        reuse_existing_input=True,
    )
    value, metrics = await _generate_with_format_repair(
        revision,
        "REBUILT-DIFFERENTLY",
        lambda text: text,
        provider,
        stage="local_repair.3",
        max_tokens=4000,
        before_call=before_call,
    )

    assert value == replay
    assert provider_calls == 0
    assert metrics["invocation_ids"] == [3968]


def test_resume_still_rejects_changed_source_binding(monkeypatch):
    revision = SimpleNamespace(
        id=1,
        business_id="revision-v4",
        continuity_ledger={"chapters": {"3": {"body_hash": "old"}}},
    )
    service = SimpleNamespace(db=_DB(), repo=_Repo(revision))
    entry = {"body_hash": "old"}
    freeze_v4_call_input(service, revision, 3, entry, "prose.3", "ORIGINAL")
    revision.continuity_ledger["chapters"]["3"]["body_hash"] = "changed"
    entry["body_hash"] = "changed"

    with pytest.raises(ValueError, match="发生变化"):
        freeze_v4_call_input(
            service,
            revision,
            3,
            entry,
            "prose.3",
            "REBUILT",
            reuse_existing_input=True,
        )


def test_explicit_regeneration_archives_only_body_attempt_calls():
    entry = {
        "model_call_snapshots": {
            "arc_planning.arc-001": {"snapshot_hash": "arc"},
            "chapter_planning.3": {"snapshot_hash": "planner"},
            "prose.3": {"snapshot_hash": "prose"},
            "audit.3.body-hash": {"snapshot_hash": "audit"},
            "local_repair.3": {"snapshot_hash": "repair"},
            "local_repair.3.format_repair": {"snapshot_hash": "format"},
        }
    }

    assert archive_regenerated_chapter_calls(entry, 3) is True
    assert list(entry["model_call_snapshots"]) == [
        "arc_planning.arc-001",
        "chapter_planning.3",
    ]
    assert {
        item["logical_stage"] for item in entry["regenerated_model_call_snapshots"]
    } == {
        "prose.3",
        "audit.3.body-hash",
        "local_repair.3",
        "local_repair.3.format_repair",
    }
    assert all(
        item["reason"] == "explicit_chapter_regeneration"
        for item in entry["regenerated_model_call_snapshots"]
    )
