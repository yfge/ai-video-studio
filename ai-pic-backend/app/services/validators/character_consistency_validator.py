"""
Character consistency validator.

Validates character consistency across Story, Episode, Script, and Storyboard
generation pipelines. Ensures:
- Character names are normalized (aliases/nicknames unified)
- Character attributes don't contradict across contexts
- Generated characters match input character profiles
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CharacterProfile:
    """Normalized character profile for validation."""

    name: str
    aliases: list[str] = field(default_factory=list)
    role_type: str | None = None  # protagonist, antagonist, supporting, etc.
    gender: str | None = None
    age: str | None = None  # "young", "middle-aged", "elderly", or specific age
    personality: list[str] = field(default_factory=list)
    appearance: str | None = None
    voice_style: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "aliases": self.aliases,
            "role_type": self.role_type,
            "gender": self.gender,
            "age": self.age,
            "personality": self.personality,
            "appearance": self.appearance,
            "voice_style": self.voice_style,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CharacterProfile:
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            aliases=data.get("aliases", []),
            role_type=data.get("role_type"),
            gender=data.get("gender"),
            age=data.get("age"),
            personality=data.get("personality", []),
            appearance=data.get("appearance"),
            voice_style=data.get("voice_style"),
        )


@dataclass
class CharacterValidationResult:
    """Result of character consistency validation."""

    passed: bool
    severity: ValidationSeverity
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "passed": self.passed,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def success(cls, message: str, details: dict | None = None) -> CharacterValidationResult:
        """Create a success result."""
        return cls(passed=True, severity=ValidationSeverity.INFO, message=message, details=details or {})

    @classmethod
    def warning(cls, message: str, details: dict | None = None, suggestions: list[str] | None = None) -> CharacterValidationResult:
        """Create a warning result."""
        return cls(passed=True, severity=ValidationSeverity.WARNING, message=message, details=details or {}, suggestions=suggestions or [])

    @classmethod
    def error(cls, message: str, details: dict | None = None, suggestions: list[str] | None = None) -> CharacterValidationResult:
        """Create an error result (validation failed)."""
        return cls(passed=False, severity=ValidationSeverity.ERROR, message=message, details=details or {}, suggestions=suggestions or [])


class CharacterConsistencyValidator:
    """
    Validates character consistency across content generation.

    Usage:
        validator = CharacterConsistencyValidator()
        validator.register_profiles(character_cards)
        results = validator.validate_content(generated_text)
    """

    # Common narrator/system names to skip
    NARRATOR_NAMES = {"旁白", "Narrator", "narrator", "画外音", "Voice Over", "VO", "系统", "System"}

    def __init__(self) -> None:
        self._profiles: dict[str, CharacterProfile] = {}
        self._alias_map: dict[str, str] = {}  # alias -> canonical name

    def register_profiles(self, profiles: list[CharacterProfile | dict[str, Any]]) -> None:
        """Register character profiles for validation."""
        for profile in profiles:
            if isinstance(profile, dict):
                profile = CharacterProfile.from_dict(profile)
            self._register_profile(profile)

    def _register_profile(self, profile: CharacterProfile) -> None:
        """Register a single character profile."""
        canonical = self._normalize_name(profile.name)
        self._profiles[canonical] = profile
        self._alias_map[canonical] = canonical

        for alias in profile.aliases:
            norm_alias = self._normalize_name(alias)
            self._alias_map[norm_alias] = canonical

    def _normalize_name(self, name: str) -> str:
        """Normalize character name for comparison."""
        return name.strip().lower()

    def resolve_name(self, name: str) -> str | None:
        """Resolve a name to its canonical form, or None if unknown."""
        norm = self._normalize_name(name)
        return self._alias_map.get(norm)

    def get_profile(self, name: str) -> CharacterProfile | None:
        """Get character profile by name or alias."""
        canonical = self.resolve_name(name)
        if canonical:
            return self._profiles.get(canonical)
        return None

    def validate_names_in_text(self, text: str) -> list[CharacterValidationResult]:
        """
        Validate character names appearing in text.

        Checks for:
        - Unknown characters (not registered)
        - Potential typos (similar to registered names)
        """
        results: list[CharacterValidationResult] = []
        found_names = self._extract_character_names(text)

        unknown_names: list[str] = []
        potential_typos: list[dict[str, Any]] = []

        for name in found_names:
            if name in self.NARRATOR_NAMES:
                continue

            canonical = self.resolve_name(name)
            if canonical:
                continue  # Known character

            # Check for potential typos
            similar = self._find_similar_names(name)
            if similar:
                potential_typos.append({"found": name, "similar_to": similar})
            else:
                unknown_names.append(name)

        if unknown_names:
            results.append(
                CharacterValidationResult.warning(
                    message=f"Found {len(unknown_names)} unknown character(s)",
                    details={"unknown_names": unknown_names},
                    suggestions=["Register these characters or check for typos"],
                )
            )

        if potential_typos:
            results.append(
                CharacterValidationResult.warning(
                    message=f"Found {len(potential_typos)} potential character name typo(s)",
                    details={"potential_typos": potential_typos},
                    suggestions=["Verify character name spelling"],
                )
            )

        if not unknown_names and not potential_typos:
            results.append(
                CharacterValidationResult.success(
                    message=f"All {len(found_names)} character names are valid",
                    details={"found_names": list(found_names)},
                )
            )

        return results

    def validate_character_attributes(
        self, name: str, attributes: dict[str, Any]
    ) -> list[CharacterValidationResult]:
        """
        Validate that character attributes don't contradict profile.

        Args:
            name: Character name
            attributes: Dict of attributes to validate (gender, age, personality, etc.)
        """
        results: list[CharacterValidationResult] = []
        profile = self.get_profile(name)

        if not profile:
            results.append(
                CharacterValidationResult.warning(
                    message=f"No profile found for character '{name}'",
                    suggestions=["Register character profile before validation"],
                )
            )
            return results

        contradictions: list[dict[str, Any]] = []

        # Check gender
        if "gender" in attributes and profile.gender:
            if not self._attributes_compatible(profile.gender, attributes["gender"]):
                contradictions.append({
                    "attribute": "gender",
                    "profile": profile.gender,
                    "found": attributes["gender"],
                })

        # Check age
        if "age" in attributes and profile.age:
            if not self._age_compatible(profile.age, attributes["age"]):
                contradictions.append({
                    "attribute": "age",
                    "profile": profile.age,
                    "found": attributes["age"],
                })

        # Check personality
        if "personality" in attributes and profile.personality:
            found_traits = attributes["personality"]
            if isinstance(found_traits, str):
                found_traits = [found_traits]
            conflicts = self._find_personality_conflicts(profile.personality, found_traits)
            if conflicts:
                contradictions.append({
                    "attribute": "personality",
                    "profile": profile.personality,
                    "found": found_traits,
                    "conflicts": conflicts,
                })

        if contradictions:
            results.append(
                CharacterValidationResult.error(
                    message=f"Character '{name}' has {len(contradictions)} attribute contradiction(s)",
                    details={"contradictions": contradictions},
                    suggestions=["Align character attributes with profile"],
                )
            )
        else:
            results.append(
                CharacterValidationResult.success(
                    message=f"Character '{name}' attributes are consistent",
                )
            )

        return results

    def _extract_character_names(self, text: str) -> set[str]:
        """Extract potential character names from text."""
        names: set[str] = set()

        # Pattern 1: Dialogue format "Name: text" or "Name："
        dialogue_pattern = r"^([^\n:：]{1,20})[:：]"
        for match in re.finditer(dialogue_pattern, text, re.MULTILINE):
            name = match.group(1).strip()
            if name and not name.startswith(("(", "（", "[", "【")):
                names.add(name)

        # Pattern 2: Stage direction [Name does something]
        stage_pattern = r"\[([^\]]{1,20}?)\s+(?:走|说|看|做|站|坐|拿|放)"
        for match in re.finditer(stage_pattern, text):
            names.add(match.group(1).strip())

        # Pattern 3: Known character names in text
        for canonical in self._profiles:
            profile = self._profiles[canonical]
            if profile.name in text:
                names.add(profile.name)
            for alias in profile.aliases:
                if alias in text:
                    names.add(alias)

        return names

    def _find_similar_names(self, name: str) -> list[str]:
        """Find registered names similar to the given name."""
        similar: list[str] = []
        norm_name = self._normalize_name(name)

        for canonical, profile in self._profiles.items():
            if self._names_similar(norm_name, canonical):
                similar.append(profile.name)

        return similar

    def _names_similar(self, name1: str, name2: str) -> bool:
        """Check if two names are similar (potential typo)."""
        if name1 == name2:
            return False

        # One contains the other
        if name1 in name2 or name2 in name1:
            return True

        # Edit distance for short names
        if len(name1) <= 10 and len(name2) <= 10:
            if abs(len(name1) - len(name2)) <= 2:
                diff = sum(1 for a, b in zip(name1, name2) if a != b)
                diff += abs(len(name1) - len(name2))
                return diff <= 2

        return False

    def _attributes_compatible(self, expected: str, found: str) -> bool:
        """Check if two attribute values are compatible."""
        e = expected.lower().strip()
        f = found.lower().strip()

        # Exact match
        if e == f:
            return True

        # Gender-specific handling (male/female are distinct)
        gender_male = {"male", "man", "boy", "男", "男性", "男人"}
        gender_female = {"female", "woman", "girl", "女", "女性", "女人"}

        e_male = any(g in e for g in gender_male)
        e_female = any(g in e for g in gender_female)
        f_male = any(g in f for g in gender_male)
        f_female = any(g in f for g in gender_female)

        if (e_male or e_female) and (f_male or f_female):
            return e_male == f_male and e_female == f_female

        # General substring match for other attributes
        return e in f or f in e

    def _age_compatible(self, profile_age: str, found_age: str) -> bool:
        """Check if age descriptions are compatible."""
        age_groups = {
            "child": ["child", "kid", "小孩", "儿童", "少年", "孩子"],
            "young": ["young", "youth", "young adult", "青年", "年轻", "青春"],
            "middle": ["middle", "middle-aged", "adult", "中年", "成年", "壮年"],
            "elderly": ["elderly", "old", "senior", "老年", "老人", "年迈"],
        }

        p_age = profile_age.lower().strip()
        f_age = found_age.lower().strip()

        # Exact match
        if p_age == f_age:
            return True

        # Find which group each belongs to
        p_group = None
        f_group = None

        for group, keywords in age_groups.items():
            if any(kw in p_age or p_age in kw for kw in keywords):
                p_group = group
            if any(kw in f_age or f_age in kw for kw in keywords):
                f_group = group

        # If both identified, check if same group
        if p_group and f_group:
            return p_group == f_group

        # Can't determine conflict
        return True

    def _find_personality_conflicts(
        self, profile_traits: list[str], found_traits: list[str]
    ) -> list[tuple[str, str]]:
        """Find conflicting personality traits."""
        conflicts: list[tuple[str, str]] = []

        opposites = [
            ("introverted", "extroverted"),
            ("shy", "outgoing"),
            ("calm", "aggressive"),
            ("kind", "cruel"),
            ("honest", "deceptive"),
            ("brave", "cowardly"),
            ("optimistic", "pessimistic"),
            ("内向", "外向"),
            ("冷静", "暴躁"),
            ("善良", "残忍"),
        ]

        p_lower = [t.lower() for t in profile_traits]
        f_lower = [t.lower() for t in found_traits]

        for trait1, trait2 in opposites:
            has_t1_profile = any(trait1 in t for t in p_lower)
            has_t2_profile = any(trait2 in t for t in p_lower)
            has_t1_found = any(trait1 in t for t in f_lower)
            has_t2_found = any(trait2 in t for t in f_lower)

            if (has_t1_profile and has_t2_found) or (has_t2_profile and has_t1_found):
                conflicts.append((trait1, trait2))

        return conflicts
