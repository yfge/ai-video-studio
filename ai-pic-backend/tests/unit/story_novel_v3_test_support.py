"""Small helpers for unit fixtures that exercise the v3 downstream boundary."""

import hashlib

from app.models.llm_invocation import LLMInvocation
from app.services.story import story_novel_planning_invocations
from app.services.story.story_novel_context_utils import (
    prompt_chapter_contract,
    value_hash,
)
from app.services.story.story_novel_invocation_evidence import (
    GeneratedNovelText,
    invocation_row_evidence,
)
from app.services.story.story_novel_length_service import generation_plan_hash
from app.services.story.story_novel_plan_state_compiler import compile_plan_state
from app.services.story.story_novel_plan_versions import V3_SCHEMA
from app.services.story.story_novel_v3_plan import v3_plan_fields


def prompt_template_evidence(template: str) -> dict:
    return {
        "template": template,
        "resolved_template": template,
        "version": "test",
        "sources_hash": "source-hash",
        "rendered_hash": "rendered-hash",
        "system_prompt": {
            "template": "story_novel_system_v3",
            "resolved_template": "story_novel_system_v3",
            "version": "test",
            "sources_hash": "system-source-hash",
            "rendered_hash": "system-rendered-hash",
        },
    }


def persisted_stage_text(
    db,
    revision,
    stage: str,
    text: str,
    invocation_id: int,
    *,
    rendered_template: dict | None = None,
    prompt_text: str = "prompt",
):
    if stage.startswith("chapter_planning"):
        model = "planning"
    elif stage.startswith(("prose", "local_repair")):
        model = "prose"
    else:
        model = "audit"
    template = dict(
        rendered_template
        or prompt_template_evidence(f"story_novel_{stage.split('.', 1)[0]}_v3")
    )
    template.setdefault(
        "system_prompt",
        prompt_template_evidence("story_novel_system_v3")["system_prompt"],
    )
    row = LLMInvocation(
        id=invocation_id,
        invocation_type="text",
        call_scene=f"story_novel.{revision.business_id}.{stage}",
        provider="deepseek",
        model=model,
        attempt_index=1,
        status="succeeded",
        original_prompt=prompt_text,
        prompt=prompt_text,
        response=text,
        input_tokens=100,
        cache_tokens=0,
        output_tokens=200,
        latency_ms=10,
        response_metadata={
            "finish_reason": "stop",
            "product_status": "accepted",
            "prompt_template": template,
        },
        input_references=[
            {
                "type": "prompt_template",
                "value": template,
            }
        ],
    )
    db.add(row)
    db.commit()
    return GeneratedNovelText(text, invocation_row_evidence(row))


def freeze_planning_invocations(
    revision, canon: dict, chapters: list[dict], *, db=None, first_id: int = 80
) -> None:
    positions = [int(item["position"]) for item in chapters]
    stages = [("canon", [], "story_novel_canon_v3")]
    stages.append(
        (
            f"chapter_plan.batch.{positions[0]}-{positions[-1]}",
            positions,
            "story_novel_plan_v3",
        )
    )
    plan = dict(revision.generation_plan or {})
    if plan.get("plan_semantic_audit_version"):
        stages.append(
            (
                f"semantic_audit.batch.{positions[0]}-{positions[-1]}",
                positions,
                "story_novel_plan_semantic_audit_v3",
            )
        )
    revision.generation_plan = plan
    for offset, (stage, covered, template) in enumerate(stages):
        text = f"planning:{stage}"
        invocation_id = first_id + offset
        evidence = _planning_evidence(revision, invocation_id, text, template, db=db)
        story_novel_planning_invocations.record(
            revision,
            stage,
            GeneratedNovelText(text, evidence),
            positions=covered,
            result_hash=(
                canon["canon_hash"]
                if stage == "canon"
                else value_hash(
                    [
                        prompt_chapter_contract(item)
                        for item in chapters
                        if int(item["position"]) in set(covered)
                    ]
                )
            ),
        )
    plan = dict(revision.generation_plan or {})
    story_novel_planning_invocations.finalize(plan, canon, chapters)
    revision.generation_plan = plan


