from __future__ import annotations

from typing import Any, Dict

from app.services.quality_gate_core import make_quality_check


def beat_contract_check(content: Dict[str, Any]) -> Dict[str, Any] | None:
    if not _has_beat_contract_data(content):
        return None
    from app.services.script.beat_contract_normalizer import (
        normalize_script_beat_contract,
    )
    from app.services.script.beat_contract_quality import evaluate_beat_contract_quality

    try:
        contract = normalize_script_beat_contract(content)
    except Exception as exc:
        return make_quality_check(
            "script_beat_contract",
            False,
            "script beat contract must be valid",
            details={"error": str(exc)},
        )
    if _content_has_fallback(content):
        contract.model_extra["fallback_detected"] = True
    report = evaluate_beat_contract_quality(contract)
    return make_quality_check(
        "script_beat_contract",
        report["passed"],
        "script beat contract must pass structure and drama gates",
        details=report,
    )


def required_beat_contract_check(content: Dict[str, Any]) -> Dict[str, Any]:
    return make_quality_check(
        "script_beat_contract_required",
        _has_beat_contract_data(content),
        "production script generation must return a beat-level contract",
        details={"required": True},
    )


def _has_beat_contract_data(content: Dict[str, Any]) -> bool:
    if isinstance(content.get("structured_script_contract"), dict):
        return True
    metadata = content.get("metadata")
    if isinstance(metadata, dict) and isinstance(
        metadata.get("structured_script_contract"), dict
    ):
        return True
    scenes = content.get("scenes") if isinstance(content.get("scenes"), list) else []
    return any(
        isinstance(scene, dict) and isinstance(scene.get("beats"), list)
        for scene in scenes
    )


def _content_has_fallback(content: Dict[str, Any]) -> bool:
    for key in ("dialogues", "stage_directions"):
        items = content.get(key)
        if isinstance(items, list) and any(
            isinstance(item, dict) and item.get("fallback") for item in items
        ):
            return True
    return False
