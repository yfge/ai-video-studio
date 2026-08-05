"""Model-call helpers for v5 scene, prose, extraction, and review stages."""

from __future__ import annotations

from app.services.narrative_consistency import ClaimDelta, validate_chapter_transition

from .story_novel_export_ai import TruncatedNovelOutput
from .story_novel_finish_reason import is_recoverable_length_finish_reason
from .story_novel_sentence_spans import audit_sentence_index, sentence_spans
from .story_novel_v5_chapter_context import prompt_snapshot
from .story_novel_v5_consistency_report import consistency_issue
from .story_novel_v5_prompts import (
    claim_prompt,
    continuation_prompt,
    full_rewrite_prompt,
    prose_prompt,
    readability_prompt,
    scene_prompt,
    span_repair_prompt,
)
from .story_novel_v5_model_calls import (
    call_metrics,
    invocation_evidence,
    json_call,
)
from .story_novel_v5_readability import validate_readability
from .story_novel_v5_text import (
    clean_prose,
    complete_sentence_prefix,
    merge_continuation,
)


async def generate_scene(revision, position, value, generate_text):
    result, metrics = await json_call(
        revision,
        scene_prompt(value),
        lambda payload: _validate_scene(payload, value),
        generate_text,
        stage=f"scene_planning.{position}",
        max_tokens=8_000,
    )
    return result, metrics


async def generate_prose(revision, position, value, generate_text):
    return await _continuous_prose_call(
        revision,
        value,
        prose_prompt(value),
        generate_text,
        stage=f"prose.{position}",
    )


async def _continuous_prose_call(
    revision, value, prompt, generate_text, *, stage, temperature=None
):
    attempts = []
    try:
        text = await generate_text(
            revision,
            prompt,
            stage=stage,
            max_tokens=_prose_tokens(value),
            **({"temperature": temperature} if temperature is not None else {}),
        )
        attempts.append(invocation_evidence(text))
        return clean_prose(str(text)), call_metrics(attempts)
    except TruncatedNovelOutput as exc:
        if not is_recoverable_length_finish_reason(exc.finish_reason):
            raise
        attempts.append(dict(exc.invocation_evidence or {}))
        prefix = complete_sentence_prefix(exc.partial_text)
        if not prefix:
            raise ValueError(
                "truncated prose has no complete sentence boundary"
            ) from exc
        continued = await generate_text(
            revision,
            continuation_prompt(
                {
                    "ending_context": prefix[-2_000:],
                    "remaining_events": value.get("allowed_events") or [],
                    "obligations": value.get("obligations") or [],
                    "hook": (value.get("scene_plan") or {}).get("hook"),
                    "remaining_target_chars": max(
                        0, int(value["target_chars"]) - len("".join(prefix.split()))
                    ),
                }
            ),
            stage=f"{stage}.truncation_continue",
            max_tokens=_prose_tokens(value),
            temperature=0.2,
        )
        attempts.append(invocation_evidence(continued))
        return merge_continuation(prefix, str(continued)), call_metrics(attempts)


async def generate_span_repair(revision, position, value, generate_text):
    text = await generate_text(
        revision,
        span_repair_prompt(value),
        stage=f"span_repair.{position}",
        max_tokens=8_000,
        temperature=0.2,
    )
    return clean_prose(str(text)), call_metrics([invocation_evidence(text)])


async def generate_full_rewrite(revision, position, value, generate_text):
    return await _continuous_prose_call(
        revision,
        value,
        full_rewrite_prompt(value),
        generate_text,
        stage=f"full_rewrite.{position}",
        temperature=0.2,
    )


async def audit_candidate(
    revision,
    position,
    content,
    contract,
    generate_text,
    *,
    source_artifact_id,
    source_hash,
):
    sentences = sentence_spans(content)
    common = {
        "consistency_schema": contract["schema"],
        "snapshot_before": prompt_snapshot(contract["snapshot_before"]),
        "allowed_events": contract["allowed_events"],
        "sentence_index": audit_sentence_index(sentences),
    }
    delta, claim_metrics = await json_call(
        revision,
        claim_prompt(common),
        lambda payload: _bind_evidence(payload, source_artifact_id, source_hash),
        generate_text,
        stage=f"claim_extraction.{position}",
        max_tokens=10_000,
        temperature=0.1,
    )
    try:
        consistency = validate_chapter_transition(
            contract["schema"],
            contract["snapshot_before"],
            delta,
            sentences,
            allowed_event_ids={item["id"] for item in contract["allowed_events"]},
            event_catalog={item["id"]: item for item in contract["event_catalog"]},
        )
        consistency_report = {"status": "passed", "issues": []}
    except ValueError as exc:
        consistency = None
        consistency_report = {
            "status": "failed",
            "issues": [consistency_issue(exc, delta, sentences)],
        }
    readability, readability_metrics = await json_call(
        revision,
        readability_prompt(
            {
                "chapter_contract": contract["chapter"],
                "scene_plan": contract["scene_plan"],
                "sentence_index": audit_sentence_index(sentences),
            }
        ),
        lambda payload: validate_readability(payload, sentences),
        generate_text,
        stage=f"readability.{position}",
        max_tokens=6_000,
        temperature=0.1,
    )
    return {
        "content_text": content,
        "sentence_index": sentences,
        "claim_delta": delta,
        "consistency_report": consistency_report,
        "readability_report": readability,
        "state_patch": (consistency or {}).get("state_patch"),
        "graph_after": (consistency or {}).get("graph_after"),
        "metrics": {
            "claim_extraction": claim_metrics,
            "readability": readability_metrics,
        },
    }


def _validate_scene(payload, value):
    scenes = payload.get("scenes") or []
    if not scenes or len({item.get("id") for item in scenes}) != len(scenes):
        raise ValueError("scene plan requires unique, non-empty scenes")
    expected = {item["id"] for item in value.get("allowed_events") or []}
    actual = {event for item in scenes for event in item.get("event_ids") or []}
    if actual != expected:
        raise ValueError("scene plan does not cover exactly the allowed events")
    entities = {item["id"] for item in value["snapshot_before"]["entities"]}
    if any(
        participant not in entities
        for item in scenes
        for participant in item.get("participant_ids") or []
    ):
        raise ValueError("scene plan references an unknown entity")
    required = ("causal_bridge", "emotional_continuity", "summary", "hook")
    if any(not str(payload.get(key) or "").strip() for key in required):
        raise ValueError("scene plan is missing narrative continuity fields")
    return payload


def _bind_evidence(payload, artifact_id, source_hash):
    result = dict(payload)
    result["evidence"] = [
        {
            **item,
            "source_artifact_type": "novel_chapter",
            "source_artifact_id": artifact_id,
            "source_version": 1,
            "source_hash": source_hash,
        }
        for item in payload.get("evidence") or []
    ]
    return ClaimDelta.model_validate(result).model_dump()


def _prose_tokens(value):
    maximum = int(value.get("max_chars") or 4_000)
    return min(32_000, max(4_000, maximum * 2))
