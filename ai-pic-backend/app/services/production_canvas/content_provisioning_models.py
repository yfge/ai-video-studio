from __future__ import annotations

import math

from app.models.script import Episode, Story, StoryCharacter
from app.models.user import User
from app.schemas.production_canvas_content import ProductionCanvasPlanningDraft
from sqlalchemy.orm import Session


def create_story(
    db: Session,
    user: User,
    planning: ProductionCanvasPlanningDraft,
) -> Story:
    brief = planning.brief
    content = planning.content_plan
    duration_minutes = max(
        1,
        math.ceil((brief.video_spec.duration_seconds or 180) / 60),
    )
    story = Story(
        user_id=user.id,
        title=content.title,
        story_format="short_drama",
        genre=brief.intent.genre or "剧情",
        theme=content.theme or "、".join(brief.video_spec.visual_style) or None,
        target_audience=brief.intent.target_audience,
        duration_minutes=duration_minutes,
        default_aspect_ratio=(
            brief.video_spec.aspect_ratio
            if brief.video_spec.aspect_ratio in {"9:16", "16:9"}
            else "9:16"
        ),
        premise=content.premise,
        synopsis=content.synopsis,
        main_conflict=content.main_conflict,
        main_characters=[item.model_dump() for item in content.characters],
        setting_location=(
            content.environments[0].name if content.environments else None
        ),
        world_building=content.season_arc,
        generation_prompt=brief.source_prompt,
        generation_params={"source": "production_canvas_content_plan"},
        tags=["production-canvas", "content-plan-v1"],
        extra_metadata=planning_metadata(planning),
    )
    db.add(story)
    db.flush()
    return story


def create_episode(story, planning, episode_plan) -> Episode:
    brief = planning.brief
    duration_minutes = max(
        1,
        math.ceil(
            (brief.video_spec.duration_seconds or (story.duration_minutes or 3) * 60)
            / 60
        ),
    )
    return Episode(
        story_id=story.id,
        story_business_id=story.business_id,
        episode_number=episode_plan.episode_number,
        title=episode_plan.title,
        summary=episode_plan.logline,
        plot_points=[
            {"description": beat, "timing": f"beat-{index}"}
            for index, beat in enumerate(episode_plan.beats, start=1)
        ],
        conflicts=[
            {
                "description": planning.content_plan.main_conflict,
                "intensity": "high",
            }
        ],
        duration_minutes=duration_minutes,
        aspect_ratio=(
            brief.video_spec.aspect_ratio
            if brief.video_spec.aspect_ratio in {"9:16", "16:9"}
            else story.default_aspect_ratio
        ),
        generation_prompt=brief.source_prompt,
        generation_params={"source": "production_canvas_content_plan"},
        tags=["production-canvas", "content-plan-v1"],
        extra_metadata={
            **planning_metadata(planning),
            "episode_plan": episode_plan.model_dump(),
        },
    )


def planning_metadata(planning: ProductionCanvasPlanningDraft) -> dict:
    return {
        "source": "production_canvas",
        "production_brief": planning.brief.model_dump(),
        "content_plan": planning.content_plan.model_dump(),
        "continuity_ledger": {
            "rules": planning.content_plan.continuity_rules,
            "future_threads": planning.content_plan.future_threads,
        },
    }


def ensure_story_character(db: Session, story: Story, virtual_ip) -> None:
    if any(
        int(character.virtual_ip_id) == int(virtual_ip.id) and not character.is_deleted
        for character in story.story_characters or []
    ):
        return
    db.add(
        StoryCharacter(
            story_id=story.id,
            story_business_id=story.business_id,
            virtual_ip_id=virtual_ip.id,
            virtual_ip_business_id=virtual_ip.business_id,
            character_name=virtual_ip.name,
            role_type="protagonist",
            importance=5,
            background=virtual_ip.description,
        )
    )
