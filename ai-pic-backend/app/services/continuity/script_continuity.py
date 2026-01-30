from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.prompts.manager import prompt_manager
from app.schemas.continuity import ContinuityAuditResult
from app.utils.json_utils import extract_json_block


def _compact_ledger_for_prompt(ledger: Dict[str, Any] | None) -> Dict[str, Any]:
    base = ledger if isinstance(ledger, dict) else {}
    facts = (base.get("facts") if isinstance(base.get("facts"), list) else [])[:25]
    timeline = (base.get("timeline") if isinstance(base.get("timeline"), list) else [])[
        :30
    ]
    open_threads = (
        base.get("open_threads") if isinstance(base.get("open_threads"), list) else []
    )[:25]
    resolved_threads = (
        base.get("resolved_threads")
        if isinstance(base.get("resolved_threads"), list)
        else []
    )[:25]
    events = (
        base.get("info_acquisition_events")
        if isinstance(base.get("info_acquisition_events"), list)
        else []
    )[:60]
    characters = (
        base.get("characters") if isinstance(base.get("characters"), dict) else {}
    )
    return {
        "version": int(base.get("version") or 1),
        "facts": facts,
        "timeline": timeline,
        "characters": characters,
        "info_acquisition_events": events,
        "open_threads": open_threads,
        "resolved_threads": resolved_threads,
    }


async def run_script_continuity_audit(
    *,
    ai_manager: Any,
    story: Dict[str, Any],
    episode: Dict[str, Any],
    continuity_ledger: Dict[str, Any] | None,
    scenes: List[Dict[str, Any]],
    dialogues: List[Dict[str, Any]],
    stage_directions: List[Dict[str, Any]],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
) -> Tuple[ContinuityAuditResult, Any]:
    schema = ContinuityAuditResult.model_json_schema()
    prompt = prompt_manager.render_prompt(
        "script_continuity_audit",
        {
            "story": story,
            "episode": episode,
            "continuity_ledger": _compact_ledger_for_prompt(continuity_ledger),
            "scenes": scenes,
            "dialogues": dialogues,
            "stage_directions": stage_directions,
        },
    )
    resp = await ai_manager.generate_text(
        prompt=prompt,
        temperature=min(0.4, temperature),
        model=model,
        prefer_provider=prefer_provider,
        json_schema={"name": "script_continuity_audit", "schema": schema},
        system_prompt=prompt_manager.render_prompt("system_prompt_json_strict", {}),
    )
    raw = resp.data if isinstance(resp.data, str) else (resp.data or {})
    payload = raw if isinstance(raw, dict) else (extract_json_block(raw) or {})
    try:
        parsed = ContinuityAuditResult.model_validate(payload)
    except Exception:
        parsed = ContinuityAuditResult(
            verdict="fail",
            issues=[
                {
                    "issue_type": "plausibility",
                    "severity": "high",
                    "description": "script_continuity_audit 输出无法解析/不符合 schema",
                    "evidence": str(raw)[:500],
                    "fix_guidance": "请严格输出 JSON 并遵守 schema。",
                }
            ],
            summary="audit_parse_failed",
        )
    return parsed, resp


async def run_script_dialogues_rewrite_with_audit(
    *,
    ai_manager: Any,
    story: Dict[str, Any],
    episode: Dict[str, Any],
    continuity_ledger: Dict[str, Any] | None,
    scenes: List[Dict[str, Any]],
    dialogues: List[Dict[str, Any]],
    stage_directions: List[Dict[str, Any]],
    audit_issues: List[Dict[str, Any]],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
) -> Tuple[Dict[str, Any], Any]:
    schema = {
        "type": "object",
        "properties": {
            "dialogues": {"type": "array"},
            "stage_directions": {"type": "array"},
            "scenes": {"type": "array"},
        },
    }
    prompt = prompt_manager.render_prompt(
        "script_dialogues_rewrite_with_audit",
        {
            "story": story,
            "episode": episode,
            "continuity_ledger": _compact_ledger_for_prompt(continuity_ledger),
            "scenes": scenes,
            "dialogues": dialogues,
            "stage_directions": stage_directions,
            "audit_issues": audit_issues,
        },
    )
    resp = await ai_manager.generate_text(
        prompt=prompt,
        temperature=min(0.5, temperature),
        model=model,
        prefer_provider=prefer_provider,
        json_schema={"name": "script_dialogues_rewrite", "schema": schema},
        system_prompt=prompt_manager.render_prompt("system_prompt_json_strict", {}),
    )
    raw = resp.data if isinstance(resp.data, str) else (resp.data or {})
    payload = raw if isinstance(raw, dict) else (extract_json_block(raw) or {})
    return payload if isinstance(payload, dict) else {}, resp
