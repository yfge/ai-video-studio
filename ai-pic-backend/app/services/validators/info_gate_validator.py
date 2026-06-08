"""Information Gate Validator - prevents dialogue from referencing unrevealed plot information.

This validator ensures that:
1. Characters don't mention information they haven't learned yet
2. Dialogue doesn't reference events that haven't happened
3. The audience-knows vs character-knows distinction is respected
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set

from app.schemas.continuity import RevealedInfoItem


class InfoGateSeverity(str, Enum):
    """Severity levels for information gate violations."""

    ERROR = "error"  # Hard violation - character references unknown info
    WARNING = "warning"  # Soft violation - ambiguous reference
    INFO = "info"  # Informational - potential issue


class InfoGateViolationType(str, Enum):
    """Types of information gate violations."""

    CHARACTER_KNOWS_TOO_MUCH = "character_knows_too_much"
    REFERENCES_FUTURE_EVENT = "references_future_event"
    REFERENCES_UNREVEALED_SECRET = "references_unrevealed_secret"
    PREMATURE_RELATIONSHIP_KNOWLEDGE = "premature_relationship_knowledge"
    TIMELINE_INCONSISTENCY = "timeline_inconsistency"


@dataclass
class InfoGateViolation:
    """A single information gate violation."""

    violation_type: InfoGateViolationType
    severity: InfoGateSeverity
    message: str
    speaker: Optional[str] = None
    dialogue_text: Optional[str] = None
    referenced_info: Optional[str] = None
    episode_number: Optional[int] = None
    scene_number: Optional[int] = None
    fix_suggestion: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "violation_type": self.violation_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "speaker": self.speaker,
            "dialogue_text": self.dialogue_text,
            "referenced_info": self.referenced_info,
            "episode_number": self.episode_number,
            "scene_number": self.scene_number,
            "fix_suggestion": self.fix_suggestion,
        }


@dataclass
class InfoGateContext:
    """Context for information gate validation at a specific point in the story."""

    current_episode: int
    current_scene: Optional[int] = None
    # Maps character name -> set of info_keys they know
    character_knowledge: Dict[str, Set[str]] = field(default_factory=dict)
    # Set of info_keys known to the audience
    audience_knowledge: Set[str] = field(default_factory=set)
    # All revealed info items up to current point
    revealed_items: List[RevealedInfoItem] = field(default_factory=list)


class InfoGateValidator:
    """Validates that dialogue doesn't reference unrevealed information.

    The validator maintains a timeline of revealed information and checks
    whether dialogue at any given point references information that hasn't
    been revealed yet.
    """

    # Common patterns that might indicate information leakage
    KNOWLEDGE_INDICATORS = [
        r"我知道.*?是",  # "I know ... is"
        r"我听说",  # "I heard"
        r"原来.*?是",  # "So ... is"
        r"其实.*?是",  # "Actually ... is"
        r"你是.*?的",  # "You are ...'s"
        r"他是.*?的",  # "He is ...'s"
        r"她是.*?的",  # "She is ...'s"
    ]

    def __init__(self) -> None:
        """Initialize the validator."""
        self._info_registry: Dict[str, RevealedInfoItem] = {}
        self._keyword_to_info: Dict[str, List[str]] = {}  # keyword -> list of info_keys

    def register_revealed_info(self, items: List[RevealedInfoItem]) -> None:
        """Register revealed information items for validation.

        Args:
            items: List of RevealedInfoItem objects from the continuity ledger
        """
        for item in items:
            self._info_registry[item.info_key] = item
            # Index keywords from info content for text scanning
            keywords = self._extract_keywords(item.info_content)
            for kw in keywords:
                if kw not in self._keyword_to_info:
                    self._keyword_to_info[kw] = []
                self._keyword_to_info[kw].append(item.info_key)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract significant keywords from text for matching.

        Args:
            text: The text to extract keywords from

        Returns:
            List of keywords (Chinese words or English words)
        """
        keywords = []
        common_words = {
            "的",
            "是",
            "在",
            "和",
            "了",
            "有",
            "与",
            "为",
            "被",
            "把",
            "a",
            "the",
            "is",
            "are",
        }

        # Remove punctuation
        cleaned = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)

        # Extract English words (space-separated)
        english_words = re.findall(r"[a-zA-Z]+", cleaned)
        for word in english_words:
            if len(word) >= 2 and word.lower() not in common_words:
                keywords.append(word)

        # Extract Chinese text chunks
        chinese_text = re.sub(r"[a-zA-Z0-9\s]+", "", cleaned)

        # For Chinese, extract bi-grams and significant substrings
        # Also keep the full text as a keyword if it's meaningful
        if len(chinese_text) >= 2:
            # Add the full phrase if short enough
            if len(chinese_text) <= 8:
                keywords.append(chinese_text)

            # Extract bi-grams for longer text
            for i in range(len(chinese_text) - 1):
                bigram = chinese_text[i : i + 2]
                if bigram not in common_words:
                    keywords.append(bigram)

            # Extract tri-grams for even better matching
            for i in range(len(chinese_text) - 2):
                trigram = chinese_text[i : i + 3]
                keywords.append(trigram)

        return list(set(keywords))  # Remove duplicates

    def build_context(
        self,
        episode_number: int,
        scene_number: Optional[int] = None,
    ) -> InfoGateContext:
        """Build validation context for a specific point in the story.

        This determines what information each character and the audience
        knows at the specified episode/scene.

        Args:
            episode_number: The current episode number
            scene_number: Optional scene number within the episode

        Returns:
            InfoGateContext with character and audience knowledge state
        """
        context = InfoGateContext(
            current_episode=episode_number,
            current_scene=scene_number,
        )

        for info_key, item in self._info_registry.items():
            # Check if this info has been revealed by this point
            if item.revealed_at_episode > episode_number:
                continue
            if (
                item.revealed_at_episode == episode_number
                and scene_number is not None
                and item.revealed_at_scene is not None
                and item.revealed_at_scene > scene_number
            ):
                continue

            # Info is revealed - add to appropriate knowledge sets
            context.revealed_items.append(item)

            if item.is_public:
                # Public info - everyone knows
                context.audience_knowledge.add(info_key)
                # Add to all known characters
                for char_name in context.character_knowledge:
                    context.character_knowledge[char_name].add(info_key)
            else:
                # Check who this info was revealed to
                for recipient in item.revealed_to:
                    if recipient == "观众" or recipient == "audience":
                        context.audience_knowledge.add(info_key)
                    else:
                        if recipient not in context.character_knowledge:
                            context.character_knowledge[recipient] = set()
                        context.character_knowledge[recipient].add(info_key)

        return context

    def validate_dialogue(
        self,
        speaker: str,
        dialogue_text: str,
        context: InfoGateContext,
    ) -> List[InfoGateViolation]:
        """Validate a single dialogue line against the information gate.

        Args:
            speaker: The character speaking
            dialogue_text: The dialogue content
            context: The current information gate context

        Returns:
            List of violations found
        """
        violations = []

        # Get what the speaker knows
        speaker_knowledge = context.character_knowledge.get(speaker, set())

        # Scan dialogue for references to registered info
        for keyword, info_keys in self._keyword_to_info.items():
            if keyword in dialogue_text:
                for info_key in info_keys:
                    item = self._info_registry.get(info_key)
                    if not item:
                        continue

                    # Check if speaker should know this
                    if info_key not in speaker_knowledge and not item.is_public:
                        # Check if it's been revealed at all
                        if item.revealed_at_episode > context.current_episode:
                            violations.append(
                                InfoGateViolation(
                                    violation_type=InfoGateViolationType.REFERENCES_FUTURE_EVENT,
                                    severity=InfoGateSeverity.ERROR,
                                    message=f"角色 '{speaker}' 提及了尚未发生的事件/信息",
                                    speaker=speaker,
                                    dialogue_text=dialogue_text,
                                    referenced_info=item.info_content,
                                    episode_number=context.current_episode,
                                    scene_number=context.current_scene,
                                    fix_suggestion=f"删除或修改对白中关于 '{keyword}' 的引用，"
                                    f"该信息将在第 {item.revealed_at_episode} 集揭示",
                                )
                            )
                        else:
                            violations.append(
                                InfoGateViolation(
                                    violation_type=InfoGateViolationType.CHARACTER_KNOWS_TOO_MUCH,
                                    severity=InfoGateSeverity.ERROR,
                                    message=f"角色 '{speaker}' 不应知道此信息",
                                    speaker=speaker,
                                    dialogue_text=dialogue_text,
                                    referenced_info=item.info_content,
                                    episode_number=context.current_episode,
                                    scene_number=context.current_scene,
                                    fix_suggestion=f"'{speaker}' 在当前时间点不知道 '{item.info_content}'，"
                                    f"该信息仅揭示给: {', '.join(item.revealed_to)}",
                                )
                            )

        return violations

    def validate_script_content(
        self,
        script_content: Dict,
        episode_number: int,
    ) -> List[InfoGateViolation]:
        """Validate an entire script for information gate violations.

        Args:
            script_content: The script content dict with scenes/dialogues
            episode_number: The episode number being validated

        Returns:
            List of all violations found
        """
        all_violations = []

        scenes = script_content.get("scenes", [])
        for scene_idx, scene in enumerate(scenes):
            scene_number = scene.get("scene_number", scene_idx + 1)
            context = self.build_context(episode_number, scene_number)

            dialogues = scene.get("dialogues", []) or scene.get("dialogue", [])
            for dialogue in dialogues:
                speaker = dialogue.get("speaker") or dialogue.get("character")
                text = (
                    dialogue.get("text")
                    or dialogue.get("content")
                    or dialogue.get("dialogue")
                )
                if not speaker or not text:
                    continue

                violations = self.validate_dialogue(speaker, text, context)
                all_violations.extend(violations)

        return all_violations

    def generate_fix_suggestions(
        self, violations: List[InfoGateViolation]
    ) -> List[Dict]:
        """Generate actionable fix suggestions for violations.

        Args:
            violations: List of violations to generate fixes for

        Returns:
            List of fix suggestion dictionaries
        """
        suggestions = []
        for v in violations:
            suggestion = {
                "violation": v.to_dict(),
                "suggested_actions": [],
            }

            if v.violation_type == InfoGateViolationType.CHARACTER_KNOWS_TOO_MUCH:
                suggestion["suggested_actions"] = [
                    f"删除对白中对 '{v.referenced_info}' 的引用",
                    f"添加一个场景让 '{v.speaker}' 先获得这个信息",
                    "修改对白使其模糊或间接引用",
                ]
            elif v.violation_type == InfoGateViolationType.REFERENCES_FUTURE_EVENT:
                suggestion["suggested_actions"] = [
                    "删除对白中对未来事件的引用",
                    "改为角色的猜测或预感（而非确定性陈述）",
                ]

            suggestions.append(suggestion)

        return suggestions
