"""Bind every accepted v5 artifact to its persisted provider invocation."""

from __future__ import annotations

import hashlib

from app.repositories.llm_invocation_repository import LLMInvocationRepository

from .story_novel_invocation_evidence import invocation_prompt_template
from .story_novel_finish_reason import is_recoverable_length_finish_reason
from .story_novel_context_utils import value_hash

_TEMPLATES_BY_STAGE = {
    "consistency_schema": {
        "story_novel_consistency_compile_v5",
        "story_novel_consistency_repair_v5",
    },
    "scene_planning": {"story_novel_scene_plan_v5", "story_novel_json_repair_v5"},
    "prose": {"story_novel_prose_v5", "story_novel_prose_continuation_v5"},
    "claim_extraction": {
        "story_novel_claim_extract_v5",
        "story_novel_json_repair_v5",
    },
    "readability": {"story_novel_readability_v5", "story_novel_json_repair_v5"},
    "span_repair": {"story_novel_span_repair_v5"},
    "full_rewrite": {
        "story_novel_full_rewrite_v5",
        "story_novel_prose_continuation_v5",
    },
}


def v5_invocation_issues(db, revision, entries: dict) -> list[dict]:
    plan = revision.generation_plan or {}
    issues = []
    repo = LLMInvocationRepository(db)
    compile_attempts = list(plan.get("schema_compile_attempts") or [])
    if not 1 <= len(compile_attempts) <= 2:
        issues.append({"position": 0, "issues": ["schema compile attempts"]})
    elif not _valid_attempts(
        repo,
        revision,
        compile_attempts,
        "consistency_schema",
        plan,
        source_business_id=plan.get("schema_compile_revision_business_id"),
    ):
        issues.append({"position": 0, "issues": ["schema invocation evidence"]})
    for position in range(1, int(revision.chapter_count or 0) + 1):
        entry = entries.get(str(position)) or {}
        entry_issues = _entry_issues(repo, revision, entry, plan)
        if entry_issues:
            issues.append({"position": position, "issues": entry_issues})
    return issues


def _entry_issues(repo, revision, entry, plan):
    metrics = entry.get("stage_metrics") or {}
    selected = _selected_candidate(entry)
    if selected is None:
        return ["selected candidate"]
    index = int(selected.get("attempt_index") or 0)
    kind = selected.get("attempt_kind")
    generator = {
        "initial": "prose",
        "span_repair": "span_repair",
        "full_rewrite": "full_rewrite",
    }.get(kind)
    required = [
        "scene_planning",
        f"{generator}.{index}" if generator else "",
        f"claim_extraction.{index}",
        f"readability.{index}",
    ]
    issues = []
    for key in required:
        metric = metrics.get(key) or {}
        stage = key.split(".", 1)[0]
        if not key or not _valid_metric(repo, revision, metric, stage, plan):
            issues.append(f"{key or 'generation'} invocation")
    if entry.get("model_call_manifest_hash") != _value_hash(metrics):
        issues.append("model call manifest hash")
    return issues


def _selected_candidate(entry):
    matches = [
        item
        for item in entry.get("candidate_attempts") or []
        if item.get("body_hash") == entry.get("body_hash")
        and item.get("consistency_report") == entry.get("consistency_report")
        and item.get("readability_report") == entry.get("readability_report")
    ]
    return matches[0] if len(matches) == 1 else None


def _valid_metric(repo, revision, metric, stage, plan):
    attempts = list(metric.get("attempts") or [])
    return bool(
        attempts
        and int(metric.get("calls") or 0) == len(attempts)
        and list(metric.get("invocation_ids") or [])
        == [item.get("invocation_id") for item in attempts]
        and _valid_attempts(repo, revision, attempts, stage, plan)
    )


def _valid_attempts(repo, revision, attempts, stage, plan, *, source_business_id=None):
    expected_model = _expected_model(plan, stage)
    revision_id = source_business_id or revision.business_id
    prefix = f"story_novel.{revision_id}.{stage}"
    for index, attempt in enumerate(attempts):
        try:
            row = repo.get_by_id(int(attempt.get("invocation_id")))
        except (TypeError, ValueError):
            return False
        response = str(getattr(row, "response", "") or "")
        template = invocation_prompt_template(row) if row else {}
        system = template.get("system_prompt") or {}
        if not (
            row
            and row.status == attempt.get("status") == "succeeded"
            and row.call_scene == attempt.get("call_scene")
            and str(row.call_scene or "").startswith(prefix)
            and row.provider == attempt.get("provider")
            and row.model == attempt.get("model")
            and _model_id(row.provider, row.model) == expected_model
            and hashlib.sha256(response.strip().encode()).hexdigest()
            == attempt.get("response_hash")
            and hashlib.sha256(response.encode()).hexdigest()
            == attempt.get("raw_response_hash")
            and _valid_product_status(attempt, attempts, index, stage)
            and template == attempt.get("prompt_template")
            and template.get("template") in _TEMPLATES_BY_STAGE[stage]
            and template.get("version")
            and template.get("sources_hash")
            and template.get("rendered_hash")
            and system.get("template") == "story_novel_system_v5"
            and system.get("version")
            and system.get("sources_hash")
            and system.get("rendered_hash")
        ):
            return False
    return True


def _expected_model(plan, stage):
    policy = plan.get("model_policy") or {}
    if stage in {"consistency_schema", "scene_planning"}:
        return policy.get("planning_model")
    if stage in {"claim_extraction", "readability"}:
        return policy.get("audit_model")
    return policy.get("prose_model")


def _model_id(provider, model):
    return f"{provider}:{model}" if provider else model


def _valid_product_status(attempt, attempts, index, stage):
    if attempt.get("product_status") == "accepted":
        return True
    return bool(
        stage in {"prose", "full_rewrite"}
        and index + 1 < len(attempts)
        and attempt.get("product_status") == "rejected"
        and is_recoverable_length_finish_reason(attempt.get("finish_reason"))
        and (
            (attempts[index + 1].get("prompt_template") or {}).get("template")
            == "story_novel_prose_continuation_v5"
        )
    )


def _value_hash(value):
    return value_hash(value)
