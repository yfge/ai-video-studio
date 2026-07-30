"""One bounded local repair and re-audit for a v3 chapter body."""

from .story_novel_domain import sha256_text
from .story_novel_v3_audit_budget import audit_contract_hash
from .story_novel_v3_checkpoint import checkpoint_prose
from .story_novel_v3_evaluation import evaluate_body
from .story_novel_v3_gate import select_failed_result
from .story_novel_v3_generation import merge_stage_metrics, repair_blocks
from .story_novel_v3_runtime import update_progress


async def repair_failed_body(
    service,
    revision,
    task,
    chapter_plan,
    brief,
    context,
    prose_input,
    expected_delta,
    first,
    generate_text,
    *,
    audit_stage,
    audit_call_budget,
    reserve_call,
    entry,
    allow_repair=True,
):
    audit = first["audit"]
    if (
        audit["passed"]
        or not allow_repair
        or audit.get("failure_kind") == "evidence_only"
        or not audit.get("repairable")
    ):
        return first, {"audit": first["audit_metrics"]}, 0
    remaining = audit_call_budget - int(first["audit_metrics"].get("calls") or 0)
    if remaining <= 0:
        return first, {"audit": first["audit_metrics"]}, 0
    position = int(chapter_plan["position"])
    update_progress(service, task, position, revision, "local_repair")
    repaired_prose, repair_metrics = await repair_blocks(
        revision,
        position,
        blocks=first["prose"]["block_contents"],
        failed_block_ids=audit["failed_block_ids"],
        violations=audit["repair_issues"],
        prose_input=prose_input,
        generate_text=generate_text,
        expected_delta=expected_delta,
    )
    original_budget_hash = entry.get("audit_budget_hash")
    _chapter, entry = checkpoint_prose(
        service,
        revision,
        position,
        chapter_plan,
        entry,
        brief,
        prose_input,
        expected_delta,
        repaired_prose,
        repair_metrics,
        metric_stage="local_repair",
        repair_count=1,
        repair_resume={
            "budget_hash": original_budget_hash,
            "audit_metrics": first["audit_metrics"],
        },
    )
    repaired = await evaluate_body(
        service,
        revision,
        task,
        chapter_plan,
        brief,
        context,
        repaired_prose,
        expected_delta,
        generate_text,
        allow_evidence_retry=True,
        audit_stage=(
            f"{audit_stage}.body."
            f"{audit_contract_hash(sha256_text(repaired_prose['content_text']), expected_delta, entry)}"
            ".local_repair"
        ),
        audit_call_budget=remaining,
        reserve_call=reserve_call,
    )
    selected = select_failed_result(first, repaired)
    metrics = merge_stage_metrics(first["audit_metrics"], repaired["audit_metrics"])
    return selected, {"audit": metrics, "local_repair": repair_metrics}, 1
