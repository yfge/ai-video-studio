import json
from types import SimpleNamespace

import anyio
import pytest

from app.core.config import settings
from app.schemas.story_novel_export import NovelModelPolicy
from app.services.story.story_novel_length_service import build_length_plan
from app.services.story.story_novel_plan_versions import is_v5_plan
from app.services.story.story_novel_v3_clone import (
    clone_generation_plan,
    clone_ledger_schema,
)
from app.services.story.story_novel_v5_plan import freeze_v5_plan, valid_v5_plan
from app.services.story.story_novel_v5_planning import ensure_v5_generation_plan
from tests.unit.test_story_novel_model_policy_v3 import _request, _story


class _DB:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


def test_internal_switch_only_upgrades_new_explicit_policy_revision(monkeypatch):
    monkeypatch.setattr(settings, "STORY_NOVEL_DEFAULT_PLAN_VERSION", "v5")

    plan = build_length_plan(
        _story(), _request(model_policy=NovelModelPolicy(prose_model="deepseek:p"))
    )
    legacy = build_length_plan(_story(), _request(model="deepseek:legacy"))

    assert is_v5_plan(plan)
    assert legacy["schema"] == "story_novel_generation_plan.v2"


def test_v5_plan_freezes_hashes_and_clone_keeps_version_without_runtime():
    plan = freeze_v5_plan(
        {**_base_plan(), "schema_compile_revision_business_id": "revision-source"},
        _compile_payload(),
        _snapshot(),
        [],
    )

    assert valid_v5_plan(plan)
    assert plan["schema_compile_status"] == "frozen"
    assert plan["canon_view"]["counts"]["predicates"] == 1
    assert plan["chapters"][0]["required_event_ids"] == ["event-1"]
    changed = {**plan, "causal_graph_hash": "changed"}
    assert not valid_v5_plan(changed)

    plan["chapters"][0].update(
        generation_status="ready",
        snapshot_before_hash="before",
        snapshot_after_hash="after",
        readability_status="passed",
    )
    cloned = clone_generation_plan(plan)
    assert cloned["schema"] == "story_novel_generation_plan.v5"
    assert cloned["schema_compile_revision_business_id"] == "revision-source"
    assert "snapshot_after_hash" not in cloned["chapters"][0]
    assert clone_ledger_schema(plan) == "story_novel_continuity.v6"


def test_schema_compile_allows_one_repair_then_auto_freezes():
    revision = SimpleNamespace(
        business_id="revision-v5",
        generation_plan=_base_plan(),
        story_snapshot=_snapshot(),
        chapters=[],
    )
    task = SimpleNamespace(description="")
    service = SimpleNamespace(db=_DB())
    calls = []

    async def generate(_revision, _prompt, *, stage, **_kwargs):
        calls.append(stage)
        return "{}" if len(calls) == 1 else json.dumps(_compile_payload())

    result = anyio.run(ensure_v5_generation_plan, service, revision, task, generate)

    assert calls == ["consistency_schema.compile", "consistency_schema.repair"]
    assert result["schema_compile_status"] == "frozen"
    assert result["status"] == "ready"
    assert valid_v5_plan(result)
    assert service.db.commits == 3


def test_schema_repair_checkpoint_resumes_without_repeating_compile_call():
    revision = SimpleNamespace(
        business_id="revision-v5-resume",
        generation_plan=_base_plan(),
        story_snapshot=_snapshot(),
        chapters=[],
    )
    task = SimpleNamespace(description="")
    service = SimpleNamespace(db=_DB())
    first_calls = []

    async def interrupted(_revision, _prompt, *, stage, **_kwargs):
        first_calls.append(stage)
        if stage == "consistency_schema.compile":
            return "{}"
        raise RuntimeError("worker interrupted")

    with pytest.raises(RuntimeError, match="worker interrupted"):
        anyio.run(ensure_v5_generation_plan, service, revision, task, interrupted)
    assert first_calls == [
        "consistency_schema.compile",
        "consistency_schema.repair",
    ]
    assert revision.generation_plan["schema_compile_status"] == "repairing"

    resumed_calls = []

    async def resumed(_revision, _prompt, *, stage, **_kwargs):
        resumed_calls.append(stage)
        return json.dumps(_compile_payload())

    result = anyio.run(ensure_v5_generation_plan, service, revision, task, resumed)

    assert resumed_calls == ["consistency_schema.repair"]
    assert valid_v5_plan(result)


def test_long_v5_plan_compiles_causal_graph_in_resumable_batches():
    chapters = [
        {
            **_base_plan()["chapters"][0],
            "position": position,
            "title": f"第 {position} 章",
        }
        for position in range(1, 34)
    ]
    base = {
        **_base_plan(),
        "chapter_count": len(chapters),
        "chapters": chapters,
    }
    snapshot = _snapshot()
    snapshot["story_seed"]["structured_outline"]["chapters"] = [
        {"position": position} for position in range(1, 34)
    ]
    revision = SimpleNamespace(
        business_id="revision-v5-long",
        generation_plan=base,
        story_snapshot=snapshot,
        chapters=[],
    )
    task = SimpleNamespace(description="")
    service = SimpleNamespace(db=_DB())
    calls = []

    async def generate(_revision, _prompt, *, stage, **_kwargs):
        calls.append(stage)
        if stage == "consistency_schema.foundation":
            payload = _compile_payload()
            payload.pop("causal_event_graph")
            return json.dumps(payload)
        start, end = [int(value) for value in stage.rsplit(".", 1)[-1].split("-")]
        return json.dumps(_causal_batch(start, end))

    result = anyio.run(ensure_v5_generation_plan, service, revision, task, generate)

    assert calls == [
        "consistency_schema.foundation",
        "consistency_schema.causal.1-16",
        "consistency_schema.causal.17-32",
        "consistency_schema.causal.33-33",
    ]
    assert result["schema_compile_mode"] == "batched"
    assert result["schema_compile_status"] == "frozen"
    assert result["chapters"][-1]["required_event_ids"] == ["event-33"]
    assert valid_v5_plan(result, snapshot)


