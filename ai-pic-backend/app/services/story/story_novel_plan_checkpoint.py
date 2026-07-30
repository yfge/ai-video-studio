"""Validated planning checkpoints for outline-driven novel generation."""

from pydantic import ValidationError

from .story_novel_canon_milestone_filter import CANON_MODEL_FILTER_VERSION
from .story_novel_canon_service import (
    CANON_GATE_VERSION,
    normalize_canon,
    validate_generation_plan,
)
from .story_novel_incremental_plan import is_incremental_plan
from .story_novel_length_service import generation_plan_hash
from .story_novel_memory_context import (
    invalidate_revision_candidates,
    mark_revision_ledger_stale,
)
from .story_novel_plan_versions import is_state_gated_plan
from .story_novel_v3_plan import valid_v3_plan_fields


def frozen_generation_spec(current: dict) -> dict | None:
    if (
        int(current.get("version") or 0) >= 4
        and current.get("outline_hash")
        and current.get("chapters")
    ):
        return current
    return None


def validated_canon_checkpoint(current: dict) -> dict | None:
    canon = current.get("canon")
    if (
        not isinstance(canon, dict)
        or int(current.get("canon_gate_version") or 0) != CANON_GATE_VERSION
        or int(canon.get("gate_version") or 0) != CANON_GATE_VERSION
    ):
        return None
    try:
        normalized = normalize_canon(canon, required_gate_version=CANON_GATE_VERSION)
    except (TypeError, ValueError, ValidationError):
        return None
    expected = normalized["canon_hash"]
    if canon.get("canon_hash") != expected or current.get("canon_hash") != expected:
        return None
    return normalized


def reusable_generation_plan(current: dict, frozen_spec: dict | None) -> bool:
    if (
        is_state_gated_plan(current)
        and int(current.get("canon_model_filter_version") or 0)
        < CANON_MODEL_FILTER_VERSION
    ):
        return False
    ready = (
        current.get("status") == "ready"
        and current.get("phase") == "ready"
        and current.get("canon")
        and current.get("chapters")
    )
    if ready:
        if not frozen_spec and not is_state_gated_plan(current):
            return True
        canon = validated_canon_checkpoint(current)
        if (
            not canon
            or not valid_v3_plan_fields(current)
            or current.get("plan_hash") != generation_plan_hash(current)
        ):
            return False
        if is_incremental_plan(current):
            return True
        try:
            validate_generation_plan(canon, current["chapters"])
        except (TypeError, ValueError):
            return False
        return True
    return bool(
        current.get("status") == "ready"
        and current.get("chapters")
        and not frozen_spec
        and not is_state_gated_plan(current)
    )


def begin_planning(service, revision, task, current: dict, frozen_spec) -> bool:
    ledger = dict(revision.continuity_ledger or {})
    if ledger.get("chapters") or ledger.get("current_state"):
        invalidate_revision_candidates(service.db, revision)
        mark_revision_ledger_stale(revision, from_position=1)
        service._invalidate_from(revision, 1)
    error = str(current.get("error") or "")
    requires_canon_recompile = current.get("status") == "failed" and any(
        marker in error for marker in ("地点引用无效", "状态提前包含未来里程碑结果")
    )
    requires_canon_recompile |= current.get("phase") in {
        "chapters",
        "ready",
    } and int(
        current.get("canon_model_filter_version") or 0
    ) < (CANON_MODEL_FILTER_VERSION)
    ready_replan = bool(
        current.get("status") == "ready" and current.get("phase") == "ready"
    )
    resume = bool(
        validated_canon_checkpoint(current)
        and not requires_canon_recompile
        and (current.get("phase") == "chapters" or ready_replan)
    )
    if resume:
        revision.generation_plan = {
            **current,
            "version": int(current.get("version") or 0) + int(ready_replan),
            "status": "planning",
            "phase": "chapters",
            "error": None,
        }
        task.description = "Canon 已验证，正在重新规划章节合同…"
        service.db.commit()
        return True
    task.description = "正在根据 StorySeed 大纲规划章节…"
    revision.generation_plan = (
        {
            **{
                key: value
                for key, value in current.items()
                if key
                not in {
                    "canon",
                    "canon_hash",
                    "canon_gate_version",
                    "canon_model_filter_version",
                    "error",
                    "plan_hash",
                    "planning_invocations",
                    "planning_invocations_hash",
                }
            },
            "version": int(current.get("version") or 0) + int(ready_replan),
            "status": "planning",
            "phase": "canon",
        }
        if frozen_spec
        else {
            "schema": "story_novel_generation_plan.v2",
            "version": int(current.get("version") or 0) + 1,
            "status": "planning",
            "phase": "canon",
            "chapters": [],
        }
    )
    service.db.commit()
    return False
