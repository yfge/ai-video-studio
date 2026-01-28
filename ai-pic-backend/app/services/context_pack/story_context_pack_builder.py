from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from app.models.script import Episode, StoryCharacter
from app.models.virtual_ip import VirtualIP
from app.schemas.context_pack import (
    CharacterCard,
    ContextPackBudget,
    ContextPackMeta,
    EpisodeSummary,
    StoryContextPack,
    StoryOutlineCore,
    StorySetting,
)
from app.services.context_pack.budgeting import apply_story_pack_budget, truncate_text
from sqlalchemy.orm import Session


def _not_deleted(query, model):
    return query.filter(model.is_deleted.is_(False))


def build_story_context_pack(
    *,
    db: Session,
    story_id: int,
    story_snapshot: Dict[str, Any],
    continuity_ledger: Optional[Dict[str, Any]],
    generation_params: Optional[Dict[str, Any]] = None,
    budget: Optional[ContextPackBudget] = None,
) -> Dict[str, Any]:
    """Build a StoryContextPack from DB + an already-merged story snapshot.

    Note: token budgeting is approximate (char-based) to stay lightweight and
    avoid extra dependencies.
    """
    budget = budget or ContextPackBudget()
    trims: list[str] = []

    # Character cards from StoryCharacter <-> VirtualIP.
    rows = (
        _not_deleted(db.query(StoryCharacter), StoryCharacter)
        .join(
            VirtualIP,
            (StoryCharacter.virtual_ip_id == VirtualIP.id)
            & VirtualIP.is_deleted.is_(False),
        )
        .filter(StoryCharacter.story_id == story_id)
        .order_by(StoryCharacter.importance.desc(), StoryCharacter.id.asc())
        .all()
    )
    cards: list[CharacterCard] = []
    for sc in rows[: budget.max_character_cards]:
        vip = getattr(sc, "virtual_ip", None)
        if not vip:
            continue
        cards.append(
            CharacterCard(
                id=vip.id,
                name=vip.name,
                role_type=sc.role_type,
                description=truncate_text(vip.description, budget.max_field_chars),
                background_story=truncate_text(
                    vip.background_story, budget.max_field_chars
                ),
                biography=truncate_text(vip.biography, budget.max_field_chars),
                style_prompt=truncate_text(vip.style_prompt, budget.max_field_chars),
                voice_config=(
                    vip.voice_config
                    if isinstance(vip.voice_config, dict) and vip.voice_config
                    else None
                ),
            )
        )

    # Recent episode summaries (non-deleted).
    recent_rows = (
        _not_deleted(db.query(Episode), Episode)
        .filter(Episode.story_id == story_id)
        .order_by(Episode.episode_number.asc())
        .all()
    )
    recent_eps: list[EpisodeSummary] = []
    max_recent = budget.max_recent_episode_summaries
    if max_recent > 0:
        for ep in recent_rows[-max_recent:]:
            extra = ep.extra_metadata if isinstance(ep.extra_metadata, dict) else {}
            summary = extra.get("episode_summary") or ep.summary
            recent_eps.append(
                EpisodeSummary(
                    episode_id=ep.id,
                    episode_number=ep.episode_number,
                    title=ep.title,
                    summary=truncate_text(summary, budget.max_field_chars),
                )
            )

    if not isinstance(generation_params, dict):
        generation_params = (
            story_snapshot.get("generation_params")
            if isinstance(story_snapshot.get("generation_params"), dict)
            else {}
        )
    style_preferences = generation_params.get("style_preferences")
    content_restrictions = generation_params.get("content_restrictions")

    pack = StoryContextPack(
        meta=ContextPackMeta(
            version="v1",
            estimated_chars=0,
            budget=budget,
            trims=[],
        ),
        story_id=story_id,
        story_title=str(story_snapshot.get("title") or ""),
        story_format=story_snapshot.get("story_format"),
        genre=story_snapshot.get("genre"),
        default_aspect_ratio=story_snapshot.get("default_aspect_ratio"),
        style_preferences=(
            [str(item) for item in (style_preferences or []) if str(item).strip()]
            if isinstance(style_preferences, list)
            else []
        ),
        content_restrictions=(
            [str(item) for item in (content_restrictions or []) if str(item).strip()]
            if isinstance(content_restrictions, list)
            else []
        ),
        marketing_meta={
            k: story_snapshot.get(k)
            for k in [
                "market_region",
                "micro_genre",
                "pacing_template",
                "hook_plan",
                "twist_density",
                "cliffhanger_plan",
                "ad_snippets",
            ]
            if story_snapshot.get(k) is not None
        },
        outline=StoryOutlineCore(
            premise=truncate_text(
                story_snapshot.get("premise"), budget.max_field_chars
            ),
            synopsis=truncate_text(
                story_snapshot.get("synopsis"), budget.max_field_chars
            ),
            main_conflict=truncate_text(
                story_snapshot.get("main_conflict"), budget.max_field_chars
            ),
            resolution=truncate_text(
                story_snapshot.get("resolution"), budget.max_field_chars
            ),
        ),
        setting=StorySetting(
            setting_time=truncate_text(
                story_snapshot.get("setting_time"), budget.max_field_chars
            ),
            setting_location=truncate_text(
                story_snapshot.get("setting_location"), budget.max_field_chars
            ),
            world_building=truncate_text(
                story_snapshot.get("world_building"), budget.max_field_chars
            ),
        ),
        character_cards=cards,
        character_relationships=(
            story_snapshot.get("character_relationships")
            if isinstance(story_snapshot.get("character_relationships"), dict)
            else {}
        ),
        continuity_ledger=continuity_ledger,
        recent_episodes=recent_eps,
    )

    dumped = pack.model_dump()
    shrunken, shrink_trims = apply_story_pack_budget(dumped, budget)
    trims.extend(shrink_trims)

    estimated = len(str(shrunken))
    try:
        # better estimate (compact JSON)
        import json

        estimated = len(json.dumps(shrunken, ensure_ascii=False, separators=(",", ":")))
    except Exception:
        pass

    meta = shrunken.get("meta") if isinstance(shrunken.get("meta"), dict) else {}
    meta["estimated_chars"] = estimated
    meta.setdefault("trims", [])
    if isinstance(meta["trims"], list):
        meta["trims"].extend(trims)
    meta.setdefault("generated_at", datetime.utcnow().isoformat() + "Z")
    shrunken["meta"] = meta

    return shrunken
