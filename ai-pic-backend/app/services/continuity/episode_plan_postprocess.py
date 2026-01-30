from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from app.services.continuity.episode_continuity import (
    build_previous_episodes_context,
    extract_single_episode,
    init_continuity_ledger_from_story,
    run_episode_continuity_audit,
    run_episode_ledger_update,
    run_episode_rewrite_with_audit,
)


def _build_outline_stub_from_episode(episode: Dict[str, Any]) -> Dict[str, Any]:
    ep_num = int(episode.get("episode_number") or 0) or 1
    title = episode.get("title") or f"第{ep_num}集"
    logline = ""
    if isinstance(episode.get("plot_points"), list) and episode.get("plot_points"):
        first = episode["plot_points"][0]
        if isinstance(first, dict):
            logline = str(first.get("description") or "").strip()
        else:
            logline = str(first or "").strip()
    if not logline:
        logline = str(episode.get("summary") or "").strip()
    if len(logline) > 240:
        logline = logline[:240].rstrip() + "…"
    return {"episode_number": ep_num, "title": title, "logline": logline}


async def postprocess_episode_plan_list(
    *,
    ai_manager: Any,
    story: Dict[str, Any],
    episodes: List[Dict[str, Any]],
    model: Optional[str],
    prefer_provider: Optional[str],
    temperature: float,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], str]:
    """Audit/rewrite + rolling ledger update for episode lists generated in one shot."""
    ordered = sorted(
        [ep for ep in episodes if isinstance(ep, dict)],
        key=lambda x: int(x.get("episode_number") or 0),
    )

    continuity_ledger = (
        story.get("continuity_ledger")
        if isinstance(story.get("continuity_ledger"), dict)
        else None
    )
    if not continuity_ledger:
        continuity_ledger = init_continuity_ledger_from_story(story)

    outlines = [_build_outline_stub_from_episode(ep) for ep in ordered]
    updated: list[dict[str, Any]] = []

    for ep in ordered:
        outline = _build_outline_stub_from_episode(ep)
        previous_eps = build_previous_episodes_context(
            step_outlines=outlines,
            ledger=continuity_ledger,
            current_episode_number=int(outline.get("episode_number") or 1),
        )

        audit, _ = await run_episode_continuity_audit(
            ai_manager=ai_manager,
            story=story,
            outline=outline,
            previous_episodes_context=previous_eps,
            continuity_ledger=continuity_ledger,
            episode_plan=ep,
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
        )
        if audit.verdict == "fail" and audit.issues:
            rewrite_payload, _ = await run_episode_rewrite_with_audit(
                ai_manager=ai_manager,
                story=story,
                outline=outline,
                previous_episodes_context=previous_eps,
                continuity_ledger=continuity_ledger,
                episode_plan_draft=ep,
                audit_issues=[issue.model_dump() for issue in audit.issues],
                model=model,
                prefer_provider=prefer_provider,
                temperature=temperature,
            )
            rewritten = extract_single_episode(rewrite_payload)
            if isinstance(rewritten, dict):
                ep = rewritten

        ledger_payload, _ = await run_episode_ledger_update(
            ai_manager=ai_manager,
            previous_ledger=continuity_ledger,
            story=story,
            outline=outline,
            episode_plan=ep,
            model=model,
            prefer_provider=prefer_provider,
        )
        continuity_ledger = ledger_payload.ledger.model_dump()
        ep["continuity_snapshot"] = ledger_payload.episode_snapshot.model_dump()
        updated.append(ep)

    content_text = json.dumps({"episodes": updated}, ensure_ascii=False)
    return updated, continuity_ledger, content_text
