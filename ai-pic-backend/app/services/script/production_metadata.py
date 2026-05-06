"""Helpers for script production pipeline metadata."""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.models.script import Script
from sqlalchemy.orm import Session


def merge_production_pipeline_metadata(
    db: Session,
    script: Script,
    *,
    production_meta: Dict[str, Any],
    scoring_artifacts: Optional[Dict[str, Any]],
) -> None:
    """Merge production pipeline and scoring metadata onto a script."""
    extra = dict(script.extra_metadata or {})
    extra["production_pipeline"] = production_meta
    if scoring_artifacts is not None:
        extra["scoring"] = scoring_artifacts
    agent_run = dict(extra.get("agent_run") or {})
    agent_run["generation_mode"] = "production"
    agent_run["production_pipeline"] = production_meta
    if scoring_artifacts is not None:
        agent_run["scoring"] = scoring_artifacts
    extra["agent_run"] = agent_run
    script.extra_metadata = extra
    db.add(script)
    db.commit()
    db.refresh(script)
