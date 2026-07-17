from __future__ import annotations

from typing import Any, Dict, Optional

from app.services.ai.scripts_continuity_contract import sync_structured_contract
from app.services.continuity.script_continuity import (
    run_script_continuity_audit,
    run_script_dialogues_rewrite_with_audit,
)


async def apply_script_continuity_rewrite(
    *,
    ai_manager: Any,
    logger: Any,
    payload: Dict[str, Any],
    story: Dict[str, Any],
    episode: Dict[str, Any],
    continuity_ledger: Optional[Dict[str, Any]],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
) -> None:
    if not ai_manager:
        return
    scenes = payload.get("scenes") if isinstance(payload.get("scenes"), list) else []
    dialogues = (
        payload.get("dialogues") if isinstance(payload.get("dialogues"), list) else []
    )
    stage_directions = (
        payload.get("stage_directions")
        if isinstance(payload.get("stage_directions"), list)
        else []
    )
    if not scenes:
        return
    try:
        audit, _ = await run_script_continuity_audit(
            ai_manager=ai_manager,
            story=story,
            episode=episode,
            continuity_ledger=continuity_ledger,
            scenes=scenes,
            dialogues=dialogues,
            stage_directions=stage_directions,
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
        )
        if audit.verdict != "fail" or not audit.issues:
            return
        rewrite_payload, _ = await run_script_dialogues_rewrite_with_audit(
            ai_manager=ai_manager,
            story=story,
            episode=episode,
            continuity_ledger=continuity_ledger,
            scenes=scenes,
            dialogues=dialogues,
            stage_directions=stage_directions,
            audit_issues=[issue.model_dump() for issue in audit.issues],
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
        )
        _merge_rewrite(payload, rewrite_payload, issue_count=len(audit.issues))
    except Exception as exc:
        logger.warning("Script continuity rewrite failed", extra={"error": str(exc)})


def _merge_rewrite(
    payload: Dict[str, Any],
    rewrite_payload: Dict[str, Any],
    *,
    issue_count: int,
) -> None:
    new_dialogues = _optional_list(rewrite_payload.get("dialogues"))
    new_stage = _optional_list(rewrite_payload.get("stage_directions"))
    new_scenes = _optional_list(rewrite_payload.get("scenes"))
    if new_scenes is not None:
        payload["scenes"] = new_scenes
    if new_dialogues is not None:
        payload["dialogues"] = new_dialogues
    if new_stage is not None:
        payload["stage_directions"] = new_stage
    contract_synced = sync_structured_contract(
        payload,
        scenes=new_scenes,
        dialogues=new_dialogues,
        stage_directions=new_stage,
    )
    payload.setdefault("metadata", {})
    if isinstance(payload["metadata"], dict):
        rewrite_metadata = {
            "verdict": "fail",
            "issue_count": issue_count,
        }
        if contract_synced is not None:
            rewrite_metadata["structured_contract_synced"] = contract_synced
        payload["metadata"]["continuity_rewrite"] = rewrite_metadata


def _optional_list(value: Any) -> list[Any] | None:
    return value if isinstance(value, list) else None
