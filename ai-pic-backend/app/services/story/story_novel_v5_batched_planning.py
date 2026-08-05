"""Bounded, resumable V5 consistency compilation for long outlines."""

from __future__ import annotations

import copy

from app.services.narrative_consistency import simulate_causal_graph
from app.utils.json_utils import extract_json_block

from .story_novel_v5_batched_calls import (
    attempt,
    batch_tokens,
    repair_batch,
    repair_foundation,
)
from .story_novel_v5_batched_checkpoint import (
    checkpoint_batched,
    checkpoint_foundation,
    raise_batched_failure,
    save_ready,
)
from .story_novel_v5_batched_contracts import (
    causal_contract,
    causal_ranges,
    foundation_contract,
    parse_causal_batch,
    parse_foundation,
)
from .story_novel_v5_output_contracts import (
    causal_batch_output_schema,
    foundation_output_schema,
)
from .story_novel_v5_plan import freeze_v5_foundation, freeze_v5_plan
from .story_novel_v5_prompts import (
    causal_batch_prompt,
    foundation_prompt,
    prompt_policy,
)


async def ensure_batched_v5_plan(service, revision, task, generate_text, current):
    current, attempts = await _ensure_foundation(
        service, revision, task, generate_text, current
    )
    foundation = {
        "consistency_schema": current["consistency_schema"],
        "initial_fact_graph": current["initial_fact_graph"],
    }
    schema, initial = freeze_v5_foundation(
        current, foundation, revision.story_snapshot or {}
    )
    partial = copy.deepcopy(
        current.get("causal_compile_partial_graph")
        or {
            "schema": "story_novel_causal_event_graph.v1",
            "events": [],
            "obligations": [],
        }
    )
    ranges = causal_ranges(current.get("chapters") or [])
    next_batch = int(current.get("causal_compile_next_batch") or 0)
    for index in range(next_batch, len(ranges)):
        rows = ranges[index]
        current, partial = await _compile_batch(
            service,
            revision,
            task,
            generate_text,
            current,
            attempts,
            schema,
            initial,
            partial,
            rows,
            index,
            len(ranges),
        )
    plan = freeze_v5_plan(
        {
            **current,
            "prompt_templates": prompt_policy(),
            "schema_compile_revision_business_id": revision.business_id,
        },
        {**foundation, "causal_event_graph": partial},
        revision.story_snapshot or {},
        attempts,
    )
    return save_ready(service, revision, task, plan)


async def _ensure_foundation(service, revision, task, generate_text, current):
    contract = foundation_contract(revision, current)
    attempts = list(current.get("schema_compile_attempts") or [])
    if current.get("schema_compile_status") == "foundation_repairing":
        previous = dict(current.get("schema_compile_candidate") or {})
        diagnostics = list(current.get("schema_compile_diagnostics") or [])
        foundation = await repair_foundation(
            revision, generate_text, contract, previous, diagnostics, attempts, current
        )
        if foundation is None:
            raise_batched_failure(
                service, revision, current, diagnostics, attempts, previous
            )
        return (
            checkpoint_foundation(service, revision, current, foundation, attempts),
            attempts,
        )
    if current.get("schema_compile_mode") == "batched":
        return current, attempts
    task.description = "正在编译长篇 Story 的一致性 Schema 与初始事实图…"
    text = await generate_text(
        revision,
        foundation_prompt(contract),
        stage="consistency_schema.foundation",
        max_tokens=20_000,
        json_schema=foundation_output_schema(),
    )
    attempts.append(attempt(text))
    foundation, diagnostics = parse_foundation(current, revision, text)
    if foundation is None:
        previous = extract_json_block(str(text)) or {}
        checkpoint_batched(
            service,
            revision,
            current,
            status="foundation_repairing",
            diagnostics=diagnostics,
            attempts=attempts,
            candidate=previous,
        )
        foundation = await repair_foundation(
            revision, generate_text, contract, previous, diagnostics, attempts, current
        )
        if foundation is None:
            raise_batched_failure(
                service, revision, current, diagnostics, attempts, previous
            )
    return (
        checkpoint_foundation(service, revision, current, foundation, attempts),
        attempts,
    )


async def _compile_batch(
    service,
    revision,
    task,
    generate_text,
    current,
    attempts,
    schema,
    initial,
    partial,
    rows,
    index,
    batch_count,
):
    start, end = rows[0]["position"], rows[-1]["position"]
    task.description = f"正在编译第 {start}–{end} 章因果骨架…"
    before = simulate_causal_graph(schema, initial, partial)["final_graph"]
    contract = causal_contract(
        current, rows, schema, before, partial, is_final=index == batch_count - 1
    )
    repairing = current.get(
        "schema_compile_status"
    ) == "causal_repairing" and current.get("causal_compile_active_range") == [
        start,
        end,
    ]
    if repairing:
        previous = dict(current.get("schema_compile_candidate") or {})
        diagnostics = list(current.get("schema_compile_diagnostics") or [])
        merged = await repair_batch(
            revision,
            generate_text,
            contract,
            previous,
            diagnostics,
            attempts,
            partial,
            schema,
            initial,
            rows,
        )
    else:
        text = await generate_text(
            revision,
            causal_batch_prompt(contract),
            stage=f"consistency_schema.causal.{start}-{end}",
            max_tokens=batch_tokens(rows),
            json_schema=causal_batch_output_schema(),
        )
        attempts.append(attempt(text))
        merged, diagnostics = parse_causal_batch(text, partial, schema, initial, rows)
        if merged is None:
            previous = extract_json_block(str(text)) or {}
            checkpoint_batched(
                service,
                revision,
                current,
                status="causal_repairing",
                diagnostics=diagnostics,
                attempts=attempts,
                candidate=previous,
                partial=partial,
                next_batch=index,
                active_range=[start, end],
            )
            merged = await repair_batch(
                revision,
                generate_text,
                contract,
                previous,
                diagnostics,
                attempts,
                partial,
                schema,
                initial,
                rows,
            )
    if merged is None:
        raise_batched_failure(
            service,
            revision,
            current,
            diagnostics,
            attempts,
            previous,
            partial=partial,
            next_batch=index,
            active_range=[start, end],
        )
    updated = checkpoint_batched(
        service,
        revision,
        current,
        status="causal_compiling",
        diagnostics=[],
        attempts=attempts,
        partial=merged,
        next_batch=index + 1,
        completed_range=[start, end],
    )
    return updated, merged
