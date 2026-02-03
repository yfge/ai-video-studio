from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from app.core.logging import get_logger
from app.prompts.templates import PromptTemplate
from app.services.validators.character_consistency_validator import (
    CharacterConsistencyValidator,
    CharacterProfile,
)
from app.services.validators.episode_quality_validator import EpisodeQualityValidator

from .episode_agent_episode import (
    dumps_episode_payload,
    generate_episodes_from_outlines,
)
from .episode_agent_outline import generate_step_outlines

try:  # pragma: no cover - optional dependency
    from langgraph.graph import END, StateGraph

    LANGGRAPH_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    END = "END"
    StateGraph = None  # type: ignore[assignment]
    LANGGRAPH_AVAILABLE = False

if TYPE_CHECKING:
    from .ai_service import AIService


@dataclass(slots=True)
class EpisodeGenerationCallbacks:
    """Optional hooks for streaming progress/persistence during agent execution."""

    on_progress: Callable[[str], Any] | None = None
    on_outline: Callable[[dict[str, Any], dict[str, Any]], Any] | None = None
    on_episode: Callable[[dict[str, Any], dict[str, Any]], Any] | None = None


async def _maybe_await(
    callback: Callable[..., Any] | None, *args: Any, **kwargs: Any
) -> Any:
    if not callback:
        return None
    result = callback(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


class EpisodeLangGraphAgent:
    """LangGraph-compatible episode generator with strict outline validation."""

    def __init__(self, service: "AIService") -> None:
        self.service = service
        self.logger = get_logger()
        self._character_validator = CharacterConsistencyValidator()
        self._quality_validator = EpisodeQualityValidator()

    def _build_character_profiles(
        self, characters: List[Dict[str, Any]]
    ) -> List[CharacterProfile]:
        """Convert character dicts to CharacterProfile objects."""
        profiles = []
        for char in characters:
            if not char.get("name"):
                continue
            profile = CharacterProfile(
                name=char.get("name", ""),
                aliases=char.get("aliases", []),
                role_type=char.get("role_type") or char.get("role"),
                gender=char.get("gender"),
                age=char.get("age"),
                personality=char.get("personality", []),
                appearance=char.get("appearance") or char.get("description"),
            )
            profiles.append(profile)
        return profiles

    def _validate_episode_characters(
        self,
        episodes: List[Dict[str, Any]],
        story_characters: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate that episode characters are consistent with story characters.

        Returns validation results dict with:
        - character_validation_passed: bool
        - character_validation_results: list of validation results
        - character_warnings: list of warning messages
        """
        results: Dict[str, Any] = {
            "character_validation_passed": True,
            "character_validation_results": [],
            "character_warnings": [],
        }

        # Build profiles from story characters
        profiles = self._build_character_profiles(story_characters)
        if not profiles:
            results["character_warnings"].append("No story characters to validate against")
            return results

        self._character_validator = CharacterConsistencyValidator()
        self._character_validator.register_profiles(profiles)

        # Validate each episode
        for episode in episodes:
            ep_num = episode.get("episode_number", "?")

            # Check episode summary/description for unknown characters
            content_to_check = []
            if episode.get("summary"):
                content_to_check.append(episode["summary"])
            if episode.get("description"):
                content_to_check.append(episode["description"])
            if episode.get("plot_points"):
                content_to_check.extend(
                    str(p) for p in episode["plot_points"] if p
                )

            if content_to_check:
                text_results = self._character_validator.validate_names_in_text(
                    "\n".join(content_to_check)
                )
                for r in text_results:
                    r_dict = r.to_dict()
                    r_dict["episode_number"] = ep_num
                    results["character_validation_results"].append(r_dict)
                    if r.severity.value == "warning":
                        results["character_warnings"].append(
                            f"Episode {ep_num}: {r.message}"
                        )

            # Check episode-specific characters if present
            ep_chars = episode.get("characters", [])
            if isinstance(ep_chars, list):
                for char in ep_chars:
                    if isinstance(char, dict):
                        name = char.get("name") or char.get("character_name")
                        if not name:
                            continue

                        canonical = self._character_validator.resolve_name(name)
                        if not canonical:
                            results["character_warnings"].append(
                                f"Episode {ep_num}: Unknown character '{name}'"
                            )
                            results["character_validation_passed"] = False

        return results

    def _validate_episode_quality(
        self,
        episodes: List[Dict[str, Any]],
        story_characters: List[Dict[str, Any]],
        continuity_ledger: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validate episode quality including arcs, tension, and foreshadowing.

        Returns validation results dict with:
        - episode_quality_passed: bool
        - episode_quality_result: dict with analysis
        - episode_quality_warnings: list of warning messages
        """
        results: Dict[str, Any] = {
            "episode_quality_passed": True,
            "episode_quality_result": {},
            "episode_quality_warnings": [],
        }

        quality_result = self._quality_validator.validate(
            episodes, story_characters, continuity_ledger
        )

        results["episode_quality_passed"] = quality_result.passed
        results["episode_quality_result"] = quality_result.to_dict()

        for issue in quality_result.issues:
            if issue.severity.value in ("error", "warning"):
                results["episode_quality_warnings"].append(issue.message)

        return results

    async def generate(
        self,
        *,
        story: Dict[str, Any],
        episode_count: int,
        episode_duration: Optional[int],
        focus_characters: Optional[list[Dict[str, Any]]],
        plot_complexity: str,
        pacing: str,
        additional_requirements: Optional[str],
        style_preferences: Optional[list[str]],
        model: Optional[str],
        prefer_provider: Optional[str],
        temperature: float,
        callbacks: EpisodeGenerationCallbacks | None = None,
    ) -> Optional[Dict[str, Any]]:
        if not LANGGRAPH_AVAILABLE or not getattr(self.service, "ai_manager", None):
            return None

        async def _progress(message: str) -> None:
            await _maybe_await(callbacks.on_progress if callbacks else None, message)

        outline_result = await generate_step_outlines(
            ai_manager=self.service.ai_manager,
            story=story,
            episode_count=episode_count,
            episode_duration=episode_duration,
            focus_characters=focus_characters or [],
            plot_complexity=plot_complexity,
            pacing=pacing,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences or [],
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
            progress=_progress,
        )

        reasoning = outline_result.reasoning
        if outline_result.error or not outline_result.step_outlines:
            return {
                "error": outline_result.error or "outline_invalid",
                "reasoning": reasoning + [outline_result.error or "outline_invalid"],
            }

        await _maybe_await(
            callbacks.on_outline if callbacks else None,
            outline_result.step_outlines,
            {
                "prompt": outline_result.prompt,
                "raw": outline_result.raw_text,
                "provider": outline_result.provider,
                "model": outline_result.model,
                "usage": outline_result.usage,
                "reasoning": reasoning,
                "generation_method": "langgraph_episode_step_outline",
            },
        )

        async def _emit_episode(
            episode_obj: Dict[str, Any], meta: Dict[str, Any]
        ) -> None:
            await _maybe_await(
                callbacks.on_episode if callbacks else None, episode_obj, meta
            )

        episode_result = await generate_episodes_from_outlines(
            ai_manager=self.service.ai_manager,
            story=story,
            step_outlines=outline_result.step_outlines,
            episode_count=episode_count,
            episode_duration=episode_duration,
            focus_characters=focus_characters or [],
            plot_complexity=plot_complexity,
            pacing=pacing,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences or [],
            model=model,
            prefer_provider=prefer_provider,
            temperature=temperature,
            progress=_progress,
            emit_episode=_emit_episode,
            reasoning=reasoning,
            initial_provider=outline_result.provider,
            initial_model=outline_result.model,
            initial_usage=outline_result.usage,
        )

        # Run character consistency validation
        story_characters = story.get("characters", [])
        char_validation = self._validate_episode_characters(
            episode_result.episodes, story_characters
        )
        if char_validation["character_warnings"]:
            self.logger.warning(
                "Episode character validation warnings",
                extra={"warnings": char_validation["character_warnings"]},
            )

        # Run episode quality validation
        quality_validation = self._validate_episode_quality(
            episode_result.episodes,
            story_characters,
            episode_result.continuity_ledger,
        )
        if quality_validation["episode_quality_warnings"]:
            self.logger.warning(
                "Episode quality validation warnings",
                extra={"warnings": quality_validation["episode_quality_warnings"]},
            )

        return {
            "content": dumps_episode_payload(episode_result.episodes),
            "normalized": {"episodes": episode_result.episodes},
            "step_outlines": outline_result.step_outlines,
            "step_outlines_raw": outline_result.raw_text,
            "step_outline_prompt": outline_result.prompt,
            "prompt": outline_result.prompt,
            "continuity_ledger": episode_result.continuity_ledger,
            "generation_method": "langgraph_episode_step_outline",
            "template_used": PromptTemplate.EPISODE_FROM_OUTLINE.value,
            "provider_used": episode_result.provider,
            "model_used": episode_result.model,
            "usage": episode_result.usage,
            "reasoning": episode_result.reasoning + ["episodes_done"],
            **char_validation,
            **quality_validation,
        }
