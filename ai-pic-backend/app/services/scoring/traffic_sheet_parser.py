from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.schemas.generation import TrafficSheet, TrafficSheetAsset
from app.utils.json_utils import extract_json_block

logger = get_logger()


def parse_traffic_sheet_response(
    response: str,
    *,
    episode_id: Optional[int] = None,
    script_id: Optional[int] = None,
    story: Optional[Dict[str, Any]] = None,
) -> TrafficSheet:
    try:
        data = extract_json_block(response)
        if not data:
            raise ValueError("No JSON found in response")

        return TrafficSheet(
            episode_id=episode_id or _coerce_int(data.get("episode_id")),
            script_id=script_id or _coerce_int(data.get("script_id")),
            market_region=data.get("market_region")
            or (story.get("market_region") if story else None),
            micro_genre=data.get("micro_genre")
            or (story.get("micro_genre") if story else None),
            assets=_parse_assets(data.get("assets", [])),
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.warning(f"Failed to parse traffic sheet response: {e}")
        return TrafficSheet(
            episode_id=episode_id,
            script_id=script_id,
            market_region=story.get("market_region") if story else None,
            micro_genre=story.get("micro_genre") if story else None,
            assets=[],
            generated_at=datetime.utcnow(),
        )


def _parse_assets(raw_assets: Any) -> list[TrafficSheetAsset]:
    assets: list[TrafficSheetAsset] = []
    if not isinstance(raw_assets, list):
        return assets

    for asset_data in raw_assets:
        if not isinstance(asset_data, dict):
            continue
        assets.append(
            TrafficSheetAsset(
                asset_id=asset_data.get("asset_id", f"asset_{len(assets)+1}"),
                duration_seconds=_coerce_int(
                    asset_data.get("duration_seconds"), default=15
                ),
                market_region=asset_data.get("market_region"),
                micro_genre=asset_data.get("micro_genre"),
                hook_type=asset_data.get("hook_type", "reveal"),
                source_episode=_coerce_int(
                    asset_data.get("source_episode"), default=1
                ),
                source_timecode_start=asset_data.get("source_timecode_start"),
                source_timecode_end=asset_data.get("source_timecode_end"),
                key_line=asset_data.get("key_line", ""),
                visual_hook=asset_data.get("visual_hook", ""),
                shot_list=asset_data.get("shot_list", []),
                cliff_or_cta=asset_data.get("cliff_or_cta", ""),
                music_reference=asset_data.get("music_reference"),
                compliance_flags=asset_data.get("compliance_flags"),
            )
        )
    return assets


def _coerce_int(value: Any, *, default: Optional[int] = None) -> Optional[int]:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
