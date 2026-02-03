"""
Visual continuity validator for storyboard frames.

Validates visual consistency across frames including:
- Costume/props/hairstyle consistency across frames
- Action physical feasibility (no teleportation)
- Composition rules (rule of thirds, leading lines, depth)
- Dialogue-visual synchronization (mouth open when speaking)
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from app.services.storyboard.pipeline.pipeline_state import (
    ValidationResult,
    ValidationSeverity,
)
from app.services.storyboard.validators import BaseValidator

if TYPE_CHECKING:
    from app.services.storyboard.pipeline.pipeline_context import PipelineContext
    from app.services.storyboard.pipeline.pipeline_state import PipelineState


class VisualContinuityValidator(BaseValidator):
    """
    Validates visual continuity across storyboard frames.

    Checks:
    1. Costume/props/hairstyle consistency for characters
    2. Physical feasibility of character movements
    3. Composition rule suggestions
    4. Dialogue-visual synchronization
    """

    # Visual element keywords for consistency checking
    COSTUME_KEYWORDS = {
        "zh": ["穿着", "衣服", "裙子", "外套", "西装", "T恤", "衬衫", "裤子", "制服"],
        "en": ["wearing", "dress", "suit", "shirt", "jacket", "pants", "uniform"],
    }

    HAIRSTYLE_KEYWORDS = {
        "zh": ["发型", "长发", "短发", "卷发", "直发", "马尾", "发色"],
        "en": ["hair", "hairstyle", "ponytail", "braid", "short hair", "long hair"],
    }

    PROP_KEYWORDS = {
        "zh": ["手持", "拿着", "戴着", "背着", "带有", "手中", "眼镜", "帽子", "包"],
        "en": ["holding", "carrying", "wearing", "glasses", "hat", "bag", "phone"],
    }

    # Position keywords for movement detection
    POSITION_KEYWORDS = {
        "zh": {
            "left": ["左侧", "左边", "画面左"],
            "right": ["右侧", "右边", "画面右"],
            "center": ["中央", "中间", "正中"],
            "foreground": ["前景", "近处", "前方"],
            "background": ["背景", "远处", "后方"],
        },
        "en": {
            "left": ["left", "left side"],
            "right": ["right", "right side"],
            "center": ["center", "middle"],
            "foreground": ["foreground", "front"],
            "background": ["background", "back"],
        },
    }

    # Pose keywords for transition checking
    POSE_KEYWORDS = {
        "sitting": {"zh": ["坐着", "坐在", "坐姿"], "en": ["sitting", "seated"]},
        "standing": {"zh": ["站着", "站立", "站姿"], "en": ["standing"]},
        "lying": {"zh": ["躺着", "躺在", "卧姿"], "en": ["lying", "laying"]},
        "walking": {"zh": ["走着", "走动", "行走"], "en": ["walking"]},
        "running": {"zh": ["跑着", "奔跑"], "en": ["running"]},
    }

    # Composition rule keywords
    COMPOSITION_KEYWORDS = {
        "rule_of_thirds": {
            "zh": ["三分法", "三分构图", "黄金分割"],
            "en": ["rule of thirds", "thirds"],
        },
        "leading_lines": {
            "zh": ["引导线", "视线引导"],
            "en": ["leading lines", "guiding lines"],
        },
        "depth": {
            "zh": ["景深", "前景", "中景", "背景", "虚化"],
            "en": ["depth", "depth of field", "bokeh", "shallow depth"],
        },
    }

    # Dialogue state keywords
    MOUTH_SPEAKING_KEYWORDS = {
        "zh": ["说话", "说道", "喊道", "叫道", "开口", "张嘴"],
        "en": ["saying", "speaking", "talking", "shouting", "mouth open"],
    }

    # Position distance thresholds (abstract units)
    POSITION_CHANGE_THRESHOLD = 2  # Max position changes in one frame transition

    @property
    def name(self) -> str:
        return "visual_continuity_validator"

    @property
    def description(self) -> str:
        return "Validates visual continuity across storyboard frames"

    def validate(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        **kwargs: Any,
    ) -> List[ValidationResult]:
        """Run all visual continuity checks."""
        results: List[ValidationResult] = []

        frames = state.frames
        if not frames or len(frames) < 2:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message="Insufficient frames for continuity check",
                    details={"frame_count": len(frames) if frames else 0},
                )
            )
            return results

        # Extract character data from frames
        characters = self._extract_characters_from_frames(frames)

        # Run checks
        results.extend(self._check_costume_continuity(frames, characters))
        results.extend(self._check_hairstyle_continuity(frames, characters))
        results.extend(self._check_prop_continuity(frames, characters))
        results.extend(self._check_movement_feasibility(frames, characters))
        results.extend(self._check_pose_transitions(frames, characters))
        results.extend(self._check_composition_suggestions(frames))
        results.extend(self._check_dialogue_visual_sync(frames))

        # Add summary if no issues
        error_count = sum(1 for r in results if not r.passed)
        warning_count = sum(
            1 for r in results if r.severity == ValidationSeverity.WARNING
        )

        if error_count == 0 and warning_count == 0:
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message=f"Visual continuity validated across {len(frames)} frames",
                    details={"frame_count": len(frames)},
                )
            )

        return results

    def _extract_characters_from_frames(
        self, frames: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract character appearances from frames.

        Returns:
            Dictionary mapping character names to their appearances in frames.
        """
        characters: Dict[str, List[Dict[str, Any]]] = {}

        for i, frame in enumerate(frames):
            frame_chars = frame.get("characters", [])
            if isinstance(frame_chars, list):
                for char in frame_chars:
                    if isinstance(char, dict):
                        name = char.get("name", "unknown")
                    else:
                        name = str(char)
                        char = {"name": name}

                    if name not in characters:
                        characters[name] = []

                    characters[name].append({
                        "frame_index": i,
                        "frame_number": frame.get("frame_number", i + 1),
                        "description": frame.get("description", ""),
                        "visual_description": frame.get("visual_description", ""),
                        "character_data": char,
                    })

        return characters

    def _check_costume_continuity(
        self,
        frames: List[Dict[str, Any]],
        characters: Dict[str, List[Dict[str, Any]]],
    ) -> List[ValidationResult]:
        """Check costume consistency for each character."""
        results: List[ValidationResult] = []

        for char_name, appearances in characters.items():
            if len(appearances) < 2:
                continue

            costumes: List[Tuple[int, Set[str]]] = []
            for app in appearances:
                desc = (
                    app.get("visual_description", "")
                    + " "
                    + app.get("description", "")
                )
                costume_elements = self._extract_visual_elements(desc, "costume")
                costumes.append((app["frame_number"], costume_elements))

            # Check for inconsistencies
            inconsistencies = self._find_inconsistencies(costumes)
            if inconsistencies:
                results.append(
                    ValidationResult.warning(
                        validator_name=self.name,
                        message=(
                            f"Costume inconsistency for '{char_name}': "
                            f"different outfits in frames {inconsistencies}"
                        ),
                        details={
                            "character": char_name,
                            "frames": inconsistencies,
                            "costumes": [
                                {"frame": f, "elements": list(c)}
                                for f, c in costumes
                            ],
                        },
                        suggestions=[
                            f"Ensure {char_name} wears consistent clothing",
                            "Add costume change transition if intentional",
                        ],
                    )
                )

        return results

    def _check_hairstyle_continuity(
        self,
        frames: List[Dict[str, Any]],
        characters: Dict[str, List[Dict[str, Any]]],
    ) -> List[ValidationResult]:
        """Check hairstyle consistency for each character."""
        results: List[ValidationResult] = []

        for char_name, appearances in characters.items():
            if len(appearances) < 2:
                continue

            hairstyles: List[Tuple[int, Set[str]]] = []
            for app in appearances:
                desc = (
                    app.get("visual_description", "")
                    + " "
                    + app.get("description", "")
                )
                hair_elements = self._extract_visual_elements(desc, "hairstyle")
                hairstyles.append((app["frame_number"], hair_elements))

            # Check for inconsistencies
            inconsistencies = self._find_inconsistencies(hairstyles)
            if inconsistencies:
                results.append(
                    ValidationResult.warning(
                        validator_name=self.name,
                        message=(
                            f"Hairstyle inconsistency for '{char_name}': "
                            f"different hair in frames {inconsistencies}"
                        ),
                        details={
                            "character": char_name,
                            "frames": inconsistencies,
                        },
                        suggestions=[
                            f"Keep {char_name}'s hairstyle consistent",
                        ],
                    )
                )

        return results

    def _check_prop_continuity(
        self,
        frames: List[Dict[str, Any]],
        characters: Dict[str, List[Dict[str, Any]]],
    ) -> List[ValidationResult]:
        """Check prop consistency for characters."""
        results: List[ValidationResult] = []

        for char_name, appearances in characters.items():
            if len(appearances) < 2:
                continue

            props: List[Tuple[int, Set[str]]] = []
            for app in appearances:
                desc = (
                    app.get("visual_description", "")
                    + " "
                    + app.get("description", "")
                )
                prop_elements = self._extract_visual_elements(desc, "props")
                props.append((app["frame_number"], prop_elements))

            # Check for props that appear/disappear without explanation
            disappearing = self._find_disappearing_elements(props)
            if disappearing:
                results.append(
                    ValidationResult.warning(
                        validator_name=self.name,
                        message=(
                            f"Props for '{char_name}' appear/disappear: "
                            f"{', '.join(disappearing)}"
                        ),
                        details={
                            "character": char_name,
                            "disappearing_props": list(disappearing),
                        },
                        suggestions=[
                            "Show prop being put down/picked up",
                            "Keep props consistent across frames",
                        ],
                    )
                )

        return results

    def _check_movement_feasibility(
        self,
        frames: List[Dict[str, Any]],
        characters: Dict[str, List[Dict[str, Any]]],
    ) -> List[ValidationResult]:
        """Check that character movements are physically feasible."""
        results: List[ValidationResult] = []

        for char_name, appearances in characters.items():
            if len(appearances) < 2:
                continue

            # Extract positions for each appearance
            positions: List[Tuple[int, str]] = []
            for app in appearances:
                desc = (
                    app.get("visual_description", "")
                    + " "
                    + app.get("description", "")
                )
                position = self._extract_position(desc)
                if position:
                    positions.append((app["frame_number"], position))

            # Check for teleportation (sudden large position changes)
            if len(positions) >= 2:
                teleportations = []
                for i in range(1, len(positions)):
                    prev_frame, prev_pos = positions[i - 1]
                    curr_frame, curr_pos = positions[i]

                    if self._is_teleportation(prev_pos, curr_pos):
                        teleportations.append((prev_frame, curr_frame))

                if teleportations:
                    results.append(
                        ValidationResult.warning(
                            validator_name=self.name,
                            message=(
                                f"'{char_name}' appears to teleport between frames: "
                                f"{teleportations}"
                            ),
                            details={
                                "character": char_name,
                                "teleportations": teleportations,
                            },
                            suggestions=[
                                "Add transition frames showing movement",
                                "Use cut or scene transition",
                            ],
                        )
                    )

        return results

    def _check_pose_transitions(
        self,
        frames: List[Dict[str, Any]],
        characters: Dict[str, List[Dict[str, Any]]],
    ) -> List[ValidationResult]:
        """Check that pose transitions are valid."""
        results: List[ValidationResult] = []

        # Define invalid transitions (require intermediate steps)
        invalid_transitions = {
            ("lying", "running"),
            ("running", "lying"),
            ("sitting", "running"),
        }

        for char_name, appearances in characters.items():
            if len(appearances) < 2:
                continue

            poses: List[Tuple[int, Optional[str]]] = []
            for app in appearances:
                desc = (
                    app.get("visual_description", "")
                    + " "
                    + app.get("description", "")
                )
                pose = self._extract_pose(desc)
                if pose:
                    poses.append((app["frame_number"], pose))

            # Check for invalid transitions
            for i in range(1, len(poses)):
                prev_frame, prev_pose = poses[i - 1]
                curr_frame, curr_pose = poses[i]

                if prev_pose and curr_pose:
                    if (prev_pose, curr_pose) in invalid_transitions:
                        results.append(
                            ValidationResult.warning(
                                validator_name=self.name,
                                message=(
                                    f"'{char_name}' has abrupt pose change: "
                                    f"{prev_pose} → {curr_pose} "
                                    f"(frames {prev_frame}-{curr_frame})"
                                ),
                                details={
                                    "character": char_name,
                                    "from_pose": prev_pose,
                                    "to_pose": curr_pose,
                                    "frames": (prev_frame, curr_frame),
                                },
                                suggestions=[
                                    "Add transition pose (e.g., getting up)",
                                    "Use scene cut for time skip",
                                ],
                            )
                        )

        return results

    def _check_composition_suggestions(
        self,
        frames: List[Dict[str, Any]],
    ) -> List[ValidationResult]:
        """Provide composition rule suggestions."""
        results: List[ValidationResult] = []

        # Track composition mentions
        has_thirds = False
        has_leading_lines = False
        has_depth = False

        for frame in frames:
            desc = (
                frame.get("visual_description", "")
                + " "
                + frame.get("description", "")
                + " "
                + frame.get("composition", "")
            ).lower()

            for keyword in self.COMPOSITION_KEYWORDS["rule_of_thirds"]["zh"]:
                if keyword in desc:
                    has_thirds = True
            for keyword in self.COMPOSITION_KEYWORDS["rule_of_thirds"]["en"]:
                if keyword in desc:
                    has_thirds = True

            for keyword in self.COMPOSITION_KEYWORDS["leading_lines"]["zh"]:
                if keyword in desc:
                    has_leading_lines = True
            for keyword in self.COMPOSITION_KEYWORDS["leading_lines"]["en"]:
                if keyword in desc:
                    has_leading_lines = True

            for keyword in self.COMPOSITION_KEYWORDS["depth"]["zh"]:
                if keyword in desc:
                    has_depth = True
            for keyword in self.COMPOSITION_KEYWORDS["depth"]["en"]:
                if keyword in desc:
                    has_depth = True

        # Generate suggestions for missing composition elements
        suggestions = []
        if not has_thirds:
            suggestions.append(
                "Consider using rule of thirds for subject placement"
            )
        if not has_leading_lines:
            suggestions.append(
                "Add leading lines to guide viewer's eye"
            )
        if not has_depth:
            suggestions.append(
                "Use depth of field to add visual interest"
            )

        if suggestions:
            results.append(
                ValidationResult(
                    validator_name=self.name,
                    passed=True,
                    severity=ValidationSeverity.INFO,
                    message="Composition enhancement suggestions",
                    suggestions=suggestions,
                )
            )

        return results

    def _check_dialogue_visual_sync(
        self,
        frames: List[Dict[str, Any]],
    ) -> List[ValidationResult]:
        """Check dialogue-visual synchronization."""
        results: List[ValidationResult] = []
        sync_issues: List[Dict[str, Any]] = []

        for i, frame in enumerate(frames):
            dialogue = frame.get("dialogue", "") or frame.get("text", "")
            visual_desc = frame.get("visual_description", "")
            beat_type = frame.get("beat_type", "")

            # Check if dialogue frame has visual indication of speaking
            if dialogue and beat_type == "dialogue":
                has_speaking_visual = False

                for keyword in self.MOUTH_SPEAKING_KEYWORDS["zh"]:
                    if keyword in visual_desc:
                        has_speaking_visual = True
                        break

                for keyword in self.MOUTH_SPEAKING_KEYWORDS["en"]:
                    if keyword in visual_desc.lower():
                        has_speaking_visual = True
                        break

                if not has_speaking_visual:
                    # Check if character is even visible
                    characters = frame.get("characters", [])
                    if characters:
                        sync_issues.append({
                            "frame_number": frame.get("frame_number", i + 1),
                            "issue": "Character speaking but no mouth movement indicated",
                            "dialogue_excerpt": dialogue[:50] + "..."
                            if len(dialogue) > 50
                            else dialogue,
                        })

        if sync_issues:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message=(
                        f"Found {len(sync_issues)} frames with dialogue "
                        f"but no speaking indication in visuals"
                    ),
                    details={"issues": sync_issues[:5]},  # Limit to 5
                    suggestions=[
                        "Add visual cues like 'mouth open' or 'speaking' to dialogue frames",
                        "Ensure character faces are visible during dialogue",
                    ],
                )
            )

        return results

    def _extract_visual_elements(
        self, description: str, element_type: str
    ) -> Set[str]:
        """Extract visual elements of a specific type from description."""
        elements: Set[str] = set()
        desc_lower = description.lower()

        if element_type == "costume":
            keywords = (
                self.COSTUME_KEYWORDS["zh"] + self.COSTUME_KEYWORDS["en"]
            )
        elif element_type == "hairstyle":
            keywords = (
                self.HAIRSTYLE_KEYWORDS["zh"] + self.HAIRSTYLE_KEYWORDS["en"]
            )
        elif element_type == "props":
            keywords = self.PROP_KEYWORDS["zh"] + self.PROP_KEYWORDS["en"]
        else:
            return elements

        for keyword in keywords:
            if keyword in desc_lower:
                # Extract the phrase containing the keyword
                # Simple extraction - find keyword and nearby words
                pattern = rf"[^，。,.\s]*{re.escape(keyword)}[^，。,.\s]*"
                matches = re.findall(pattern, desc_lower)
                elements.update(matches)

        return elements

    def _extract_position(self, description: str) -> Optional[str]:
        """Extract position information from description."""
        desc_lower = description.lower()

        for position, keywords in self.POSITION_KEYWORDS["zh"].items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return position

        for position, keywords in self.POSITION_KEYWORDS["en"].items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return position

        return None

    def _extract_pose(self, description: str) -> Optional[str]:
        """Extract pose information from description."""
        desc_lower = description.lower()

        for pose, lang_keywords in self.POSE_KEYWORDS.items():
            for keyword in lang_keywords["zh"]:
                if keyword in desc_lower:
                    return pose
            for keyword in lang_keywords["en"]:
                if keyword in desc_lower:
                    return pose

        return None

    def _find_inconsistencies(
        self, elements: List[Tuple[int, Set[str]]]
    ) -> List[int]:
        """Find frames with inconsistent elements."""
        if len(elements) < 2:
            return []

        # Use first non-empty set as reference
        reference: Optional[Set[str]] = None
        ref_frame: Optional[int] = None
        for frame_num, elem_set in elements:
            if elem_set:
                reference = elem_set
                ref_frame = frame_num
                break

        if not reference:
            return []

        inconsistent_frames = []
        for frame_num, elem_set in elements:
            if not elem_set or frame_num == ref_frame:
                continue

            # Check if any keyword overlaps between sets
            # Use substring matching for better detection
            has_overlap = False
            for ref_elem in reference:
                for curr_elem in elem_set:
                    # Check if they share significant keywords
                    if self._elements_similar(ref_elem, curr_elem):
                        has_overlap = True
                        break
                if has_overlap:
                    break

            if not has_overlap:
                inconsistent_frames.append(frame_num)

        return inconsistent_frames

    def _elements_similar(self, elem1: str, elem2: str) -> bool:
        """Check if two extracted elements are similar enough."""
        # Extract core keywords (remove context)
        core_keywords = [
            # Costume
            "裙子", "西装", "衬衫", "外套", "裤子", "制服", "T恤",
            "dress", "suit", "shirt", "jacket", "pants", "uniform",
            # Colors
            "红色", "蓝色", "黑色", "白色", "绿色", "黄色",
            "red", "blue", "black", "white", "green", "yellow",
            # Hairstyle
            "长发", "短发", "卷发", "直发", "马尾",
            "long hair", "short hair", "ponytail",
        ]

        elem1_lower = elem1.lower()
        elem2_lower = elem2.lower()

        # Check for shared core keywords
        shared_keywords = []
        for kw in core_keywords:
            if kw in elem1_lower and kw in elem2_lower:
                shared_keywords.append(kw)

        if shared_keywords:
            return True

        # Fallback: check basic substring overlap
        # If one is substring of other, they're similar
        if elem1_lower in elem2_lower or elem2_lower in elem1_lower:
            return True

        return False

    def _find_disappearing_elements(
        self, elements: List[Tuple[int, Set[str]]]
    ) -> Set[str]:
        """Find elements that appear in one frame but not adjacent frames."""
        if len(elements) < 2:
            return set()

        disappearing: Set[str] = set()

        for i in range(1, len(elements) - 1):
            prev_set = elements[i - 1][1]
            curr_set = elements[i][1]
            next_set = elements[i + 1][1]

            # Elements in current but not in adjacent frames
            lone_elements = curr_set - prev_set - next_set
            disappearing.update(lone_elements)

        return disappearing

    def _is_teleportation(self, pos1: str, pos2: str) -> bool:
        """Check if position change represents teleportation."""
        # Define position relationships (adjacent positions)
        adjacent_positions = {
            "left": {"center"},
            "right": {"center"},
            "center": {"left", "right"},
            "foreground": {"center"},
            "background": {"center"},
        }

        # Teleportation = non-adjacent position change
        if pos1 == pos2:
            return False

        if pos2 in adjacent_positions.get(pos1, set()):
            return False

        # Left to right or foreground to background = teleportation
        if pos1 in ("left", "right") and pos2 in ("left", "right") and pos1 != pos2:
            return True

        if pos1 in ("foreground", "background") and pos2 in (
            "foreground",
            "background",
        ):
            if pos1 != pos2:
                return True

        return False

    def can_auto_fix(self) -> bool:
        """Visual continuity issues typically require human review."""
        return False
