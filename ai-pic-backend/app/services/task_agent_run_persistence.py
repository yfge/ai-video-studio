"""
Persist agent execution traces into Task.parameters.agent_run.

We already store provider/model/usage metadata on target entities (Story/Episode/Script)
via extra_metadata.agent_run. This module copies the essential audit trail into the Task
record so operators can inspect executions directly from /tasks UI.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional


def persist_task_agent_run(
    *,
    task_id: int,
    user_id: int,
    kind: str,
    request_dict: Optional[Dict[str, Any]] = None,
    db_session=None,
) -> None:
    """Persist agent_run into Task.parameters for a completed task.

    Args:
        task_id: Task primary key.
        user_id: Owner user_id for safety checks.
        kind: One of "story" | "episode" | "script".
        request_dict: Original request payload (optional, used for episode tasks).
    """

    from app.models.task import Task, TaskStatus

    should_close = False
    if db_session is None:
        from app.core.database import SessionLocal

        db = SessionLocal()
        should_close = True
    else:
        db = db_session
    try:
        task: Task | None = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        if task.status != TaskStatus.COMPLETED:
            return

        agent_run = _build_agent_run(db, task, user_id=user_id, kind=kind, request_dict=request_dict)
        if not agent_run:
            return

        _patch_task_parameters(db, task, {"agent_run": agent_run})
    finally:
        if should_close:
            db.close()


def _patch_task_parameters(db, task, patch: Dict[str, Any]) -> None:
    base = _loads_task_parameters(task.parameters)
    merged = _deep_merge_dict(base, patch)
    task.parameters = json.dumps(merged, ensure_ascii=False)
    db.commit()


def _loads_task_parameters(raw: Optional[str]) -> Dict[str, Any]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _deep_merge_dict(base: Dict[str, Any], patch: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(base)
    for key, value in patch.items():
        existing = merged.get(key)
        if isinstance(existing, dict) and isinstance(value, dict):
            merged[key] = _deep_merge_dict(existing, value)
        else:
            merged[key] = value
    return merged


def _build_agent_run(
    db,
    task,
    *,
    user_id: int,
    kind: str,
    request_dict: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    if kind == "story":
        return _build_story_agent_run(db, task, user_id=user_id)
    if kind == "episode":
        return _build_episode_agent_run(db, task, user_id=user_id, request_dict=request_dict)
    if kind == "script":
        return _build_script_agent_run(db, task, user_id=user_id)
    return {}


def _safe_dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _parse_result_id(result_file_path: Optional[str], *, prefix: str) -> Optional[str]:
    if not result_file_path:
        return None
    if not result_file_path.startswith(prefix + ":"):
        return None
    return result_file_path.split(":", 1)[1]


def _build_story_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    from app.models.script import Story

    story_id_str = _parse_result_id(task.result_file_path, prefix="story")
    if not story_id_str:
        return {}
    try:
        story_id = int(story_id_str)
    except (TypeError, ValueError):
        return {}

    story: Story | None = (
        db.query(Story).filter(Story.id == story_id, Story.user_id == user_id).first()
    )
    if not story:
        return {}

    meta = _safe_dict(getattr(story, "extra_metadata", None))
    agent_run = _safe_dict(meta.get("agent_run"))
    prompt = getattr(story, "generation_prompt", None)
    if prompt:
        agent_run = {**agent_run, "prompt": prompt}
    agent_run["result_ref"] = {
        "story_id": story.id,
        "story_business_id": getattr(story, "business_id", None),
    }
    return agent_run


def _build_episode_agent_run(
    db,
    task,
    *,
    user_id: int,
    request_dict: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    from app.models.script import Episode, Story

    created_ids: list[int] = []
    episode_ids_str = _parse_result_id(task.result_file_path, prefix="episodes")
    if episode_ids_str:
        for token in episode_ids_str.split(","):
            token = (token or "").strip()
            if not token:
                continue
            try:
                created_ids.append(int(token))
            except (TypeError, ValueError):
                continue

    story_id = None
    if isinstance(request_dict, dict):
        try:
            story_id = int(request_dict.get("story_id")) if request_dict.get("story_id") is not None else None
        except (TypeError, ValueError):
            story_id = None

    outline_payload: Dict[str, Any] | None = None
    story: Story | None = None
    if story_id is not None:
        story = (
            db.query(Story).filter(Story.id == story_id, Story.user_id == user_id).first()
        )
    if story:
        story_meta = _safe_dict(getattr(story, "extra_metadata", None))
        outlines = _safe_dict(story_meta.get("episode_step_outlines"))
        outline_agent_run = _safe_dict(outlines.get("agent_run"))
        outline_prompt = outlines.get("prompt")
        if outline_prompt:
            outline_agent_run = {**outline_agent_run, "prompt": outline_prompt}
        if outline_agent_run:
            outline_payload = outline_agent_run

    episode_runs: List[Dict[str, Any]] = []
    if created_ids:
        episodes = (
            db.query(Episode)
            .join(Story, Episode.story_id == Story.id)
            .filter(Episode.id.in_(created_ids), Story.user_id == user_id)
            .all()
        )
        for ep in sorted(episodes, key=lambda e: (getattr(e, "episode_number", 0) or 0, e.id)):
            ep_meta = _safe_dict(getattr(ep, "extra_metadata", None))
            run = _safe_dict(ep_meta.get("agent_run"))
            prompt = getattr(ep, "generation_prompt", None)
            if prompt:
                run = {**run, "prompt": prompt}
            episode_runs.append(
                {
                    "episode_id": ep.id,
                    "episode_business_id": getattr(ep, "business_id", None),
                    "episode_number": getattr(ep, "episode_number", None),
                    **run,
                }
            )

    payload: Dict[str, Any] = {
        "result_ref": {
            "story_id": story_id,
            "episode_ids": created_ids,
        }
    }
    if outline_payload:
        payload["outline"] = outline_payload
    if episode_runs:
        payload["episodes"] = episode_runs
    return payload


def _build_script_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    from app.models.script import Episode, Script, Story

    script_id_str = _parse_result_id(task.result_file_path, prefix="script")
    if not script_id_str:
        return {}
    # task.result_file_path might be like "script:123:storyboard"
    script_id_token = script_id_str.split(":", 1)[0]
    try:
        script_id = int(script_id_token)
    except (TypeError, ValueError):
        return {}

    script: Script | None = (
        db.query(Script)
        .join(Episode, Script.episode_id == Episode.id)
        .join(Story, Episode.story_id == Story.id)
        .filter(Script.id == script_id, Story.user_id == user_id)
        .first()
    )
    if not script:
        return {}

    meta = _safe_dict(getattr(script, "extra_metadata", None))
    agent_run = _safe_dict(meta.get("agent_run"))
    prompt = getattr(script, "generation_prompt", None)
    if prompt:
        agent_run = {**agent_run, "prompt": prompt}
    agent_run["result_ref"] = {
        "script_id": script.id,
        "script_business_id": getattr(script, "business_id", None),
        "episode_id": getattr(script, "episode_id", None),
        "episode_business_id": getattr(script, "episode_business_id", None),
    }
    return agent_run