def _planning_evidence(revision, invocation_id, text, template, *, db=None) -> dict:
    policy = (revision.generation_plan or {}).get("model_policy") or {}
    provider, model = str(policy.get("planning_model") or "deepseek:planning").split(
        ":", 1
    )
    frozen = (revision.generation_plan or {})["prompt_templates"]["templates"]
    prompt_template = {
        **frozen[template],
        "rendered_hash": "rendered-hash",
        "system_prompt": {
            **frozen["story_novel_system_v3"],
            "rendered_hash": "system-rendered-hash",
        },
    }
    if db is None:
        digest = hashlib.sha256(text.encode()).hexdigest()
        return {
            "invocation_id": invocation_id,
            "provider": provider,
            "model": model,
            "status": "succeeded",
            "input_tokens": 100,
            "cache_tokens": 0,
            "output_tokens": 200,
            "finish_reason": "stop",
            "latency_ms": 10,
            "response_hash": digest,
            "raw_response_hash": digest,
            "prompt_template": prompt_template,
        }
    row = LLMInvocation(
        id=invocation_id,
        invocation_type="text",
        call_scene=f"story_novel.{revision.business_id}.planning",
        provider=provider,
        model=model,
        attempt_index=1,
        status="succeeded",
        original_prompt="prompt",
        prompt="prompt",
        response=text,
        input_tokens=100,
        cache_tokens=0,
        output_tokens=200,
        latency_ms=10,
        response_metadata={
            "finish_reason": "stop",
            "product_status": "accepted",
            "prompt_template": prompt_template,
        },
        input_references=[{"type": "prompt_template", "value": prompt_template}],
    )
    db.add(row)
    db.flush()
    return invocation_row_evidence(row)


def mark_v3_downstream_ready(revision) -> None:
    plan = dict(revision.generation_plan or {})
    chapters = []
    for source in plan.get("chapters") or []:
        row = dict(source)
        key_events = list(row.get("key_events") or [])
        row["required_event_ids"] = [
            f"event-{row['position']}-{index}"
            for index in range(1, len(key_events) + 1)
        ]
        chapters.append(row)
    canon = dict(plan.get("canon") or {})
    canon.setdefault("canon_hash", plan.get("canon_hash") or value_hash(canon))
    chapters = compile_plan_state(canon, chapters)
    for row in chapters:
        bindings = row.get("timeline_event_bindings") or {}
        grants = row.get("knowledge_grants") or []
        row["execution_contracts"] = [
            {
                "event_id": event_id,
                "action_phase": "instant",
                "time_scope": "unspecified",
                "actor_ids": [],
                "effort": "unspecified",
                "timeline_ids": [
                    key for key, value in bindings.items() if value == event_id
                ],
                "knowledge_fact_ids": [
                    item["fact_id"]
                    for item in grants
                    if item.get("source_event_id") == event_id
                ],
            }
            for event_id in row["required_event_ids"]
        ]
    plan.update(
        {
            "schema": V3_SCHEMA,
            "status": "ready",
            "canon": canon,
            "canon_hash": canon["canon_hash"],
            "chapters": chapters,
            "model_policy": {
                "planning_model": revision.model or "deepseek:deepseek-chat",
                "prose_model": revision.model or "deepseek:deepseek-chat",
                "audit_model": revision.model or "deepseek:deepseek-chat",
            },
        }
    )
    plan.update(v3_plan_fields(V3_SCHEMA, canon, chapters))
    revision.generation_plan = plan
    freeze_planning_invocations(revision, canon, chapters)
    plan = dict(revision.generation_plan or {})
    plan["plan_hash"] = generation_plan_hash(plan)
    revision.generation_plan = plan
    report = dict(revision.continuity_report or {})
    report.update({"plan_version": plan["version"], "plan_hash": plan["plan_hash"]})
    revision.continuity_report = report
