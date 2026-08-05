"""Version-aware frozen generation-plan approval validation."""

from fastapi import HTTPException

from .story_novel_canon_service import (
    CANON_GATE_VERSION,
    content_hash,
    normalize_canon,
    validate_generation_plan,
)
from .story_novel_length_service import generation_plan_hash
from .story_novel_plan_versions import is_v5_plan
from .story_novel_v3_plan import valid_v3_plan_fields
from .story_novel_v5_plan import valid_v5_plan
from .story_novel_world_expansion import canon_with_plan_expansion


def require_current_frozen_plan(revision, plan: dict) -> None:
    snapshot = revision.story_snapshot or {}
    outline = (snapshot.get("story_seed") or {}).get("structured_outline") or {}
    if plan.get("status") != "ready":
        raise HTTPException(status_code=409, detail="生成计划尚未就绪")
    if int(plan.get("story_seed_version") or 0) != int(
        snapshot.get("story_seed_version") or 0
    ):
        raise HTTPException(status_code=409, detail="冻结 StorySeed 版本不匹配")
    if plan.get("outline_hash") != content_hash(outline):
        raise HTTPException(status_code=409, detail="冻结大纲 hash 已变化")
    if is_v5_plan(plan):
        _require_v5_report(revision, plan)
        return
    try:
        canon = normalize_canon(
            plan.get("canon") or {},
            required_gate_version=CANON_GATE_VERSION,
        )
        validate_generation_plan(
            canon_with_plan_expansion(canon, plan.get("chapters") or []),
            plan.get("chapters") or [],
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=409, detail=f"Canon/章节合同门禁无效: {exc}"
        ) from exc
    if (
        int(plan.get("canon_gate_version") or 0) != CANON_GATE_VERSION
        or not valid_v3_plan_fields(plan)
        or plan.get("canon_hash") != canon["canon_hash"]
        or plan.get("plan_hash") != generation_plan_hash(plan)
    ):
        raise HTTPException(status_code=409, detail="Canon 或生成计划 hash 不匹配")
    positions = [int(item.get("position") or 0) for item in plan.get("chapters") or []]
    if positions != list(range(1, len(positions) + 1)):
        raise HTTPException(status_code=409, detail="冻结章节计划不连续")
    _require_bound_report(revision, plan, "连续性报告未绑定当前生成计划")


def _require_v5_report(revision, plan):
    if not valid_v5_plan(plan, revision.story_snapshot or {}):
        raise HTTPException(status_code=409, detail="V5 Schema/事实图/因果图 hash 无效")
    _require_bound_report(revision, plan, "V5 质量报告未绑定当前生成计划")


def _require_bound_report(revision, plan, detail):
    report = revision.continuity_report or {}
    if (
        report.get("status") == "stale"
        or report.get("plan_version") != plan.get("version")
        or report.get("plan_hash") != plan.get("plan_hash")
    ):
        raise HTTPException(status_code=409, detail=detail)
