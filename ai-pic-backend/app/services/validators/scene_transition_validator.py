"""Scene Transition Validator - validates physical plausibility of scene transitions.

This validator ensures that:
1. Geographic transitions are plausible (travel time between locations)
2. Time transitions are logical (day→night progression)
3. Character states are consistent across scenes (injury→recovery)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class TransitionSeverity(str, Enum):
    """Severity levels for transition issues."""

    ERROR = "error"  # Hard violation - physically impossible
    WARNING = "warning"  # Soft violation - implausible but possible
    INFO = "info"  # Informational - minor inconsistency


class TransitionIssueType(str, Enum):
    """Types of transition issues."""

    GEOGRAPHIC_IMPOSSIBILITY = "geographic_impossibility"
    TIME_DISCONTINUITY = "time_discontinuity"
    CHARACTER_STATE_VIOLATION = "character_state_violation"
    WEATHER_INCONSISTENCY = "weather_inconsistency"
    LIGHTING_DISCONTINUITY = "lighting_discontinuity"


@dataclass
class TransitionIssue:
    """A single scene transition issue."""

    issue_type: TransitionIssueType
    severity: TransitionSeverity
    message: str
    from_scene: int
    to_scene: int
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    affected_characters: List[str] = field(default_factory=list)
    fix_suggestion: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "from_scene": self.from_scene,
            "to_scene": self.to_scene,
            "from_location": self.from_location,
            "to_location": self.to_location,
            "affected_characters": self.affected_characters,
            "fix_suggestion": self.fix_suggestion,
        }


@dataclass
class SceneInfo:
    """Extracted scene information for transition validation."""

    scene_number: int
    location: Optional[str] = None
    city: Optional[str] = None
    time_of_day: Optional[str] = None
    weather: Optional[str] = None
    characters_present: List[str] = field(default_factory=list)
    character_states: Dict[str, str] = field(default_factory=dict)


class SceneTransitionValidator:
    """Validates physical plausibility of scene transitions.

    Checks geographic, temporal, and character state continuity
    between consecutive scenes.
    """

    # Time of day categories for transition validation
    TIME_CATEGORIES = {
        "dawn": ["dawn", "sunrise", "daybreak", "黎明", "拂晓", "日出"],
        "morning": ["morning", "am", "早上", "上午", "早晨"],
        "noon": ["noon", "midday", "正午", "中午"],
        "afternoon": ["afternoon", "pm", "下午"],
        "evening": ["evening", "dusk", "sunset", "傍晚", "黄昏", "日落"],
        "night": ["night", "midnight", "late night", "夜晚", "深夜", "半夜", "晚上"],
    }

    # Valid time progressions (key can transition to values)
    VALID_TIME_PROGRESSIONS = {
        "dawn": ["dawn", "morning", "noon"],
        "morning": ["morning", "noon", "afternoon"],
        "noon": ["noon", "afternoon", "evening"],
        "afternoon": ["afternoon", "evening", "night"],
        "evening": ["evening", "night"],
        "night": ["night", "dawn", "morning"],  # Night can transition to next day
    }

    # Major cities and their approximate travel times (in hours) to other cities
    # This is simplified - real implementation would use a proper distance/time API
    CITY_TRAVEL_TIMES: Dict[str, Dict[str, float]] = {
        "北京": {"上海": 5, "广州": 8, "深圳": 8, "成都": 6, "杭州": 5, "西安": 4},
        "上海": {"北京": 5, "广州": 6, "深圳": 6, "成都": 7, "杭州": 1, "西安": 6},
        "广州": {"北京": 8, "上海": 6, "深圳": 0.5, "成都": 6, "杭州": 5, "西安": 7},
        "深圳": {"北京": 8, "上海": 6, "广州": 0.5, "成都": 6, "杭州": 5, "西安": 7},
    }

    # Character states that restrict actions
    RESTRICTIVE_STATES = {
        "injured": ["受伤", "injured", "hurt", "wounded", "伤"],
        "unconscious": ["昏迷", "unconscious", "passed out", "晕倒"],
        "sick": ["生病", "sick", "ill", "病"],
        "exhausted": ["疲惫", "exhausted", "tired", "累"],
        "restrained": ["被绑", "restrained", "tied up", "captured", "囚禁"],
    }

    # Actions that conflict with restrictive states
    STATE_ACTION_CONFLICTS = {
        "injured": ["running", "fighting", "跑", "打斗", "激烈运动", "追逐"],
        "unconscious": ["speaking", "walking", "说话", "行走", "任何动作"],
        "sick": ["intense activity", "激烈活动"],
        "exhausted": ["marathon", "马拉松", "长跑"],
        "restrained": ["free movement", "自由行动", "逃跑"],
    }

    def __init__(self) -> None:
        """Initialize the validator."""
        self._character_states: Dict[str, Dict[str, str]] = (
            {}
        )  # char -> scene_num -> state

    def _normalize_time(self, time_str: Optional[str]) -> Optional[str]:
        """Normalize time of day string to category.

        Args:
            time_str: Time of day string (e.g., "morning", "早上")

        Returns:
            Normalized time category or None
        """
        if not time_str:
            return None

        time_lower = time_str.lower()
        for category, keywords in self.TIME_CATEGORIES.items():
            for kw in keywords:
                if kw in time_lower:
                    return category
        return None

    def _extract_city(self, location: Optional[str]) -> Optional[str]:
        """Extract city name from location string.

        Args:
            location: Location string (e.g., "北京市朝阳区")

        Returns:
            City name or None
        """
        if not location:
            return None

        # Check for known cities
        known_cities = list(self.CITY_TRAVEL_TIMES.keys())
        for city in known_cities:
            if city in location:
                return city

        # Try to extract city pattern
        city_patterns = [
            r"(\w+)市",  # X市
            r"(\w+)省",  # X省
            r"in (\w+)",  # in City
            r"(\w+), ",  # City,
        ]
        for pattern in city_patterns:
            match = re.search(pattern, location)
            if match:
                return match.group(1)

        return None

    def _check_time_transition(
        self,
        from_scene: SceneInfo,
        to_scene: SceneInfo,
    ) -> Optional[TransitionIssue]:
        """Check if time transition between scenes is valid.

        Args:
            from_scene: Previous scene info
            to_scene: Next scene info

        Returns:
            TransitionIssue if invalid, None otherwise
        """
        from_time = self._normalize_time(from_scene.time_of_day)
        to_time = self._normalize_time(to_scene.time_of_day)

        if not from_time or not to_time:
            return None  # Can't validate without time info

        # Check if transition is valid
        valid_transitions = self.VALID_TIME_PROGRESSIONS.get(from_time, [])
        if to_time not in valid_transitions:
            # Check if it's a backwards jump (needs explicit time jump)
            return TransitionIssue(
                issue_type=TransitionIssueType.TIME_DISCONTINUITY,
                severity=TransitionSeverity.WARNING,
                message=f"时间跳跃不连贯：从 {from_time}({from_scene.time_of_day}) 到 {to_time}({to_scene.time_of_day})",
                from_scene=from_scene.scene_number,
                to_scene=to_scene.scene_number,
                fix_suggestion="添加过渡场景或时间标记说明时间流逝（如'数小时后'、'第二天'）",
            )

        return None

    def _check_geographic_transition(
        self,
        from_scene: SceneInfo,
        to_scene: SceneInfo,
    ) -> Optional[TransitionIssue]:
        """Check if geographic transition between scenes is plausible.

        Args:
            from_scene: Previous scene info
            to_scene: Next scene info

        Returns:
            TransitionIssue if implausible, None otherwise
        """
        from_city = from_scene.city or self._extract_city(from_scene.location)
        to_city = to_scene.city or self._extract_city(to_scene.location)

        if not from_city or not to_city:
            return None  # Can't validate without city info

        if from_city == to_city:
            return None  # Same city, no issue

        # Check travel time between cities
        travel_time = self.CITY_TRAVEL_TIMES.get(from_city, {}).get(to_city)
        if travel_time is None:
            # Try reverse lookup
            travel_time = self.CITY_TRAVEL_TIMES.get(to_city, {}).get(from_city)

        if travel_time is None:
            # Unknown cities - assume potential issue
            return TransitionIssue(
                issue_type=TransitionIssueType.GEOGRAPHIC_IMPOSSIBILITY,
                severity=TransitionSeverity.WARNING,
                message=f"跨城市转场：从 {from_city} 到 {to_city}，请确认时间合理性",
                from_scene=from_scene.scene_number,
                to_scene=to_scene.scene_number,
                from_location=from_scene.location,
                to_location=to_scene.location,
                fix_suggestion="添加交通/旅行场景或时间标记说明旅途",
            )

        # If travel time > 2 hours, check if time of day supports it
        if travel_time > 2:
            from_time = self._normalize_time(from_scene.time_of_day)
            to_time = self._normalize_time(to_scene.time_of_day)

            # If same time of day but long travel, flag it
            if from_time and to_time and from_time == to_time:
                return TransitionIssue(
                    issue_type=TransitionIssueType.GEOGRAPHIC_IMPOSSIBILITY,
                    severity=TransitionSeverity.ERROR,
                    message=f"地理不可能：从 {from_city} 到 {to_city} 需要约 {travel_time} 小时，但时间未变化",
                    from_scene=from_scene.scene_number,
                    to_scene=to_scene.scene_number,
                    from_location=from_scene.location,
                    to_location=to_scene.location,
                    fix_suggestion=f"修改到达场景的时间为 {travel_time} 小时后，或添加旅途过渡",
                )

        return None

    def _detect_character_state(self, text: str) -> Optional[str]:
        """Detect restrictive character state from text.

        Args:
            text: Text to scan (dialogue, stage direction, etc.)

        Returns:
            Detected state or None
        """
        text_lower = text.lower()
        for state, keywords in self.RESTRICTIVE_STATES.items():
            for kw in keywords:
                if kw in text_lower:
                    return state
        return None

    def _check_character_state_transition(
        self,
        from_scene: SceneInfo,
        to_scene: SceneInfo,
        scene_content: Optional[Dict] = None,
    ) -> List[TransitionIssue]:
        """Check if character states are consistent across scenes.

        Args:
            from_scene: Previous scene info
            to_scene: Next scene info
            scene_content: Optional scene content dict for action detection

        Returns:
            List of TransitionIssue objects
        """
        issues = []

        # Find common characters between scenes
        common_chars = set(from_scene.characters_present) & set(
            to_scene.characters_present
        )

        for char in common_chars:
            # Check if character had a restrictive state in previous scene
            prev_state = from_scene.character_states.get(char)
            if not prev_state:
                continue

            # Check for conflicting actions in new scene
            conflicting_actions = self.STATE_ACTION_CONFLICTS.get(prev_state, [])
            if not conflicting_actions:
                continue

            # Scan scene content for conflicting actions
            if scene_content:
                stage_dirs = scene_content.get("stage_directions", [])
                for sd in stage_dirs:
                    content = sd.get("content", "") if isinstance(sd, dict) else str(sd)
                    for action in conflicting_actions:
                        if action in content.lower() and char in content:
                            issues.append(
                                TransitionIssue(
                                    issue_type=TransitionIssueType.CHARACTER_STATE_VIOLATION,
                                    severity=TransitionSeverity.ERROR,
                                    message=f"角色状态冲突：{char} 在上一场景处于 '{prev_state}' 状态，但在本场景执行了 '{action}'",
                                    from_scene=from_scene.scene_number,
                                    to_scene=to_scene.scene_number,
                                    affected_characters=[char],
                                    fix_suggestion=f"添加 {char} 恢复/状态变化的说明，或修改动作",
                                )
                            )

        return issues

    def extract_scene_info(self, scene: Dict) -> SceneInfo:
        """Extract relevant information from a scene dict.

        Args:
            scene: Scene dictionary from script

        Returns:
            SceneInfo object
        """
        # Extract basic info
        scene_number = scene.get("scene_number", 0)
        location = scene.get("location") or scene.get("slug_line", "")
        time_of_day = scene.get("time_of_day", "")

        # Extract city from location
        city = self._extract_city(location)

        # Extract characters from dialogues
        characters = set()
        dialogues = scene.get("dialogues", [])
        for d in dialogues:
            if isinstance(d, dict):
                char = d.get("character") or d.get("speaker")
                if char:
                    characters.add(char)

        # Detect character states from stage directions
        character_states = {}
        stage_dirs = scene.get("stage_directions", [])
        for sd in stage_dirs:
            content = sd.get("content", "") if isinstance(sd, dict) else str(sd)
            state = self._detect_character_state(content)
            if state:
                # Try to associate with a character
                for char in characters:
                    if char in content:
                        character_states[char] = state

        return SceneInfo(
            scene_number=scene_number,
            location=location,
            city=city,
            time_of_day=time_of_day,
            characters_present=list(characters),
            character_states=character_states,
        )

    def validate_transitions(
        self,
        scenes: List[Dict],
        scene_contents: Optional[List[Dict]] = None,
    ) -> List[TransitionIssue]:
        """Validate all scene transitions in a script.

        Args:
            scenes: List of scene dicts from script
            scene_contents: Optional list of scene content dicts (with dialogues, stage_directions)

        Returns:
            List of all transition issues found
        """
        if len(scenes) < 2:
            return []  # Need at least 2 scenes to validate transitions

        all_issues = []

        # Extract info from all scenes
        scene_infos = [self.extract_scene_info(s) for s in scenes]

        # If scene_contents provided, merge with scene_infos
        if scene_contents:
            for i, content in enumerate(scene_contents):
                if i < len(scene_infos):
                    # Update characters from content
                    dialogues = content.get("dialogues", [])
                    for d in dialogues:
                        if isinstance(d, dict):
                            char = d.get("character") or d.get("speaker")
                            if char and char not in scene_infos[i].characters_present:
                                scene_infos[i].characters_present.append(char)

        # Validate each transition
        for i in range(len(scene_infos) - 1):
            from_scene = scene_infos[i]
            to_scene = scene_infos[i + 1]

            # Check time transition
            time_issue = self._check_time_transition(from_scene, to_scene)
            if time_issue:
                all_issues.append(time_issue)

            # Check geographic transition
            geo_issue = self._check_geographic_transition(from_scene, to_scene)
            if geo_issue:
                all_issues.append(geo_issue)

            # Check character state transitions
            scene_content = (
                scene_contents[i + 1]
                if scene_contents and i + 1 < len(scene_contents)
                else None
            )
            state_issues = self._check_character_state_transition(
                from_scene, to_scene, scene_content
            )
            all_issues.extend(state_issues)

        return all_issues

    def generate_fix_suggestions(self, issues: List[TransitionIssue]) -> List[Dict]:
        """Generate actionable fix suggestions for issues.

        Args:
            issues: List of issues to generate fixes for

        Returns:
            List of fix suggestion dictionaries
        """
        suggestions = []
        for issue in issues:
            suggestion = {
                "issue": issue.to_dict(),
                "suggested_actions": [],
            }

            if issue.issue_type == TransitionIssueType.GEOGRAPHIC_IMPOSSIBILITY:
                suggestion["suggested_actions"] = [
                    "添加交通/旅行过渡场景",
                    "调整到达场景的时间设定",
                    "考虑使用'X小时后'、'第二天'等时间标记",
                ]
            elif issue.issue_type == TransitionIssueType.TIME_DISCONTINUITY:
                suggestion["suggested_actions"] = [
                    "添加过渡场景展示时间流逝",
                    "使用字幕/旁白说明时间变化",
                    "调整场景顺序使时间连贯",
                ]
            elif issue.issue_type == TransitionIssueType.CHARACTER_STATE_VIOLATION:
                suggestion["suggested_actions"] = [
                    "添加角色恢复/状态变化的过渡",
                    "修改角色在新场景的动作",
                    "在场景开头说明时间已过去足够久",
                ]

            suggestions.append(suggestion)

        return suggestions
