"""Repair calls and metrics for bounded V5 consistency batches."""

from .story_novel_v5_batched_contracts import parse_causal_batch, parse_foundation
from .story_novel_v5_output_contracts import (
    causal_batch_output_schema,
    foundation_output_schema,
)
from .story_novel_v5_prompts import causal_batch_repair_prompt, foundation_repair_prompt


async def repair_foundation(
    revision, generate_text, contract, previous, diagnostics, attempts, base
):
    text = await generate_text(
        revision,
        foundation_repair_prompt(contract, previous, diagnostics),
        stage="consistency_schema.foundation_repair",
        max_tokens=20_000,
        temperature=0.1,
        json_schema=foundation_output_schema(),
    )
    attempts.append(attempt(text))
    foundation, refreshed = parse_foundation(base, revision, text)
    diagnostics[:] = refreshed
    return foundation


async def repair_batch(
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
):
    start, end = rows[0]["position"], rows[-1]["position"]
    text = await generate_text(
        revision,
        causal_batch_repair_prompt(contract, previous, diagnostics),
        stage=f"consistency_schema.causal.{start}-{end}.repair",
        max_tokens=batch_tokens(rows),
        temperature=0.1,
        json_schema=causal_batch_output_schema(),
    )
    attempts.append(attempt(text))
    merged, refreshed = parse_causal_batch(text, partial, schema, initial, rows)
    diagnostics[:] = refreshed
    return merged


def batch_tokens(rows):
    return max(8_000, min(20_000, len(rows) * 900))


def attempt(text):
    return dict(getattr(text, "invocation_evidence", {}) or {})
