from __future__ import annotations

import re
from typing import Callable, TypeVar

from app.models.script import Episode, Story
from app.models.user import User
from app.repositories.production_canvas_context_repository import (
    ProductionCanvasContextRepository,
)
from app.repositories.script_repository import EpisodeRepository
from app.repositories.virtual_ip_repository import VirtualIPRepository
from app.schemas.production_canvas import ProductionCanvasPlanRequest
from app.services.production_canvas.asset_selection import (
    CanvasAssetSelection,
    clean_list,
    score_text_match,
)
from sqlalchemy.orm import Session

T = TypeVar("T")
EPISODE_NUMBER = re.compile(r"(?:第\s*)?(\d+)\s*集", re.IGNORECASE)


def _owner_id(user: User) -> int | None:
    return None if user.is_admin or user.is_superuser else int(user.id)


def _episode_number(prompt: str) -> int | None:
    match = EPISODE_NUMBER.search(prompt)
    return int(match.group(1)) if match else None


def _unique_best(items: list[T], score: Callable[[T], int]) -> T | None:
    scored = [(score(item), item) for item in items]
    matched = [(value, item) for value, item in scored if value > 0]
    if not matched:
        return items[0] if len(items) == 1 else None
    best_score = max(value for value, _ in matched)
    best = [item for value, item in matched if value == best_score]
    return best[0] if len(best) == 1 else None


def _choose_story(prompt: str, stories: list[Story]) -> Story | None:
    return _unique_best(
        stories,
        lambda story: score_text_match(
            prompt,
            story.title,
            clean_list(story.tags),
        ),
    )


def _choose_episode(prompt: str, episodes: list[Episode]) -> Episode | None:
    number = _episode_number(prompt)
    if number is not None:
        matched = [item for item in episodes if item.episode_number == number]
        return matched[0] if len(matched) == 1 else None
    normalized = prompt.casefold()
    matched = [
        item for item in episodes if item.title and item.title.casefold() in normalized
    ]
    if len(matched) == 1:
        return matched[0]
    return episodes[0] if len(episodes) == 1 else None


def derive_story_ip(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
) -> int | None:
    if request.virtual_ip_id is not None or request.story_id is None:
        return request.virtual_ip_id
    ids = ProductionCanvasContextRepository(db).list_story_virtual_ip_ids(
        request.story_id
    )
    repo = VirtualIPRepository(db)
    accessible = [
        ip for ip_id in ids if (ip := repo.find_accessible_by_id(ip_id, user=user))
    ]
    selected = _unique_best(
        accessible,
        lambda ip: score_text_match(
            request.prompt,
            ip.name,
            clean_list(ip.tags),
        ),
    )
    return int(selected.id) if selected else None


def resolve_prompt_story_episode(
    db: Session,
    user: User,
    request: ProductionCanvasPlanRequest,
) -> ProductionCanvasPlanRequest:
    story_id = request.story_id
    number = _episode_number(request.prompt)
    if story_id is None:
        stories = ProductionCanvasContextRepository(db).list_stories(
            user,
            virtual_ip_id=request.virtual_ip_id,
            episode_number=number,
        )
        story = _choose_story(request.prompt, stories)
        story_id = int(story.id) if story else None
    episode_id = request.episode_id
    if story_id is not None and episode_id is None:
        episodes = EpisodeRepository(db).list_by_story(
            story_id,
            user_id=_owner_id(user),
        )
        episode = _choose_episode(request.prompt, episodes)
        episode_id = int(episode.id) if episode else None
    return request.model_copy(update={"story_id": story_id, "episode_id": episode_id})


def selected_asset_context(
    request: ProductionCanvasPlanRequest,
    assets: CanvasAssetSelection,
) -> ProductionCanvasPlanRequest:
    updates = {}
    if request.virtual_ip_id is None and assets.selected.virtual_ips:
        updates["virtual_ip_id"] = int(assets.selected.virtual_ips[0].id)
    if request.environment_id is None and assets.selected.environments:
        updates["environment_id"] = int(assets.selected.environments[0].id)
    return request.model_copy(update=updates) if updates else request