def test_plan_hash_binds_schema_compile_invocation_evidence():
    plan = freeze_v5_plan(
        _base_plan(),
        _compile_payload(),
        _snapshot(),
        [{"invocation_id": 41, "response_hash": "compile-response"}],
    )
    plan["schema_compile_attempts"][0]["invocation_id"] = 42

    assert not valid_v5_plan(plan)


def test_v5_plan_rejects_cross_story_source_even_when_outline_matches():
    plan = freeze_v5_plan(_base_plan(), _compile_payload(), _snapshot(), [])
    other_story = {**_snapshot(), "business_id": "story-2"}

    assert valid_v5_plan(plan, _snapshot())
    assert not valid_v5_plan(plan, other_story)


def _base_plan():
    return {
        "schema": "story_novel_generation_plan.v5",
        "version": 4,
        "status": "ready",
        "phase": "spec_ready",
        "story_seed_version": 2,
        "outline_hash": "outline-hash",
        "model": "deepseek:prose",
        "model_policy": {
            "planning_model": "deepseek:plan",
            "prose_model": "deepseek:prose",
            "audit_model": "deepseek:audit",
        },
        "length_profile": {"profile_id": "test"},
        "chapter_length_overrides": {},
        "chapter_count": 1,
        "planned_min_chars": 100,
        "planned_target_chars": 120,
        "planned_max_chars": 150,
        "chapters": [
            {
                "position": 1,
                "title": "第一章",
                "goal": "改变关系",
                "key_events": ["A 改变选择"],
                "character_focus": ["A"],
                "open_threads": [],
                "end_state": "选择已改变",
                "min_chars": 100,
                "target_chars": 120,
                "max_chars": 150,
                "length_source": "profile_default",
            }
        ],
    }


def _snapshot():
    return {
        "business_id": "story-1",
        "title": "测试故事",
        "story_seed_version": 2,
        "story_seed": {
            "schema": "story_seed_v2",
            "structured_outline": {"chapters": [{"position": 1}]},
        },
        "characters": [],
    }


def _compile_payload():
    return {
        "consistency_schema": {
            "schema": "story_novel_consistency_schema.v1",
            "version": 1,
            "entity_types": [
                {"id": "agent", "label": "Agent", "capabilities": []},
                {"id": "choice", "label": "Choice", "capabilities": []},
            ],
            "predicates": [
                {
                    "id": "selects",
                    "label": "selects",
                    "subject_type_ids": ["agent"],
                    "value_kind": "entity_ref",
                    "value_entity_type_ids": ["choice"],
                    "cardinality": "one",
                    "mutability": "replaceable",
                    "persistence": "causal",
                }
            ],
            "event_types": [
                {
                    "id": "changes",
                    "label": "changes",
                    "roles": {"actor": ["agent"], "target": ["choice"]},
                }
            ],
            "constraints": [],
            "perspectives": [],
            "source_manifest": {},
        },
        "initial_fact_graph": {
            "schema": "story_novel_fact_graph.v1",
            "entities": [
                {"id": "a", "type_id": "agent", "name": "A"},
                {"id": "old", "type_id": "choice", "name": "Old"},
                {"id": "new", "type_id": "choice", "name": "New"},
            ],
            "facts": [
                {
                    "id": "fact-1",
                    "subject_id": "a",
                    "predicate_id": "selects",
                    "value": "old",
                }
            ],
            "evidence": [],
            "occurred_event_ids": [],
        },
        "causal_event_graph": {
            "schema": "story_novel_causal_event_graph.v1",
            "events": [
                {
                    "id": "event-1",
                    "event_type_id": "changes",
                    "chapter_position": 1,
                    "role_bindings": {"actor": ["a"], "target": ["new"]},
                    "effects": [
                        {
                            "op": "replace",
                            "subject": {"role": "actor"},
                            "predicate_id": "selects",
                            "value": {"role": "target"},
                        }
                    ],
                    "obligation_ids": ["obligation-1"],
                }
            ],
            "obligations": [
                {
                    "id": "obligation-1",
                    "kind": "hook",
                    "chapter_position": 1,
                    "required_event_ids": ["event-1"],
                }
            ],
        },
    }


def _causal_batch(start, end):
    events = []
    obligations = []
    for position in range(start, end + 1):
        event_id = f"event-{position}"
        obligation_id = f"obligation-{position}"
        events.append(
            {
                "id": event_id,
                "event_type_id": "changes",
                "chapter_position": position,
                "role_bindings": {"actor": ["a"], "target": ["new"]},
                "dependency_event_ids": (
                    [f"event-{position - 1}"] if position > 1 else []
                ),
                "effects": [
                    {
                        "op": "replace",
                        "subject": {"role": "actor"},
                        "predicate_id": "selects",
                        "value": {"role": "target"},
                    }
                ],
                "obligation_ids": [obligation_id],
            }
        )
        obligations.append(
            {
                "id": obligation_id,
                "kind": "hook",
                "chapter_position": position,
                "required_event_ids": [event_id],
            }
        )
    return {
        "causal_event_graph": {
            "schema": "story_novel_causal_event_graph.v1",
            "events": events,
            "obligations": obligations,
        }
    }
