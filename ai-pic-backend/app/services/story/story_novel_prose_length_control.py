"""Closed-loop prose length control derived from prior accepted invocations."""

from __future__ import annotations

import copy
import statistics

from .story_novel_context_utils import value_hash
from .story_novel_prompt_renderer import prompt_template_evidence
from .story_novel_prose_length_evidence import (
    reconstruct_initial_prose,
    recorded_initial_prose,
)
from .story_novel_prose_length_history import length_observations
from .story_novel_prose_length_policy import (
    POLICY_SCHEMA,
    length_control_required,
    valid_length_control_marker,
)
from .story_novel_prose_length_prompt import controlled_prompt_input
from .story_novel_v3_prompts import prose_blocks_prompt

_LEGACY_WINDOW = 8
_CONTROLLED_WINDOW = 3
_MIN_LEGACY_SAMPLES = 3
_MIN_SCALE = 0.30
_MAX_SCALE = 1.25
_REQUEST_VARIANCE = 0.10
PROMPT_CONTRACT_VERSION = 5


def build_length_control(
    db,
    revision,
    position: int,
    prose_input: dict,
    *,
    prompt_contract_version: int = PROMPT_CONTRACT_VERSION,
) -> dict:
    """Return a bounded model request target without changing the chapter contract."""
    model = _prose_model(revision)
    observations = length_observations(
        db,
        revision,
        position,
        model,
        POLICY_SCHEMA,
        prompt_contract_version,
    )
    controlled = [item for item in observations if item["controlled"]]
    samples = (
        controlled[-_CONTROLLED_WINDOW:]
        if controlled
        else observations[-_LEGACY_WINDOW:]
    )
    enough = bool(controlled) or len(samples) >= _MIN_LEGACY_SAMPLES
    response_ratio = (
        statistics.median(
            item["actual_chars"] / item["requested_chars"] for item in samples
        )
        if enough
        else 1.0
    )
    scale = _bounded(1.0 / response_ratio, _MIN_SCALE, _MAX_SCALE)
    if controlled:
        prior = float(controlled[-1].get("request_scale") or 1.0)
        scale = _bounded(scale, prior * 0.67, prior * 1.5)
        scale = _bounded(scale, _MIN_SCALE, _MAX_SCALE)
    acceptance = copy.deepcopy(prose_input["chapter_length"])
    requested = max(1, round(int(acceptance["target_chars"]) * scale))
    if 3 <= prompt_contract_version < 5:
        requested = _safe_v3_target(acceptance, requested)
    block_targets = _scaled_blocks(
        prose_input["chapter_brief"].get("beats") or [], requested
    )
    result = {
        "schema": POLICY_SCHEMA,
        "model": model,
        "sample_source": (
            "controlled" if controlled else "historical" if enough else "none"
        ),
        "sample_count": len(samples) if enough else 0,
        "sample_refs": [_sample_ref(item) for item in samples] if enough else [],
        "observed_response_ratio": round(response_ratio, 6),
        "request_scale": round(scale, 6),
        "acceptance_length": acceptance,
        "requested_length": _requested_length(
            acceptance, requested, prompt_contract_version
        ),
        "requested_blocks": block_targets,
    }
    if prompt_contract_version > 1:
        result["prompt_contract_version"] = prompt_contract_version
    return result


def record_length_observation(
    metrics: dict, control: dict, prose: dict, prompt_input: dict
) -> dict:
    result = copy.deepcopy(metrics)
    requested = int(control["requested_length"]["target_chars"])
    evidence = recorded_initial_prose(prose, metrics)
    actual = int(evidence["observed_output_chars"])
    result["length_control"] = {
        **copy.deepcopy(control),
        "prompt_input_hash": value_hash(prompt_input),
        **evidence,
        "observed_output_ratio": round(actual / requested, 6),
    }
    return result


def valid_length_control(
    db, revision, position: int, prose_input: dict, prose_metric: dict
) -> bool:
    if not valid_length_control_marker(revision):
        return False
    stored = copy.deepcopy(prose_metric.get("length_control") or {})
    if not stored:
        return not length_control_required(revision, position)
    actual = int(stored.pop("observed_output_chars", 0) or 0)
    ratio = stored.pop("observed_output_ratio", None)
    prompt_hash = stored.pop("prompt_input_hash", None)
    body_hash = stored.pop("initial_prose_body_hash", None)
    source_ids = stored.pop("source_invocation_ids", None)
    source_hashes = stored.pop("source_response_hashes", None)
    version = int(stored.get("prompt_contract_version") or 1)
    expected = build_length_control(
        db,
        revision,
        position,
        prose_input,
        prompt_contract_version=version,
    )
    prompt_input = controlled_prompt_input(prose_input, expected)
    requested = int(expected["requested_length"]["target_chars"])
    attempts = prose_metric.get("attempts") or []
    expected_template = prompt_template_evidence(prose_blocks_prompt(prompt_input))
    actual_template = (attempts[0].get("prompt_template") or {}) if attempts else {}
    reconstructed = reconstruct_initial_prose(
        db,
        revision.business_id,
        position,
        prose_metric,
        len(prose_input["chapter_brief"].get("beats") or []),
    )
    return bool(
        stored == expected
        and actual > 0
        and ratio == round(actual / requested, 6)
        and prompt_hash == value_hash(prompt_input)
        and actual_template.get("rendered_hash")
        == expected_template.get("rendered_hash")
        and reconstructed
        == {
            "initial_prose_body_hash": body_hash,
            "observed_output_chars": actual,
            "source_invocation_ids": source_ids,
            "source_response_hashes": source_hashes,
        }
    )


def _prose_model(revision) -> str | None:
    return ((revision.generation_plan or {}).get("model_policy") or {}).get(
        "prose_model"
    ) or revision.model


def _sample_ref(item: dict) -> dict:
    return {
        key: copy.deepcopy(item.get(key))
        for key in (
            "position",
            "body_hash",
            "source_hash",
            "invocation_ids",
            "prompt_input_hash",
            "requested_chars",
            "actual_chars",
            "controlled",
            "source_revision_business_id",
        )
        if item.get(key) is not None
    }


def _scaled_blocks(beats: list[dict], total: int) -> list[dict]:
    weights = [max(1, int(item.get("target_chars") or 0)) for item in beats]
    weight_sum = sum(weights) or len(beats) or 1
    rows, remaining = [], total
    for index, (beat, weight) in enumerate(zip(beats, weights, strict=True)):
        target = (
            remaining
            if index == len(beats) - 1
            else max(1, total * weight // weight_sum)
        )
        remaining -= target
        rows.append({"block_id": beat["beat_id"], "target_chars": target})
    return rows


def _bounded(value: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, value))


def _safe_v3_target(acceptance: dict, requested: int) -> int:
    """Keep calibration variance inside the immutable acceptance interval."""
    minimum = int(acceptance["min_chars"])
    maximum = int(acceptance["max_chars"])
    lower = (minimum * 100 + 89) // 90
    upper = maximum * 100 // 110
    if lower > upper:
        return int(acceptance["target_chars"])
    return min(upper, max(lower, requested))


def _requested_length(acceptance: dict, requested: int, version: int) -> dict:
    if version >= 5:
        return {
            "min_chars": max(1, requested * 90 // 100),
            "target_chars": requested,
            "max_chars": max(1, requested * 110 // 100),
        }
    if version >= 3:
        return {**copy.deepcopy(acceptance), "target_chars": requested}
    return {
        "min_chars": max(1, requested * 90 // 100),
        "target_chars": requested,
        "max_chars": max(1, requested * 110 // 100),
    }
