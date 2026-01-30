"""
Scoring artifacts pipeline.

Generates script score + traffic sheet and derives lightweight tags that can be
stored in Script.extra_metadata and Task.parameters.agent_run for auditability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.schemas.generation import TrafficSheet
from app.services.scoring.script_score_service import ScriptScoreService
from app.services.scoring.traffic_sheet_service import TrafficSheetService

if TYPE_CHECKING:
    from app.services.ai_service import AIService


def build_traffic_asset_tags(sheet: TrafficSheet) -> Dict[str, Any]:
    hook_types: set[str] = set()
    durations: set[int] = set()
    compliance_flags: set[str] = set()

    assets = sheet.assets or []
    for asset in assets:
        if asset.hook_type:
            hook_types.add(str(asset.hook_type))
        if asset.duration_seconds is not None:
            durations.add(int(asset.duration_seconds))
        for flag in asset.compliance_flags or []:
            if flag:
                compliance_flags.add(str(flag))

    return {
        "asset_count": len(assets),
        "hook_types": sorted(hook_types),
        "durations": sorted(durations),
        "compliance_flags": sorted(compliance_flags),
    }


async def generate_scoring_artifacts(
    *,
    ai_service: "AIService",
    script_content: str,
    story: Optional[Dict[str, Any]] = None,
    episode: Optional[Dict[str, Any]] = None,
    scenes: Optional[List[Dict[str, Any]]] = None,
    dialogues: Optional[List[Dict[str, Any]]] = None,
    hook_plan: Optional[Dict[str, Any]] = None,
    prefer_provider: Optional[str] = None,
    prefer_model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate scoring artifacts for a script.

    Returns a dict that is safe to JSON serialize and embed into agent_run.
    """
    score_service = ScriptScoreService(ai_service)
    traffic_service = TrafficSheetService(ai_service)

    score = await score_service.score_script(
        script_content=script_content,
        story=story,
        episode=episode,
        scenes=scenes,
        dialogues=dialogues,
        prefer_provider=prefer_provider,
        prefer_model=prefer_model,
    )

    episode_number = None
    if isinstance(episode, dict):
        episode_number = episode.get("episode_number")
    traffic = await traffic_service.generate_traffic_sheet(
        script_content=script_content,
        episode_number=int(episode_number or 1),
        story=story,
        scenes=scenes,
        dialogues=dialogues,
        hook_plan=hook_plan,
        prefer_provider=prefer_provider,
        prefer_model=prefer_model,
    )

    traffic_tags = build_traffic_asset_tags(traffic)

    return {
        "script_score": score.model_dump(mode="json", exclude_none=True),
        "traffic_sheet": traffic.model_dump(mode="json", exclude_none=True),
        "asset_tags": traffic_tags,
    }
