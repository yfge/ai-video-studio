"""Validate v3 stage metrics, audit reservations, and model bindings."""

from .story_novel_v3_audit_budget import (
    MAX_AUDIT_ATTEMPTS_PER_BODY,
    audit_contract_hash,
    audit_stage,
    persisted_audit_attempts,
)
from .story_novel_v3_audit_checkpoint import reservation_metrics


def valid_stage_metrics(db, revision, position: int, entry: dict) -> bool:
    policy = (revision.generation_plan or {}).get("model_policy") or {}
    required = {
        "chapter_planning": policy.get("planning_model"),
        "prose": policy.get("prose_model"),
        "audit": policy.get("audit_model"),
    }
    if int(entry.get("body_repair_count") or 0) > 0:
        required["local_repair"] = policy.get("prose_model")
    metrics = entry.get("stage_metrics") or {}
    expected_hash = audit_contract_hash(
        str(entry.get("body_hash") or ""), entry.get("expected_delta") or {}, entry
    )
    budget_hash = str(entry.get("audit_budget_hash") or "")
    reservations = list(entry.get("audit_reservations") or [])
    audit_attempts = (metrics.get("audit") or {}).get("attempts") or []
    recovered = reservation_metrics(db, revision.business_id, entry)
    successful = [item for item in reservations if item.get("status") == "succeeded"]
    expected_scenes = [
        f"story_novel.{revision.business_id}.{item.get('stage')}" for item in successful
    ]
    if (
        entry.get("audit_contract_hash") != expected_hash
        or not budget_hash
        or not reservations
        or len(reservations) > MAX_AUDIT_ATTEMPTS_PER_BODY
        or not recovered["complete"]
        or recovered["reservations"] != reservations
        or len(audit_attempts) != len(successful)
        or [item.get("call_scene") for item in audit_attempts] != expected_scenes
        or [item.get("invocation_id") for item in audit_attempts]
        != [item.get("accepted_invocation_id") for item in successful]
        or not any(
            f".body.{expected_hash}." in str(item.get("call_scene") or "")
            for item in audit_attempts
        )
        or persisted_audit_attempts(db, revision.business_id, position, budget_hash)
        != len(reservations)
        or any(item.get("budget_hash") != budget_hash for item in reservations)
        or any(
            not str(item.get("stage") or "").startswith(
                f"{audit_stage(position, budget_hash)}."
            )
            for item in reservations
        )
    ):
        return False
    return all(
        _valid_metric(metrics.get(stage) or {}, expected_model)
        for stage, expected_model in required.items()
    )


def _valid_metric(metric: dict, expected_model: str | None) -> bool:
    attempts = metric.get("attempts") or []
    return bool(
        int(metric.get("calls") or 0) == len(attempts)
        and attempts
        and (metric.get("invocation_ids") or [])
        == [item.get("invocation_id") for item in attempts]
        and all(
            valid_invocation(item, expected_model, require_prompt_template=True)
            for item in attempts
        )
    )


def valid_invocation(
    attempt: dict, expected_model: str | None, *, require_prompt_template: bool = False
) -> bool:
    actual_model = f"{attempt.get('provider')}:{attempt.get('model')}"
    model_matches = (
        actual_model == expected_model
        if expected_model and ":" in expected_model
        else attempt.get("model") == expected_model
    )
    template = attempt.get("prompt_template") or {}
    system_template = template.get("system_prompt") or {}
    return bool(
        attempt.get("status") == "succeeded"
        and attempt.get("invocation_id")
        and attempt.get("response_hash")
        and attempt.get("raw_response_hash")
        and model_matches
        and "finish_reason" in attempt
        and (
            not require_prompt_template
            or bool(
                template.get("template")
                and template.get("version")
                and template.get("sources_hash")
                and template.get("rendered_hash")
                and system_template.get("template") == "story_novel_system_v3"
                and system_template.get("version")
                and system_template.get("sources_hash")
                and system_template.get("rendered_hash")
            )
        )
    )
