"""Read the durable invocation created for one novel model stage."""

from __future__ import annotations

import hashlib

from app.core.database import SessionLocal
from app.repositories.llm_invocation_repository import LLMInvocationRepository


def latest_invocation_evidence(
    call_scene: str, expected_response: str, *, invocation_id: int | None
) -> dict:
    session = SessionLocal()
    try:
        product_hash = hashlib.sha256(expected_response.encode()).hexdigest()
        row = _matching_row(
            LLMInvocationRepository(session),
            call_scene,
            expected_response,
            invocation_id,
        )
        if row is None:
            return {}
        return invocation_row_evidence(row, product_hash=product_hash)
    finally:
        session.close()


def mark_invocation_product_rejected(
    call_scene: str,
    expected_response: str,
    *,
    invocation_id: int | None,
    reason: str,
) -> dict:
    """Preserve transport success while recording product-level rejection."""
    session = SessionLocal()
    try:
        product_hash = hashlib.sha256(expected_response.encode()).hexdigest()
        repository = LLMInvocationRepository(session)
        row = _matching_row(repository, call_scene, expected_response, invocation_id)
        if row is None:
            return {}
        metadata = {
            **dict(row.response_metadata or {}),
            "product_status": "rejected",
            "product_error": reason,
        }
        repository.update(row, response_metadata=metadata)
        session.commit()
        return {
            "invocation_id": row.id,
            "response_hash": product_hash,
            "raw_response_hash": hashlib.sha256(
                str(row.response or "").encode()
            ).hexdigest(),
        }
    finally:
        session.close()


def bind_invocation_prompt_template(invocation_id: int | None, template: dict) -> dict:
    """Persist the exact PromptManager template fingerprint used by a stage."""
    if invocation_id is None or not template:
        return {}
    session = SessionLocal()
    try:
        repository = LLMInvocationRepository(session)
        row = repository.get_by_id(int(invocation_id))
        if row is None:
            return {}
        if invocation_input_prompt_template(row) != template:
            raise ValueError("invocation 创建前 PromptManager 指纹缺失或不匹配")
        metadata = {**dict(row.response_metadata or {}), "prompt_template": template}
        repository.update(row, response_metadata=metadata)
        session.commit()
        return dict(template)
    finally:
        session.close()


def _matching_row(repository, call_scene, expected_response, invocation_id):
    try:
        row = repository.get_by_id(int(invocation_id))
    except (TypeError, ValueError):
        return None
    if (
        row is None
        or row.call_scene != call_scene
        or row.status != "succeeded"
        or str(row.response or "").strip() != expected_response
    ):
        return None
    return row


def invocation_row_evidence(row, *, product_hash: str | None = None) -> dict:
    raw_response = str(row.response or "")
    metadata = dict(row.response_metadata or {})
    evidence = {
        "invocation_id": row.id,
        "call_scene": row.call_scene,
        "provider": row.provider,
        "model": row.model,
        "status": row.status,
        "input_tokens": int(row.input_tokens or 0),
        "cache_tokens": int(row.cache_tokens or 0),
        "output_tokens": int(row.output_tokens or 0),
        "finish_reason": str(metadata.get("finish_reason") or ""),
        "latency_ms": int(row.latency_ms or 0),
        "response_hash": product_hash
        or hashlib.sha256(raw_response.strip().encode()).hexdigest(),
        "raw_response_hash": hashlib.sha256(raw_response.encode()).hexdigest(),
        "product_status": str(metadata.get("product_status") or "accepted"),
    }
    template = invocation_prompt_template(row)
    if template:
        evidence["prompt_template"] = template
    return evidence


def invocation_prompt_template(row) -> dict:
    prebound = invocation_input_prompt_template(row)
    if prebound:
        return prebound
    metadata = dict(row.response_metadata or {})
    if metadata.get("prompt_template"):
        return dict(metadata["prompt_template"])


def invocation_input_prompt_template(row) -> dict:
    references = getattr(row, "input_references", None) or []
    if not isinstance(references, list):
        return {}
    for item in references:
        if (
            isinstance(item, dict)
            and item.get("type") == "prompt_template"
            and isinstance(item.get("value"), dict)
        ):
            return dict(item["value"])
    return {}


class GeneratedNovelText(str):
    """String-compatible provider output carrying persisted invocation evidence."""

    invocation_evidence: dict

    def __new__(cls, value: str, evidence: dict | None = None):
        instance = super().__new__(cls, value)
        instance.invocation_evidence = dict(evidence or {})
        return instance
