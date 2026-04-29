"""
Script generation service for AI-powered script creation.

Handles AI generation, content parsing, and normalization for scripts.
"""

from typing import Any, Dict, List, Optional

from app.core.exceptions import GenerationFailedError, NotFoundError
from app.core.logging import get_logger
from app.models.script import Episode, Script, Story
from app.models.user import User
from app.prompts.manager import PromptManager
from app.prompts.templates import PromptTemplate
from app.repositories.script_repository import EpisodeRepository, StoryRepository
from app.services.ai.script_text import build_script_text
from app.services.ai_service import ai_service
from app.services.narrative_quality_gate import (
    NarrativeQualityGateError,
    enforce_script_quality_gate_with_repair,
)
from app.services.script.scene_utils import to_int
from app.services.script.script_character_policy import enforce_script_character_policy
from app.services.script.script_utils import (
    build_character_profiles,
    build_episode_data,
    build_story_data,
    collect_previous_episode_summaries,
)
from app.utils.json_utils import extract_json_block
from app.utils.script_parser import extract_script_structure
from sqlalchemy.orm import Session

logger = get_logger()


class ScriptGenerator:
    """
    Service for AI-powered script generation.

    Handles prompt building, AI service calls, and content normalization.
    """

    def __init__(self, session: Session):
        """Initialize generator with database session."""
        self.session = session
        self.episode_repo = EpisodeRepository(session)
        self.story_repo = StoryRepository(session)
        self.prompt_manager = PromptManager()

    def _get_user_id_filter(self, user: User) -> Optional[int]:
        """Get user ID for filtering, None for admins."""
        if user.is_admin or user.is_superuser:
            return None
        return user.id

    async def generate_script(
        self,
        episode_id: int,
        user: User,
        format_type: str = "screenplay",
        language: str = "zh-CN",
        model: Optional[str] = None,
        dialogue_style: Optional[str] = None,
        scene_detail_level: Optional[str] = None,
        template_style: str = "commercial_vertical_drama",
        target_chars_per_episode: int = 1300,
        quality_threshold: float = 9.0,
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
        temperature: float = 0.7,
    ) -> Script:
        """
        Generate a script using AI.

        Args:
            episode_id: Episode ID to generate script for
            user: Current user
            format_type: Script format type
            language: Script language
            model: AI model to use
            dialogue_style: Dialogue style preference
            scene_detail_level: Scene detail level
            template_style: Output text template style
            target_chars_per_episode: Target episode script characters
            quality_threshold: Deterministic lint pass threshold
            additional_requirements: Additional requirements
            style_preferences: Style preferences list
            temperature: Generation temperature

        Returns:
            Generated Script instance

        Raises:
            NotFoundError: If episode not found
            GenerationFailedError: If AI generation fails
        """
        # Get episode and story
        user_id = self._get_user_id_filter(user)
        episode = self.episode_repo.get_with_story(
            episode_id=episode_id, user_id=user_id
        )
        if not episode:
            raise NotFoundError("剧集", episode_id)

        story = episode.story
        if not story:
            raise NotFoundError("故事", episode.story_id)

        # Build context data
        episode_data, story_data = self._build_context(episode, story)

        # Parse model and provider
        prefer_provider = None
        model_id = model
        if model_id and ":" in model_id:
            prefer_provider, model_id = model_id.split(":", 1)

        # Call AI service
        result = await ai_service.generate_script(
            episode=episode_data,
            story=story_data,
            format_type=format_type,
            language=language,
            dialogue_style=dialogue_style,
            scene_detail_level=scene_detail_level,
            template_style=template_style,
            target_chars_per_episode=target_chars_per_episode,
            quality_threshold=quality_threshold,
            additional_requirements=additional_requirements,
            style_preferences=style_preferences,
            model=model_id,
            prefer_provider=prefer_provider,
            temperature=temperature,
        )

        if not result:
            raise GenerationFailedError("AI剧本生成失败")

        # Parse and normalize content
        ai_content = self._parse_ai_result(result)
        ai_content = self._normalize_content(
            ai_content,
            format_type,
            language,
            episode_data.get("scenes"),
            episode_number=episode.episode_number,
            template_style=template_style,
            target_chars_per_episode=target_chars_per_episode,
            title=episode.title,
        )

        # Extract content parts
        script_content = ai_content.get("content", "")
        scenes = ai_content.get("scenes", [])
        dialogues = ai_content.get("dialogues", [])
        stage_directions = ai_content.get("stage_directions", [])

        # Populate missing dialogues/stage directions
        dialogues, stage_directions = self._populate_missing_parts(
            scenes, dialogues, stage_directions, story
        )
        if not ai_content.get("dialogues") or not ai_content.get("stage_directions"):
            script_content = build_script_text(
                scenes,
                dialogues,
                stage_directions,
                format_type=format_type,
                language=language,
                episode_number=episode.episode_number,
                template_style=template_style,
                target_chars_per_episode=target_chars_per_episode,
                title=episode.title,
            )
            ai_content["content"] = script_content
        try:
            result, ai_content, _quality_gate = (
                await enforce_script_quality_gate_with_repair(
                    ai_manager=getattr(ai_service, "ai_manager", None),
                    result=result,
                    content={
                        **ai_content,
                        "content": script_content,
                        "scenes": scenes,
                        "dialogues": dialogues,
                        "stage_directions": stage_directions,
                    },
                    story=story_data,
                    story_model=story,
                    episode_id=episode_id,
                    db=self.session,
                    model=model_id,
                    prefer_provider=prefer_provider,
                    temperature=temperature,
                    lint_threshold=quality_threshold,
                    target_chars_per_episode=target_chars_per_episode,
                )
            )
        except NarrativeQualityGateError as exc:
            raise GenerationFailedError(
                "剧本",
                f"质量校验失败: {exc}",
                context={"quality_gate": exc.quality_gate},
            ) from exc
        script_content = ai_content.get("content", "")
        scenes = ai_content.get("scenes", [])
        dialogues = ai_content.get("dialogues", [])
        stage_directions = ai_content.get("stage_directions", [])

        policy = enforce_script_character_policy(
            story=story, scenes=scenes, dialogues=dialogues
        )
        if policy.unknown_names:
            raise GenerationFailedError(
                "检测到未注册角色，已阻断生成。"
                f" 未注册角色: {policy.unknown_names};"
                f" 已注册角色: {policy.canonical_names};"
                " 允许的泛化小角色: ['路人','店员','旁白']"
            )

        # Calculate statistics
        word_count = len(script_content.split()) if script_content else 0
        character_count = len(script_content) if script_content else 0
        page_count = max(1, character_count // 2000)

        # Build extra metadata
        extra_meta = self._build_extra_metadata(ai_content, result)

        # Create script
        db_script = Script(
            episode_id=episode_id,
            title=f"{episode.title} - 剧本",
            content=script_content,
            scenes=scenes,
            dialogues=dialogues,
            stage_directions=stage_directions,
            format_type=format_type,
            language=language,
            page_count=page_count,
            word_count=word_count,
            character_count=character_count,
            generation_prompt=result.get("prompt"),
            ai_model=result.get("generation_method"),
            generation_params={
                "dialogue_style": dialogue_style,
                "scene_detail_level": scene_detail_level,
                "template_style": template_style,
                "target_chars_per_episode": target_chars_per_episode,
                "quality_threshold": quality_threshold,
                "additional_requirements": additional_requirements,
                "style_preferences": style_preferences,
                "model": model,
                "temperature": temperature,
            },
            extra_metadata=extra_meta or None,
            status="draft",
        )

        self.session.add(db_script)
        self.session.commit()
        self.session.refresh(db_script)

        return db_script

    def preview_prompt(
        self,
        episode_id: int,
        user: User,
        format_type: str = "screenplay",
        language: str = "zh-CN",
        dialogue_style: Optional[str] = None,
        scene_detail_level: Optional[str] = None,
        template_style: str = "commercial_vertical_drama",
        target_chars_per_episode: int = 1300,
        quality_threshold: float = 9.0,
        additional_requirements: Optional[str] = None,
        style_preferences: Optional[List[str]] = None,
    ) -> str:
        """
        Preview the generation prompt without calling AI.

        Args:
            episode_id: Episode ID
            user: Current user
            format_type: Script format type
            language: Script language
            dialogue_style: Dialogue style
            scene_detail_level: Scene detail level
            additional_requirements: Additional requirements
            style_preferences: Style preferences

        Returns:
            Generated prompt string
        """
        user_id = self._get_user_id_filter(user)
        episode = self.episode_repo.get_with_story(
            episode_id=episode_id, user_id=user_id
        )
        if not episode:
            raise NotFoundError("剧集", episode_id)

        story = episode.story
        if not story:
            raise NotFoundError("故事", episode.story_id)

        episode_data, story_data = self._build_context(episode, story)

        variables = {
            "story": story_data,
            "episode": episode_data,
            "format_type": format_type,
            "language": language,
            "dialogue_style": dialogue_style,
            "scene_detail_level": scene_detail_level,
            "template_style": template_style,
            "target_chars_per_episode": target_chars_per_episode,
            "quality_threshold": quality_threshold,
            "additional_requirements": additional_requirements,
            "style_preferences": style_preferences or [],
        }

        return self.prompt_manager.render_prompt(
            PromptTemplate.SCRIPT_GENERATION.value, variables
        )

    def _build_context(
        self, episode: Episode, story: Story
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Build episode and story context data."""
        previous_summaries = collect_previous_episode_summaries(
            self.session, story.id, episode.episode_number
        )
        character_profiles = build_character_profiles(story)
        episode_data = build_episode_data(episode)
        story_data = build_story_data(
            story,
            previous_episode_summaries=previous_summaries,
            character_profiles=character_profiles,
        )
        return episode_data, story_data

    def _parse_ai_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI result into structured content."""
        raw_content = result.get("content")
        if isinstance(raw_content, dict):
            return raw_content

        parsed = extract_json_block(raw_content)
        if parsed:
            return parsed

        source_text = raw_content or ""
        extracted = extract_script_structure(source_text)
        return {
            "content": extracted.get("content", source_text),
            "scenes": extracted.get("scenes", []),
            "dialogues": extracted.get("dialogues", []),
            "stage_directions": extracted.get("stage_directions", []),
            "metadata": extracted.get("metadata", {}),
        }

    def _normalize_content(
        self,
        ai_content: Dict[str, Any],
        format_type: str,
        language: str,
        default_scenes: Optional[List[Dict[str, Any]]] = None,
        *,
        episode_number: Optional[int] = None,
        template_style: Optional[str] = None,
        target_chars_per_episode: Optional[int] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Normalize AI content to expected format."""
        normalized = dict(ai_content or {})
        fallback_scenes = default_scenes or []

        # Normalize scenes
        raw_scenes = normalized.get("scenes")
        if not isinstance(raw_scenes, list) or len(raw_scenes) == 0:
            raw_scenes = fallback_scenes

        scenes = self._normalize_scenes(raw_scenes)
        normalized["scenes"] = scenes

        # Normalize dialogues and stage directions
        normalized["dialogues"] = self._normalize_dialogues(
            normalized.get("dialogues", []), scenes
        )
        normalized["stage_directions"] = self._normalize_stage_directions(
            normalized.get("stage_directions", []), scenes
        )

        # Ensure content text exists
        content_value = normalized.get("content")
        if isinstance(content_value, dict):
            content_text = content_value.get("content") or ""
        else:
            content_text = content_value or ""

        if not content_text:
            content_text = build_script_text(
                scenes,
                normalized["dialogues"],
                normalized["stage_directions"],
                format_type=format_type,
                language=language,
                episode_number=episode_number,
                template_style=template_style,
                target_chars_per_episode=target_chars_per_episode,
                title=title,
            )
        normalized["content"] = content_text

        return normalized

    def _normalize_scenes(self, raw_scenes: List) -> List[Dict[str, Any]]:
        """Normalize scenes list."""
        scenes = []
        for idx, scene in enumerate(raw_scenes, start=1):
            base = (
                dict(scene)
                if isinstance(scene, dict)
                else {"description": str(scene) if scene else ""}
            )
            scene_no = to_int(base.get("scene_number")) or idx
            desc = (
                base.get("description")
                or base.get("summary")
                or base.get("slug_line")
                or base.get("story_beat")
                or base.get("title")
            )
            base["scene_number"] = scene_no
            if desc:
                base.setdefault("description", desc)
                base.setdefault("summary", desc)
            if not base.get("slug_line"):
                location = base.get("location") or base.get("place")
                time_of_day = base.get("time_of_day") or base.get("time")
                if location and time_of_day:
                    base["slug_line"] = f"{location} - {time_of_day}"
                elif desc:
                    base["slug_line"] = desc[:80]
            scenes.append(base)
        return scenes

    def _normalize_dialogues(
        self, raw_dialogues: List, scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize dialogues list."""
        dialogues = []
        for idx, item in enumerate(raw_dialogues, start=1):
            if isinstance(item, str):
                dialogues.append(
                    {
                        "scene_number": (
                            scenes[idx - 1]["scene_number"]
                            if idx - 1 < len(scenes)
                            else idx
                        ),
                        "content": item,
                    }
                )
                continue
            if not isinstance(item, dict):
                continue
            dialog = dict(item)
            content = (
                dialog.get("content")
                or dialog.get("line")
                or dialog.get("text")
                or dialog.get("dialogue")
            )
            if not content:
                continue
            dialog["content"] = content
            sn = to_int(dialog.get("scene_number"))
            if sn is None:
                dialog["scene_number"] = (
                    scenes[idx - 1]["scene_number"] if idx - 1 < len(scenes) else idx
                )
            dialogues.append(dialog)
        return dialogues

    def _normalize_stage_directions(
        self, raw_stage: List, scenes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Normalize stage directions list."""
        directions = []
        for idx, item in enumerate(raw_stage, start=1):
            if isinstance(item, str):
                directions.append(
                    {
                        "scene_number": (
                            scenes[idx - 1]["scene_number"]
                            if idx - 1 < len(scenes)
                            else idx
                        ),
                        "content": item,
                    }
                )
                continue
            if not isinstance(item, dict):
                continue
            direction = dict(item)
            content = (
                direction.get("content")
                or direction.get("direction")
                or direction.get("description")
            )
            if not content:
                continue
            direction["content"] = content
            sn = to_int(direction.get("scene_number"))
            if sn is None:
                direction["scene_number"] = (
                    scenes[idx - 1]["scene_number"] if idx - 1 < len(scenes) else idx
                )
            directions.append(direction)
        return directions

    def _populate_missing_parts(
        self,
        scenes: List[Dict[str, Any]],
        dialogues: List[Dict[str, Any]],
        stage_directions: List[Dict[str, Any]],
        story: Story,
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Populate missing dialogues and stage directions from scenes."""
        from app.services.script_missing_parts import (
            populate_dialogues_and_stage_if_missing,
        )

        return populate_dialogues_and_stage_if_missing(
            scenes,
            dialogues,
            stage_directions,
            story=story,
        )

    def _build_extra_metadata(
        self, ai_content: Dict[str, Any], result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build extra metadata from AI result."""
        extra_meta = {
            k: v
            for k, v in ai_content.items()
            if k
            not in {"content", "scenes", "dialogues", "stage_directions", "metadata"}
        }

        agent_run = {}
        if isinstance(result, dict):
            agent_run = {
                "generation_method": result.get("generation_method"),
                "template_used": result.get("template_used"),
                "provider_used": result.get("provider_used"),
                "model_used": result.get("model_used"),
                "usage": result.get("usage"),
                "reasoning": result.get("reasoning"),
                "quality_gate": result.get("quality_gate"),
            }

        if agent_run:
            extra_meta = {**(extra_meta or {}), "agent_run": agent_run}

        return extra_meta


def get_script_generator(session: Session) -> ScriptGenerator:
    """Factory function to create ScriptGenerator instance."""
    return ScriptGenerator(session)
