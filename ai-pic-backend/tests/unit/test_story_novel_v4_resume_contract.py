from types import SimpleNamespace

import pytest
from app.services.story.story_novel_context_utils import value_hash
from app.services.story.story_novel_plan_hash import generation_plan_hash
from app.services.story.story_novel_resume_cursor import resume_suffix_plan_rows
from app.services.story.story_novel_v4_call_snapshot import (
    freeze_v4_call_input,
    valid_call_snapshot,
)
from app.services.story.story_novel_v4_plan_reset import (
    reset_stale_snapshot_suffix,
    reset_v4_plan_from,
)
from app.services.story.story_novel_v4_snapshot_guard import (
    _selected_sources_current,
    lock_current_snapshot_source,
)
from fastapi import HTTPException


class _DB:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        pass


class _Repo:
    def __init__(self, revision):
        self.revision = revision

    def revision_by_id(self, _revision_id, for_update=False):
        assert for_update
        return self.revision


def _revision():
    plan = {
        "schema": "story_novel_generation_plan.v4",
        "canon": {"canon_hash": "canon", "milestones": [], "entities": []},
        "canon_hash": "canon",
        "chapters": [
            {
                "position": 1,
                "title": "第一章",
                "goal": "开始",
                "key_events": ["事件"],
                "character_focus": [],
                "open_threads": [],
                "end_state": "结束",
                "min_chars": 2000,
                "target_chars": 2400,
                "max_chars": 3000,
                "length_source": "profile",
                "required_event_ids": ["event-1-1"],
                "timeline_event_bindings": {},
                "milestones_consumed": [],
                "forbidden_event_ids": [],
                "payoffs_due": [],
                "canon_refs": [],
                "future_guard_entity_ids": [],
                "contract_status": "compiled",
                "execution_contracts": [{"contract_id": "event:event-1-1"}],
            }
        ],
        "compiled_chapter_count": 1,
        "planning_invocations": {
            "entries": [
                {"logical_stage": "canon", "positions": []},
                {"logical_stage": "chapter_package.1", "positions": [1]},
            ]
        },
    }
    return SimpleNamespace(
        id=1,
        chapters=[],
        generation_plan=plan,
        continuity_ledger={
            "schema": "story_novel_continuity.v5",
            "chapters": {
                "1": {
                    "status": "snapshot_stale",
                    "execution_generation_plan_hash": "execution-plan",
                }
            },
            "stale_from_position": 1,
        },
    )


def test_same_call_stage_cannot_change_its_frozen_input():
    revision = _revision()
    service = SimpleNamespace(db=_DB(), repo=_Repo(revision))
    entry = {
        "planner_snapshot_hash": "planner",
        "execution_generation_plan_hash": "execution-plan",
        "source_manifest": {},
    }
    first = freeze_v4_call_input(service, revision, 1, entry, "prose.1", "A")
    assert valid_call_snapshot(first)
    assert first["execution_generation_plan_hash"] == "execution-plan"
    assert freeze_v4_call_input(service, revision, 1, entry, "prose.1", "A") == first
    with pytest.raises(ValueError, match="发生变化"):
        freeze_v4_call_input(service, revision, 1, entry, "prose.1", "B")


def test_formal_resume_archives_failed_planning_calls_but_keeps_planner_snapshot():
    revision = _revision()
    revision.generation_plan["chapters"][0]["position"] = 5
    entry = {
        "status": "chapter_planning",
        "stage": "planner_snapshot_ready",
        "planner_snapshot": {"snapshot_hash": "planner"},
        "planner_snapshot_hash": "planner",
        "source_manifest": {"event_ids": ["event-1"]},
        "model_call_snapshots": {
            "chapter_planning.5": {"snapshot_hash": "first"},
            "chapter_planning.5.format_repair": {"snapshot_hash": "repair"},
            "arc_planning.arc-001": {"snapshot_hash": "arc"},
        },
    }
    revision.continuity_ledger = {
        "schema": "story_novel_continuity.v5",
        "chapters": {"5": entry},
        "stale_from_position": 5,
    }
    service = SimpleNamespace(db=_DB(), repo=_Repo(revision))

    assert (
        resume_suffix_plan_rows(service, revision, revision.generation_plan["chapters"])
        == revision.generation_plan["chapters"]
    )
    assert service.db.commits == 1
    entry = revision.continuity_ledger["chapters"]["5"]
    assert entry["planner_snapshot_hash"] == "planner"
    assert entry["source_manifest"] == {"event_ids": ["event-1"]}
    assert list(entry["model_call_snapshots"]) == [
        "chapter_planning.5",
        "arc_planning.arc-001",
    ]
    assert [item["logical_stage"] for item in entry["failed_model_call_snapshots"]] == [
        "chapter_planning.5.format_repair",
    ]


