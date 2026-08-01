"""One bounded local repair and re-audit for a v3 chapter body."""

import copy

from .story_novel_context_utils import value_hash
from .story_novel_domain import sha256_text
from .story_novel_v3_audit_budget import audit_contract_hash
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
    frozen_plan=None,
    before_call=None,
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
        before_call=before_call,
    )
    original = _stage_repair_candidate(
        entry, repaired_prose, prose_input, expected_delta
    )
    try:
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
                f"{audit_contract_hash(entry['body_hash'], expected_delta, entry)}"
                ".local_repair"
            ),
            audit_call_budget=remaining,
            reserve_call=reserve_call,
            frozen_plan=frozen_plan,
            before_call=before_call,
        )
    finally:
        _restore_checkpoint_chain(entry, original)
    selected = select_failed_result(first, repaired)
    metrics = merge_stage_metrics(first["audit_metrics"], repaired["audit_metrics"])
    return selected, {"audit": metrics, "local_repair": repair_metrics}, 1


_REPAIR_CHAIN_KEYS = (
    "body_hash",
    "audit_contract_hash",
    "char_count",
    "blocks",
    "prose_context_hash",
    "expected_delta",
    "body_repair_count",
)


def _stage_repair_candidate(entry, prose, prose_input, expected_delta):
    original = {key: copy.deepcopy(entry.get(key)) for key in _REPAIR_CHAIN_KEYS}
    body_hash = sha256_text(prose["content_text"].strip())
    entry.update(
        body_hash=body_hash,
        audit_contract_hash=audit_contract_hash(body_hash, expected_delta, entry),
        char_count=prose.get("char_count"),
        blocks=copy.deepcopy(prose.get("blocks") or []),
        prose_context_hash=value_hash(prose_input),
        expected_delta=copy.deepcopy(expected_delta),
        body_repair_count=1,
    )
    return original


def _restore_checkpoint_chain(entry, original):
    for key, value in original.items():
        if value is None:
            entry.pop(key, None)
        else:
            entry[key] = value
