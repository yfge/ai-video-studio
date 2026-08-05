"""Bounded, auditable model calls shared by v5 structured stages."""

from app.utils.json_utils import extract_json_block

from .story_novel_v5_prompts import json_repair_prompt


async def json_call(
    revision,
    prompt,
    parser,
    generate_text,
    *,
    stage,
    max_tokens,
    temperature=None,
):
    attempts = []
    text = await generate_text(
        revision,
        prompt,
        stage=stage,
        max_tokens=max_tokens,
        **({"temperature": temperature} if temperature is not None else {}),
    )
    attempts.append(invocation_evidence(text))
    try:
        return parser(json_payload(text)), call_metrics(attempts)
    except (TypeError, ValueError) as exc:
        repair = await generate_text(
            revision,
            json_repair_prompt(
                {
                    "original_response": str(text),
                    "validation_error": str(exc),
                }
            ),
            stage=f"{stage}.format_repair",
            max_tokens=max_tokens,
            temperature=0.1,
        )
        attempts.append(invocation_evidence(repair))
        return parser(json_payload(repair)), call_metrics(attempts)


def json_payload(text):
    payload = extract_json_block(str(text))
    if not isinstance(payload, dict):
        raise ValueError("response does not contain one JSON object")
    return payload


def invocation_evidence(text):
    return dict(getattr(text, "invocation_evidence", {}) or {})


def call_metrics(attempts):
    return {
        "calls": len(attempts),
        "attempts": attempts,
        "invocation_ids": [
            item["invocation_id"] for item in attempts if item.get("invocation_id")
        ],
        "input_tokens": sum(int(item.get("input_tokens") or 0) for item in attempts),
        "output_tokens": sum(int(item.get("output_tokens") or 0) for item in attempts),
        "latency_ms": sum(int(item.get("latency_ms") or 0) for item in attempts),
    }
