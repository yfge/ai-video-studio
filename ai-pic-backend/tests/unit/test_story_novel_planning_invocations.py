import copy
from types import SimpleNamespace

from app.services.story.story_novel_invocation_evidence import GeneratedNovelText
from app.services.story.story_novel_planning_invocations import (
    record_plan_batch_sources,
    valid,
)
from app.services.story.story_novel_planning_phases import complete_plan
from app.services.story.story_novel_prompt_renderer import v3_prompt_template_policy
from tests.unit.story_novel_v3_test_support import freeze_planning_invocations
from tests.unit.test_story_novel_v3_pipeline import _canon, _row


def _revision():
    canon, row = _canon(), _row()
    revision = SimpleNamespace(
        generation_plan={
            "schema": "story_novel_generation_plan.v3",
            "model_policy": {
                "planning_model": "deepseek:planning",
                "prose_model": "deepseek:prose",
                "audit_model": "deepseek:audit",
            },
            "prompt_templates": v3_prompt_template_policy(),
            "canon": canon,
            "canon_hash": canon["canon_hash"],
            "chapters": [row],
        }
    )
    freeze_planning_invocations(revision, canon, [row])
    return revision


def test_planning_manifest_survives_chapter_runtime_mirrors():
    revision = _revision()

    revision.generation_plan["chapters"][0].update(
        actual_chars=2400,
        generation_status="ready",
        body_hash="body",
        context_hash="context",
    )

    assert valid(revision.generation_plan)


def test_planning_manifest_rejects_missing_prompt_fingerprint():
    revision = _revision()

    revision.generation_plan["planning_invocations"]["entries"][0]["attempt"].pop(
        "prompt_template"
    )

    assert not valid(revision.generation_plan)


def test_plan_patch_provenance_keeps_initial_and_repair_attempts():
    revision = _revision()
    row = _row()
    initial = GeneratedNovelText("initial", {"invocation_id": 91})
    repair = GeneratedNovelText("repair", {"invocation_id": 92})

    record_plan_batch_sources(revision, initial, repair, [1], [row])

    entries = revision.generation_plan["planning_invocations"]["entries"]
    sources = [
        item for item in entries if item["logical_stage"].startswith("chapter_plan")
    ][-2:]
    assert [item["logical_stage"] for item in sources] == [
        "chapter_plan.batch.1-1.initial",
        "chapter_plan.batch.1-1.repair",
    ]
    assert sources[0]["result_hash"] == sources[1]["result_hash"]


def test_complete_plan_preserves_the_recorded_planning_manifest():
    revision = _revision()
    revision.chapter_count = 0
    revision.target_words = 0
    canon, row = _canon(), _row()
    task = SimpleNamespace(status="pending", description="")
    service = SimpleNamespace(db=SimpleNamespace(commit=lambda: None))

    plan = complete_plan(
        service,
        revision,
        task,
        dict(revision.generation_plan),
        canon,
        [row],
    )

    assert valid(plan)
    assert [
        item["logical_stage"] for item in plan["planning_invocations"]["entries"]
    ] == ["canon", "chapter_plan.batch.1-1"]


def test_manifest_rejects_reused_invocation_prompt_drift_and_result_hash():
    revision = _revision()
    base = revision.generation_plan
    for mutation in (
        lambda plan: plan["planning_invocations"]["entries"][1]["attempt"].update(
            invocation_id=80
        ),
        lambda plan: plan["planning_invocations"]["entries"][1]["attempt"][
            "prompt_template"
        ].update(template="story_novel_proof_audit_v3"),
        lambda plan: plan["planning_invocations"]["entries"][1]["attempt"][
            "prompt_template"
        ].update(version="old-version"),
        lambda plan: plan["planning_invocations"]["entries"][1]["attempt"][
            "prompt_template"
        ]["system_prompt"].update(sources_hash="old-system-source"),
        lambda plan: plan["planning_invocations"]["entries"][1].update(
            result_hash="tampered"
        ),
    ):
        tampered = copy.deepcopy(base)
        mutation(tampered)
        assert not valid(tampered)


def test_manifest_rejects_unpaired_repair_source():
    revision = _revision()
    entries = revision.generation_plan["planning_invocations"]["entries"]
    entries[1]["logical_stage"] = "chapter_plan.batch.1-1.repair"
    entries[1]["attempt"]["prompt_template"][
        "template"
    ] = "story_novel_plan_patch_repair_v3"

    assert not valid(revision.generation_plan)
