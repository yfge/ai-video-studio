from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.repositories.script_repository import (
    EpisodeRepository,
    ScriptRepository,
    StoryRepository,
)
from app.services.task_agent_run.timeline_refs import domain_ref_for_script
from app.services.task_agent_run.utils import parse_result_id, safe_dict


def build_story_agent_run(db, task, *, user_id: int) -> Dict[str, Any]:
    story_id_str = parse_result_id(task.result_file_path, prefix="story")
    if not story_id_str:
        return {}
    try:
        story_id = int(story_id_str)
    except (TypeError, ValueError):
        return {}

    story = StoryRepository(db).get_by_user(story_id, user_id=user_id)
    if not story:
        return {}

    meta = safe_dict(getattr(story, "extra_metadata", None))
    agent_run = safe_dict(meta.get("agent_run"))
    prompt = getattr(story, "generation_prompt", None)
    if prompt:
        agent_run = {**agent_run, "prompt": prompt}
    source_novel = meta.get("source_novel")
    if isinstance(source_novel, dict):
        agent_run = {**agent_run, "source_novel": source_novel}
    agent_run["result_ref"] = {
        "story_id": story.id,
        "story_business_id": getattr(story, "business_id", None),
    }
    return agent_run


def build_episode_agent_run(
    db,
    task,
    *,
    user_id: int,
    story_id: int | None,
    created_episode_ids: list[int],
) -> Dict[str, Any]:
    outline_payload: Dict[str, Any] | None = None
    story = None
    if story_id is not None:
        story = StoryRepository(db).get_by_user(story_id, user_id=user_id)
    if story:
        story_meta = safe_dict(getattr(story, "extra_metadata", None))
        outlines = safe_dict(story_meta.get("episode_step_outlines"))
        outline_agent_run = safe_dict(outlines.get("agent_run"))
        outline_prompt = outlines.get("prompt")
        if outline_prompt:
            outline_agent_run = {**outline_agent_run, "prompt": outline_prompt}
        if outline_agent_run:
            outline_payload = outline_agent_run

    episode_runs: List[Dict[str, Any]] = []
    if created_episode_ids:
        repository = EpisodeRepository(db)
        episodes = [
            episode
            for episode_id in created_episode_ids
            if (
                episode := repository.get_with_story(
                    episode_id=episode_id,
                    user_id=user_id,
                )
            )
        ]
        for ep in sorted(
            episodes, key=lambda e: (getattr(e, "episode_number", 0) or 0, e.id)
        ):
            ep_meta = safe_dict(getattr(ep, "extra_metadata", None))
            run = safe_dict(ep_meta.get("agent_run"))
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
            "episode_ids": created_episode_ids,
        }
    }
    if outline_payload:
        payload["outline"] = outline_payload
    if episode_runs:
        payload["episodes"] = episode_runs
    return payload


def build_script_run(db, task, *, user_id: int, script_id: int) -> Dict[str, Any]:
    script = ScriptRepository(db).get_with_relations(
        script_id=script_id,
        user_id=user_id,
    )
    if not script:
        return {}

    meta = safe_dict(getattr(script, "extra_metadata", None))
    agent_run = safe_dict(meta.get("agent_run"))
    prompt = getattr(script, "generation_prompt", None)
    if prompt:
        agent_run = {**agent_run, "prompt": prompt}
    agent_run["result_ref"] = {
        "script_id": script.id,
        "script_business_id": getattr(script, "business_id", None),
        "episode_id": getattr(script, "episode_id", None),
        "episode_business_id": getattr(script, "episode_business_id", None),
        **domain_ref_for_script(db, script),
    }
    return agent_run


def parse_episode_task_ids(
    task, *, request_dict: Optional[Dict[str, Any]]
) -> tuple[int | None, list[int]]:
    created_ids: list[int] = []
    episode_ids_str = parse_result_id(task.result_file_path, prefix="episodes")
    if episode_ids_str:
        for token in episode_ids_str.split(","):
            token = (token or "").strip()
            if not token:
                continue
            try:
                created_ids.append(int(token))
            except (TypeError, ValueError):
                continue

    story_id: int | None = None
    if isinstance(request_dict, dict):
        try:
            raw = request_dict.get("story_id")
            story_id = int(raw) if raw is not None else None
        except (TypeError, ValueError):
            story_id = None

    return story_id, created_ids
