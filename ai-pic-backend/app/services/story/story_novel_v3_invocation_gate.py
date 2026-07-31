"""Validate v3 ledger invocation evidence against persisted provider calls."""

from __future__ import annotations

import hashlib

from app.repositories.llm_invocation_repository import LLMInvocationRepository
from app.utils.json_utils import extract_json_block

from .story_novel_context_utils import value_hash
from .story_novel_finish_reason import is_recoverable_length_finish_reason
from .story_novel_invocation_evidence import (
    invocation_input_prompt_template,
    invocation_prompt_template,
)
from .story_novel_planning_invocations import valid as valid_planning_invocations


def persisted_invocation_issues(db, revision, entries: dict, report: dict) -> list[str]:
    policy = (revision.generation_plan or {}).get("model_policy") or {}
    specs = []
    issues = []
    repo = LLMInvocationRepository(db)
    plan = revision.generation_plan or {}
    require_prebound = (plan.get("prompt_templates") or {}).get("schema") in {
        "story_novel_prompt_policy.v2",
        "story_novel_prompt_policy.v3",
        "story_novel_prompt_policy.v4",
        "story_novel_prompt_policy.v5",
        "story_novel_prompt_policy.v6",
        "story_novel_prompt_policy.v7",
        "story_novel_prompt_policy.v8",
        "story_novel_prompt_policy.v9",
    }
    if not valid_planning_invocations(plan):
        issues.append("planning_manifest")
    for entry in (plan.get("planning_invocations") or {}).get("entries") or []:
        specs.append(
            ("planning", policy.get("planning_model"), entry.get("attempt") or {})
        )
    for position, entry in sorted(entries.items(), key=lambda item: int(item[0])):
        stages = (
            ("chapter_planning", f"chapter_planning.{position}", "planning_model"),
            ("prose", f"prose.{position}", "prose_model"),
            ("audit", f"audit.{position}", "audit_model"),
            ("local_repair", f"local_repair.{position}", "prose_model"),
        )
        metrics = entry.get("stage_metrics") or {}
        applied_repairs = _applied_repair_ids(
            repo, revision.business_id, position, entry
        )
        recorded_repairs = set(
            (metrics.get("local_repair") or {}).get("invocation_ids") or []
        )
        if applied_repairs and (
            int(entry.get("body_repair_count") or 0) < 1
            or not applied_repairs.intersection(recorded_repairs)
        ):
            issues.append(f"local_repair:{position}")
        for stage, scene, model_key in stages:
            if stage in metrics:
                specs.extend(
                    (scene, policy.get(model_key), attempt)
                    for attempt in (metrics[stage].get("attempts") or [])
                )
    reviews = list(report.get("review_invocations") or [])
    reviewer_model = report.get("reviewer_model") or policy.get("audit_model")
    for index, attempt in enumerate(reviews, start=1):
        scene = (
            "continuity.global"
            if index == len(reviews)
            else f"continuity.window.{index}"
        )
        specs.append((scene, reviewer_model, attempt))
    return issues + [
        f"invocation:{attempt.get('invocation_id')}"
        for scene, model, attempt in specs
        if not _matches(
            repo,
            revision.business_id,
            scene,
            model,
            attempt,
            require_prebound=require_prebound,
        )
    ]


def _applied_repair_ids(repo, revision_id: str, position: str, entry: dict) -> set[int]:
    prefix = f"story_novel.{revision_id}.local_repair.{position}"
    blocks = {
        item.get("block_id"): item.get("content_hash")
        for item in entry.get("blocks") or []
    }
    applied = set()
    for row in repo.list_by_call_scene_prefix(prefix):
        metadata = dict(row.response_metadata or {})
        payload = extract_json_block(str(row.response or "")) or {}
        replacements = payload.get("replacements") or []
        if (
            row.status == "succeeded"
            and metadata.get("product_status", "accepted") == "accepted"
            and any(
                blocks.get(item.get("block_id"))
                == value_hash(str(item.get("content_text") or ""))
                for item in replacements
                if isinstance(item, dict)
            )
        ):
            applied.add(int(row.id))
    return applied


def _matches(
    repo,
    revision_id: str,
    scene: str,
    expected_model,
    attempt: dict,
    *,
    require_prebound: bool,
) -> bool:
    try:
        row = repo.get_by_id(int(attempt.get("invocation_id")))
    except (TypeError, ValueError):
        return False
    if row is None:
        return False
    metadata = dict(row.response_metadata or {})
    raw_response = str(row.response or "")
    raw_response_hash = hashlib.sha256(raw_response.encode()).hexdigest()
    response_hash = hashlib.sha256(raw_response.strip().encode()).hexdigest()
    actual_model = f"{row.provider}:{row.model}"
    model_matches = (
        actual_model == expected_model
        if expected_model and ":" in expected_model
        else row.model == expected_model
    )
    expected_scene = f"story_novel.{revision_id}.{scene}"
    scene_matches = row.call_scene == expected_scene or row.call_scene.startswith(
        f"{expected_scene}."
    )
    prompt_template = invocation_prompt_template(row)
    response_template = metadata.get("prompt_template") or {}
    prebound_template = invocation_input_prompt_template(row)
    product_status = str(metadata.get("product_status") or "accepted")
    product_matches = product_status == "accepted" or bool(
        scene.startswith("prose.")
        and product_status == attempt.get("product_status") == "rejected"
        and is_recoverable_length_finish_reason(metadata.get("finish_reason"))
    )
    return bool(
        row.invocation_type == "text"
        and scene_matches
        and row.status == "succeeded"
        and row.provider == attempt.get("provider")
        and row.model == attempt.get("model")
        and model_matches
        and response_hash == attempt.get("response_hash")
        and attempt.get("raw_response_hash")
        and raw_response_hash == attempt.get("raw_response_hash")
        and product_matches
        and metadata.get("finish_reason")
        and metadata.get("finish_reason") == attempt.get("finish_reason")
        and int(row.input_tokens or 0) == int(attempt.get("input_tokens") or 0)
        and int(row.cache_tokens or 0) == int(attempt.get("cache_tokens") or 0)
        and int(row.output_tokens or 0) == int(attempt.get("output_tokens") or 0)
        and int(row.latency_ms or 0) == int(attempt.get("latency_ms") or 0)
        and prompt_template == attempt.get("prompt_template")
        and (
            not require_prebound
            or bool(
                prebound_template == attempt.get("prompt_template")
                and response_template == attempt.get("prompt_template")
            )
        )
    )
