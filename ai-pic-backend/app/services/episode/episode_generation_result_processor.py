from __future__ import annotations

import json
from typing import Any, Dict

import anyio
from app.models.script import Story
from app.repositories.episode_repository import list_episodes_by_ids
from app.schemas.generation_requests import EpisodeGenerationRequest
from app.services.ai_service import ai_service
from app.services.episode.episode_generation_persistence import (
    persist_step_outline_beats,
)
from app.services.episode.episode_generation_utils import (
    build_agent_run_info,
    build_stub_episodes_from_outlines,
    parse_step_outlines,
    persist_story_outlines,
)
from app.services.episode.episode_stream_persistence import persist_episode_record
from app.services.narrative_quality_gate import enforce_episode_quality_gate_with_repair
from app.utils.json_utils import extract_json_block
from sqlalchemy.orm import Session


def process_episode_generation_result(
    *,
    db: Session,
    result: Dict[str, Any],
    story: Story,
    story_data: Dict[str, Any],
    request: EpisodeGenerationRequest,
    created_ids: list[int],
    progress_fn,
) -> None:
    progress_fn("剧集生成：模型返回结果解析中")
    content = (
        result.get("normalized") if isinstance(result, dict) else None
    ) or extract_json_block(result.get("content") if isinstance(result, dict) else None)
    episodes_data = content.get("episodes", []) if content else []

    agent_run = build_agent_run_info(result)
    used_context = story_data.get("context_pack")
    if used_context:
        agent_run["used_context"] = used_context

    raw_step_outlines = result.get("step_outlines") or result.get("step_outlines_raw")
    episode_count = request.episode_count or len(episodes_data) or 1
    parsed_outlines = (
        parse_step_outlines(raw_step_outlines, episode_count)
        if raw_step_outlines
        else None
    )
    if parsed_outlines:
        persist_story_outlines(
            story,
            parsed_outlines,
            prompt=result.get("step_outline_prompt"),
            agent_run=agent_run,
        )
        progress_fn("剧集生成：大纲校验通过，写入故事信息")
        db.refresh(story)

    if not episodes_data and parsed_outlines:
        episodes_data = build_stub_episodes_from_outlines(
            parsed_outlines, episode_count
        )
        result = {
            **result,
            "normalized": {"episodes": episodes_data},
            "content": json.dumps({"episodes": episodes_data}, ensure_ascii=False),
        }
        agent_run = {**agent_run, "fallback_from_outline": True}
        progress_fn("模型输出无效，使用大纲兜底生成")

    if episodes_data:
        result = {
            **result,
            "normalized": {"episodes": episodes_data},
            "content": json.dumps({"episodes": episodes_data}, ensure_ascii=False),
        }
    if not isinstance(result.get("quality_gate"), dict) or not result[
        "quality_gate"
    ].get("passed"):

        async def _quality_gate_call() -> Dict[str, Any]:
            return await _run_quality_gate(
                result=result,
                story_data=story_data,
                request=request,
            )

        result = anyio.run(_quality_gate_call)
        content = result.get("normalized") if isinstance(result, dict) else None
        episodes_data = content.get("episodes", []) if content else []

    quality_gate = result.get("quality_gate") if isinstance(result, dict) else None
    if isinstance(quality_gate, dict):
        agent_run["quality_gate"] = quality_gate
    if not episodes_data:
        raise RuntimeError("AI生成内容格式错误")
    if len(episodes_data) < episode_count:
        raise RuntimeError(
            f"AI生成剧集数量不足：期望 {episode_count} 集，实际 {len(episodes_data)} 集"
        )

    for idx, ep_data in enumerate(episodes_data[:episode_count], start=1):
        ep, created = persist_episode_record(
            db=db,
            request=request,
            story=story,
            story_data=story_data,
            episode_data=ep_data,
            fallback_number=idx,
            result=result,
            agent_run=agent_run,
            progress_fn=progress_fn,
        )
        if ep and created:
            created_ids.append(ep.id)

    if parsed_outlines and created_ids:
        outline_episodes = list_episodes_by_ids(db, created_ids)
        if outline_episodes:
            persist_step_outline_beats(
                db=db,
                story=story,
                step_outlines=parsed_outlines,
                created_episodes=outline_episodes,
                agent_run=agent_run,
                result=result,
            )


async def _run_quality_gate(
    *,
    result: Dict[str, Any],
    story_data: Dict[str, Any],
    request: EpisodeGenerationRequest,
) -> Dict[str, Any]:
    prefer_provider = None
    model_id = request.model
    if model_id and ":" in model_id:
        prefer_provider, model_id = model_id.split(":", 1)
    return await enforce_episode_quality_gate_with_repair(
        ai_manager=getattr(ai_service, "ai_manager", None),
        result=result,
        story=story_data,
        episode_count=request.episode_count,
        model=model_id,
        prefer_provider=prefer_provider,
        temperature=request.temperature or 0.3,
        require_episode_contract=request.generation_mode == "production",
    )
