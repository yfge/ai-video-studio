"""Facade exports for production quality regression helpers."""

from __future__ import annotations

from scripts.harness.production_quality_aggregate import aggregate_quality_report
from scripts.harness.production_quality_gates import (
    evaluate_character_consistency,
    evaluate_provider_chain_sample,
    evaluate_render_structure,
    evaluate_timeline_order,
    extract_step_timings,
)
from scripts.harness.production_quality_io import (
    extract_clip_frames,
    load_provider_chain,
    make_contact_sheet,
    resolve_provider_chain_path,
    write_quality_outputs,
)
from scripts.harness.production_quality_script import (
    extract_script_payload,
    lint_script,
    normalize_script_score,
    provider_chain_script_text,
    structured_script_score,
)

__all__ = [
    "aggregate_quality_report",
    "evaluate_character_consistency",
    "evaluate_provider_chain_sample",
    "evaluate_render_structure",
    "evaluate_timeline_order",
    "extract_clip_frames",
    "extract_script_payload",
    "extract_step_timings",
    "lint_script",
    "load_provider_chain",
    "make_contact_sheet",
    "normalize_script_score",
    "provider_chain_script_text",
    "resolve_provider_chain_path",
    "structured_script_score",
    "write_quality_outputs",
]
