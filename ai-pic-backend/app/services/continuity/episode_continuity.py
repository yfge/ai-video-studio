from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.prompts.manager import prompt_manager
from app.schemas.continuity import (
    ContinuityAuditResult,
    ContinuityLedger,
    EpisodeContinuityUpdatePayload,
)
from app.schemas.generation import EpisodePlanModel
from app.utils.json_utils import extract_json_block


def init_continuity_ledger_from_story(story: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize a continuity ledger from story payload without model calls."""
    characters: dict[str, Any] = {}
    candidates = []
    if isinstance(story.get("character_profiles"), list):
        candidates = story.get("character_profiles") or []
    elif isinstance(story.get("main_characters"), list):
        candidates = story.get("main_characters") or []

    for raw in candidates:
        name = ""
        if isinstance(raw, dict):
            name = str(raw.get("name") or raw.get("character_name") or "").strip()
        elif isinstance(raw, str):
            name = raw.strip()
        if not name or name in characters:
            continue
        characters[name] = {
            "status": "",
            "goal": "",
            "relationships": {},
            "known_info": [],
            "unknown_info": [],
        }

    # Always return a dict that matches ContinuityLedger (best-effort).
    return ContinuityLedger(
        version=1,
        facts=[],
        timeline=[],
        characters=characters,
        info_acquisition_events=[],
        open_threads=[],
        resolved_threads=[],
    ).model_dump()


def compact_continuity_ledger_for_prompt(ledger: Dict[str, Any]) -> Dict[str, Any]:
    """Truncate ledger payload for prompt injection."""
    base = ledger if isinstance(ledger, dict) else {}
    facts = (base.get("facts") if isinstance(base.get("facts"), list) else [])[:25]
    timeline = (base.get("timeline") if isinstance(base.get("timeline"), list) else [])[
        :30
    ]
    open_threads = (
        (base.get("open_threads") if isinstance(base.get("open_threads"), list) else [])[
            :25
        ]
    )
    resolved_threads = (
        (
            base.get("resolved_threads")
            if isinstance(base.get("resolved_threads"), list)
            else []
        )[:25]
    )
    events = (
        (
            base.get("info_acquisition_events")
            if isinstance(base.get("info_acquisition_events"), list)
            else []
        )[:60]
    )
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


def build_previous_episodes_context(
    *,
    step_outlines: List[Dict[str, Any]],
    ledger: Dict[str, Any],
    current_episode_number: int,
) -> List[Dict[str, Any]]:
    """Merge step outline info with continuity snapshots for prompt context."""
    timeline = ledger.get("timeline") if isinstance(ledger.get("timeline"), list) else []
    timeline_by_ep = {
        int(item.get("episode_number") or 0): item
        for item in timeline
        if isinstance(item, dict)
    }

    previous: list[dict[str, Any]] = []
    for outline in step_outlines:
        ep_num = outline.get("episode_number")
        if not isinstance(ep_num, int) or ep_num >= current_episode_number:
            continue
        entry = {
            "episode_number": ep_num,
            "title": outline.get("title"),
            "logline": outline.get("logline"),
        }
        snapshot = timeline_by_ep.get(ep_num) or {}
        entry.update(
            {
                "time_anchor": snapshot.get("time_anchor"),
                "location_anchor": snapshot.get("location_anchor"),
                "end_state": snapshot.get("end_state"),
                "reveals": snapshot.get("reveals") or [],
            }
        )
        previous.append(entry)
    return previous


async def run_episode_continuity_audit(
    *,
    ai_manager: Any,
    story: Dict[str, Any],
    outline: Dict[str, Any],
    previous_episodes_context: List[Dict[str, Any]],
    continuity_ledger: Dict[str, Any],
    episode_plan: Dict[str, Any],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
) -> Tuple[ContinuityAuditResult, Any]:
    schema = ContinuityAuditResult.model_json_schema()
    prompt = prompt_manager.render_prompt(
        "episode_continuity_audit",
        {
            "story": story,
            "outline": outline,
            "previous_episodes_context": previous_episodes_context,
            "continuity_ledger": compact_continuity_ledger_for_prompt(continuity_ledger),
            "episode_plan": episode_plan,
        },
    )
    resp = await ai_manager.generate_text(
        prompt=prompt,
        temperature=min(0.4, temperature),
        model=model,
        prefer_provider=prefer_provider,
        json_schema={"name": "continuity_audit", "schema": schema},
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
                    "description": "continuity_audit 输出无法解析/不符合 schema",
                    "evidence": str(raw)[:500],
                    "fix_guidance": "请严格输出 JSON 并遵守 schema。",
                }
            ],
            summary="audit_parse_failed",
        )
    return parsed, resp


async def run_episode_rewrite_with_audit(
    *,
    ai_manager: Any,
    story: Dict[str, Any],
    outline: Dict[str, Any],
    previous_episodes_context: List[Dict[str, Any]],
    continuity_ledger: Dict[str, Any],
    episode_plan_draft: Dict[str, Any],
    audit_issues: List[Dict[str, Any]],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
) -> Tuple[Dict[str, Any], Any]:
    schema = EpisodePlanModel.model_json_schema()
    prompt = prompt_manager.render_prompt(
        "episode_rewrite_with_audit",
        {
            "story": story,
            "outline": outline,
            "previous_episodes_context": previous_episodes_context,
            "continuity_ledger": compact_continuity_ledger_for_prompt(continuity_ledger),
            "episode_plan": episode_plan_draft,
            "audit_issues": audit_issues,
        },
    )
    resp = await ai_manager.generate_text(
        prompt=prompt,
        temperature=min(0.5, temperature),
        model=model,
        prefer_provider=prefer_provider,
        json_schema={"name": "episode_plan_rewrite", "schema": schema},
        system_prompt=prompt_manager.render_prompt("system_prompt_json_strict", {}),
    )
    raw = resp.data if isinstance(resp.data, str) else (resp.data or {})
    payload = raw if isinstance(raw, dict) else (extract_json_block(raw) or {})
    return payload if isinstance(payload, dict) else {}, resp


async def run_episode_ledger_update(
    *,
    ai_manager: Any,
    previous_ledger: Dict[str, Any],
    story: Dict[str, Any],
    outline: Dict[str, Any],
    episode_plan: Dict[str, Any],
    model: Optional[str],
    prefer_provider: Optional[str],
) -> Tuple[EpisodeContinuityUpdatePayload, Any]:
    schema = EpisodeContinuityUpdatePayload.model_json_schema()
    prompt = prompt_manager.render_prompt(
        "episode_continuity_ledger_update",
        {
            "previous_ledger": compact_continuity_ledger_for_prompt(previous_ledger),
            "story": story,
            "outline": outline,
            "episode_plan": episode_plan,
        },
    )
    resp = await ai_manager.generate_text(
        prompt=prompt,
        temperature=0.2,
        model=model,
        prefer_provider=prefer_provider,
        json_schema={"name": "episode_continuity_ledger_update", "schema": schema},
        system_prompt=prompt_manager.render_prompt("system_prompt_json_strict", {}),
    )
    raw = resp.data if isinstance(resp.data, str) else (resp.data or {})
    payload = raw if isinstance(raw, dict) else (extract_json_block(raw) or {})
    try:
        parsed = EpisodeContinuityUpdatePayload.model_validate(payload)
    except Exception:
        parsed = EpisodeContinuityUpdatePayload(
            ledger=ContinuityLedger(**previous_ledger),
            episode_snapshot={
                "episode_number": int(outline.get("episode_number") or 0) or 1,
                "time_anchor": None,
                "location_anchor": None,
                "end_state": None,
                "reveals": [],
                "info_acquisition_events": [],
            },
        )
    return parsed, resp


def extract_single_episode(plan_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    episodes = plan_payload.get("episodes") if isinstance(plan_payload, dict) else None
    if not isinstance(episodes, list) or not episodes:
        return None
    first = episodes[0] if isinstance(episodes[0], dict) else None
    return first