def test_stale_snapshot_resume_resets_derived_contract_suffix():
    revision = _revision()
    reset = reset_stale_snapshot_suffix(revision, 1)
    assert reset == 1
    assert revision.generation_plan["compiled_chapter_count"] == 0
    assert revision.generation_plan["chapters"][0]["contract_status"] == "pending"
    assert revision.continuity_ledger["chapters"] == {}
    assert all(
        not item["logical_stage"].startswith("chapter_package.")
        for item in revision.generation_plan["planning_invocations"]["entries"]
    )


def test_gate_failed_resume_discards_failed_intent_and_entity_proposals():
    revision = _revision()
    entry = revision.continuity_ledger["chapters"]["1"]
    entry.update(
        status="gate_failed",
        chapter_intent={"entity_proposals": [{"name": "failed-entity"}]},
    )

    assert reset_stale_snapshot_suffix(revision, 1) == 1
    assert revision.continuity_ledger["chapters"] == {}
    assert revision.generation_plan["chapters"][0]["contract_status"] == "pending"


def test_plan_reset_does_not_mutate_source():
    revision = _revision()
    source_hash = value_hash(revision.generation_plan)
    reset = reset_v4_plan_from(revision.generation_plan, 1)
    assert value_hash(revision.generation_plan) == source_hash
    assert reset["plan_hash"]


def test_provider_result_is_rejected_when_frozen_plan_changed(monkeypatch):
    revision = _revision()
    revision.generation_plan["plan_hash"] = "live-plan"
    service = SimpleNamespace(
        db=_DB(),
        repo=_Repo(revision),
        _invalidate_from=lambda _revision, _position: None,
    )
    monkeypatch.setattr(
        "app.services.story.story_novel_v4_snapshot_guard.source_manifest_current",
        lambda *_args: True,
    )
    snapshot = {
        "position": 1,
        "generation_plan_hash": "provider-input-plan",
        "canon_hash": "canon",
        "source_manifest": {},
    }

    with pytest.raises(HTTPException, match="generation plan hash changed"):
        lock_current_snapshot_source(service, revision, snapshot)

    entry = revision.continuity_ledger["chapters"]["1"]
    assert entry["status"] == "snapshot_stale"


def test_selected_planning_evidence_requires_exact_source_hash():
    rows = [{"business_id": "event-a", "source_hash": "source-a"}]
    manifest = {"event_ids": ["event-a"], "event_hashes": ["source-a"]}

    assert _selected_sources_current(rows, "event", manifest)
    manifest["event_hashes"] = ["changed"]
    assert not _selected_sources_current(rows, "event", manifest)


@pytest.mark.parametrize(
    "path,replacement",
    [
        (("chapters", 0, "entity_introductions"), [{"id": "entity-new"}]),
        (("series_roadmap", "arcs"), [{"arc_id": "changed"}]),
        (("scope_graph", "nodes"), [{"scope_id": "changed"}]),
        (("world_reveal_index",), {"index_hash": "changed"}),
        (("world_reveal_hash",), "changed"),
        (("prompt_templates",), {"schema": "changed"}),
        (("event_execution_contract_version",), 2),
        (("prose_execution_boundary_version",), 2),
        (("chapter_effect_manifest_version",), 2),
        (("state_compiler_version",), 2),
    ],
)
def test_v4_plan_hash_covers_authoritative_runtime_contracts(path, replacement):
    plan = _revision().generation_plan
    plan.update(
        series_bible={"core_promises": ["promise"]},
        series_roadmap={"arcs": [{"arc_id": "arc-1"}]},
        current_arc_plan={"arc_id": "arc-1"},
        arc_plans={"arc-1": {"arc_id": "arc-1"}},
        scope_graph={"nodes": [{"scope_id": "home"}], "edges": []},
    )
    plan["chapters"][0]["entity_introductions"] = []
    original = generation_plan_hash(plan)
    target = plan
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement
    assert generation_plan_hash(plan) != original
