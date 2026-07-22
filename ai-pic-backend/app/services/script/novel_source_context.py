from __future__ import annotations

from typing import Any


def build_source_novel_context(episode) -> dict[str, Any] | None:
    revision_id = getattr(episode, "source_novel_export_business_id", None)
    refs = getattr(episode, "source_chapter_refs", None)
    if not revision_id or not isinstance(refs, list):
        return None
    metadata = (
        episode.extra_metadata if isinstance(episode.extra_metadata, dict) else {}
    )
    params = (
        episode.generation_params if isinstance(episode.generation_params, dict) else {}
    )
    return {
        "revision_business_id": revision_id,
        "revision_content_hash": metadata.get("source_novel_content_hash"),
        "adaptation_plan_version": params.get("adaptation_plan_version"),
        "adaptation_goal": metadata.get("adaptation_goal"),
        "source_anchors": [
            {
                "chapter_business_id": row.get("business_id"),
                "position": row.get("position"),
                "title": row.get("title"),
                "summary": row.get("summary"),
                "content_hash": row.get("content_hash"),
            }
            for row in refs
            if isinstance(row, dict)
        ],
    }
