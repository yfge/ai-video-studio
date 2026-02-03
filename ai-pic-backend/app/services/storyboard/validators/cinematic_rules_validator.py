"""
Cinematic rules validator.

Validates that storyboard frames follow basic filmmaking rules:
- 180-degree rule: Camera stays on one side of the axis line
- Shot scale distribution: Variety in shot types (not all close-ups or wide shots)
- Lighting continuity: Day/night consistency within scenes
"""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from app.services.storyboard.pipeline.pipeline_state import (
    ValidationResult,
    ValidationSeverity,
)

if TYPE_CHECKING:
    from app.services.storyboard.pipeline.pipeline_context import PipelineContext
    from app.services.storyboard.pipeline.pipeline_state import PipelineState


class CinematicRulesValidator:
    """
    Validates that storyboard frames follow basic cinematic rules.

    Checks:
    1. 180-degree rule: Camera position consistency in dialogue scenes
    2. Shot scale distribution: Variety in close-up/medium/wide shots
    3. Lighting continuity: Day/night consistency within scenes
    4. Shot rhythm: Avoiding jump cuts and monotonous sequences
    """

    # Shot types for classification
    SHOT_TYPES = {
        "extreme_close_up": [
            "extreme close-up", "extreme closeup", "ECU",
            "特写", "大特写", "超特写",
        ],
        "close_up": [
            "close-up", "closeup", "close up", "CU",
            "近景", "特写镜头",
        ],
        "medium_close_up": [
            "medium close-up", "MCU", "medium closeup",
            "中近景",
        ],
        "medium": [
            "medium shot", "MS", "waist shot",
            "中景", "半身",
        ],
        "medium_wide": [
            "medium wide", "MWS", "medium long",
            "中全景",
        ],
        "wide": [
            "wide shot", "WS", "full shot", "long shot", "LS",
            "全景", "远景", "广角",
        ],
        "extreme_wide": [
            "extreme wide", "EWS", "establishing",
            "大全景", "极远景", "建立镜头",
        ],
    }

    # Camera positions for 180-degree rule
    CAMERA_POSITIONS = {
        "left": ["left", "左侧", "左边", "screen left"],
        "right": ["right", "右侧", "右边", "screen right"],
        "center": ["center", "中间", "正面", "front"],
        "over_shoulder_left": ["OTS left", "过肩左", "左过肩"],
        "over_shoulder_right": ["OTS right", "过肩右", "右过肩"],
    }

    # Lighting keywords
    LIGHTING_DAY = [
        "day", "daylight", "daytime", "morning", "afternoon", "noon",
        "白天", "日光", "早晨", "上午", "下午", "正午", "阳光",
    ]
    LIGHTING_NIGHT = [
        "night", "nighttime", "evening", "midnight", "dark",
        "夜晚", "夜间", "傍晚", "深夜", "黑暗", "月光",
    ]

    # Minimum shot variety threshold (percentage of dominant shot type)
    SHOT_VARIETY_THRESHOLD = 0.6  # If one type > 60%, warn about lack of variety

    @property
    def name(self) -> str:
        return "cinematic_rules_validator"

    @property
    def description(self) -> str:
        return "Validates 180-degree rule, shot variety, and lighting continuity"

    def validate(
        self,
        state: "PipelineState",
        context: "PipelineContext",
        **kwargs: Any,
    ) -> list[ValidationResult]:
        """Run all cinematic rule checks."""
        results: list[ValidationResult] = []

        frames = state.frames
        if not frames:
            results.append(
                ValidationResult.warning(
                    validator_name=self.name,
                    message="No frames to validate cinematic rules",
                    details={"frame_count": 0},
                )
            )
            return results

        # Group frames by scene
        scenes = self._group_frames_by_scene(frames)

        # Run checks
        results.extend(self._check_180_degree_rule(scenes))
        results.extend(self._check_shot_variety(scenes))
        results.extend(self._check_lighting_continuity(scenes))
        results.extend(self._check_shot_rhythm(scenes))

        # Add success result if no issues
        if all(r.passed for r in results):
            results.append(
                ValidationResult.success(
                    validator_name=self.name,
                    message="All cinematic rules validated successfully",
                    details={"total_frames": len(frames), "total_scenes": len(scenes)},
                )
            )

        return results

    def _group_frames_by_scene(
        self, frames: List[Dict[str, Any]]
    ) -> Dict[int, List[Dict[str, Any]]]:
        """Group frames by scene number."""
        scenes: Dict[int, List[Dict[str, Any]]] = {}
        for frame in frames:
            scene_num = frame.get("scene_number", 0)
            if scene_num not in scenes:
                scenes[scene_num] = []
            scenes[scene_num].append(frame)
        return scenes

    def _classify_shot_type(self, frame: Dict[str, Any]) -> Optional[str]:
        """Classify frame's shot type from description or metadata."""
        # Check explicit shot_type field first
        shot_type = frame.get("shot_type", "")
        if shot_type:
            shot_lower = shot_type.lower()
            for category, keywords in self.SHOT_TYPES.items():
                for kw in keywords:
                    if kw.lower() in shot_lower:
                        return category

        # Fall back to description analysis
        description = frame.get("description", "")
        desc_lower = description.lower()

        for category, keywords in self.SHOT_TYPES.items():
            for kw in keywords:
                if kw.lower() in desc_lower:
                    return category

        return None

    def _detect_camera_position(self, frame: Dict[str, Any]) -> Optional[str]:
        """Detect camera position from frame description or metadata."""
        # Check explicit camera_position field
        cam_pos = frame.get("camera_position", "") or frame.get("camera_angle", "")
        if cam_pos:
            pos_lower = cam_pos.lower()
            for position, keywords in self.CAMERA_POSITIONS.items():
                for kw in keywords:
                    if kw.lower() in pos_lower:
                        return position

        # Analyze description
        description = frame.get("description", "")
        desc_lower = description.lower()

        for position, keywords in self.CAMERA_POSITIONS.items():
            for kw in keywords:
                if kw.lower() in desc_lower:
                    return position

        return None

    def _detect_lighting(self, frame: Dict[str, Any]) -> Optional[str]:
        """Detect lighting conditions from frame description or metadata."""
        # Check explicit lighting field
        lighting = frame.get("lighting", "") or frame.get("time_of_day", "")
        description = frame.get("description", "")
        combined = f"{lighting} {description}".lower()

        # Check for day indicators
        for kw in self.LIGHTING_DAY:
            if kw.lower() in combined:
                return "day"

        # Check for night indicators
        for kw in self.LIGHTING_NIGHT:
            if kw.lower() in combined:
                return "night"

        return None

    def _check_180_degree_rule(
        self, scenes: Dict[int, List[Dict[str, Any]]]
    ) -> List[ValidationResult]:
        """
        Check 180-degree rule violations.

        In a dialogue scene, if the camera crosses the axis line (the imaginary
        line connecting two characters), it creates disorienting screen direction
        changes.
        """
        results: List[ValidationResult] = []

        for scene_num, frames in scenes.items():
            if len(frames) < 2:
                continue

            # Track character positions established in the scene
            established_positions: Dict[str, str] = {}  # character -> screen position
            violations: List[Tuple[int, str]] = []

            for i, frame in enumerate(frames):
                description = frame.get("description", "")

                # Extract character mentions and their positions
                current_positions = self._extract_character_positions(description)

                for char, pos in current_positions.items():
                    if char in established_positions:
                        # Check for position flip (left <-> right)
                        prev_pos = established_positions[char]
                        if self._is_position_flip(prev_pos, pos):
                            violations.append((i, f"{char}: {prev_pos} → {pos}"))
                    else:
                        established_positions[char] = pos

            if violations:
                results.append(
                    ValidationResult(
                        validator_name=self.name,
                        passed=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"场景 {scene_num}: 可能违反180度规则，角色位置跳跃",
                        details={
                            "scene_number": scene_num,
                            "violations": violations,
                        },
                        suggestions=[
                            "检查分镜描述中的角色位置是否一致",
                            "确保同一对话场景中相机不跨越轴线",
                            "考虑添加过渡镜头（如中性镜头）来合理化位置变化",
                        ],
                    )
                )

        return results

    def _extract_character_positions(
        self, description: str
    ) -> Dict[str, str]:
        """Extract character names and their screen positions from description."""
        positions: Dict[str, str] = {}

        # Patterns like "张三在画面左侧" or "Li on the right"
        patterns = [
            r"(\w+).*?(在|位于|stands on|on the)\s*(左|右|left|right)",
            r"(左|右|left|right).*?的\s*(\w+)",
        ]

        desc_lower = description.lower()
        for position, keywords in self.CAMERA_POSITIONS.items():
            if "left" in position:
                for kw in keywords:
                    if kw.lower() in desc_lower:
                        # Try to find associated character
                        match = re.search(
                            rf"(\w{{2,}}).*?{re.escape(kw)}|{re.escape(kw)}.*?(\w{{2,}})",
                            description,
                            re.IGNORECASE,
                        )
                        if match:
                            char = match.group(1) or match.group(2)
                            if char and len(char) >= 2:
                                positions[char] = "left"
            elif "right" in position:
                for kw in keywords:
                    if kw.lower() in desc_lower:
                        match = re.search(
                            rf"(\w{{2,}}).*?{re.escape(kw)}|{re.escape(kw)}.*?(\w{{2,}})",
                            description,
                            re.IGNORECASE,
                        )
                        if match:
                            char = match.group(1) or match.group(2)
                            if char and len(char) >= 2:
                                positions[char] = "right"

        return positions

    def _is_position_flip(self, pos1: str, pos2: str) -> bool:
        """Check if two positions represent a left-right flip."""
        left_positions = {"left", "over_shoulder_left"}
        right_positions = {"right", "over_shoulder_right"}

        is_pos1_left = pos1 in left_positions
        is_pos1_right = pos1 in right_positions
        is_pos2_left = pos2 in left_positions
        is_pos2_right = pos2 in right_positions

        return (is_pos1_left and is_pos2_right) or (is_pos1_right and is_pos2_left)

    def _check_shot_variety(
        self, scenes: Dict[int, List[Dict[str, Any]]]
    ) -> List[ValidationResult]:
        """
        Check shot scale variety within scenes.

        Warns if a scene has too many shots of the same type (e.g., all close-ups).
        """
        results: List[ValidationResult] = []

        for scene_num, frames in scenes.items():
            if len(frames) < 3:
                continue  # Too few frames to meaningfully check variety

            shot_types = []
            for frame in frames:
                shot_type = self._classify_shot_type(frame)
                if shot_type:
                    shot_types.append(shot_type)

            if not shot_types:
                results.append(
                    ValidationResult.warning(
                        validator_name=self.name,
                        message=f"场景 {scene_num}: 无法识别镜头景别",
                        details={"scene_number": scene_num, "frame_count": len(frames)},
                        suggestions=[
                            "在分镜描述中明确标注景别（特写/中景/全景）",
                            "使用 shot_type 字段指定镜头类型",
                        ],
                    )
                )
                continue

            # Check distribution
            counter = Counter(shot_types)
            most_common_type, most_common_count = counter.most_common(1)[0]
            ratio = most_common_count / len(shot_types)

            if ratio > self.SHOT_VARIETY_THRESHOLD:
                results.append(
                    ValidationResult(
                        validator_name=self.name,
                        passed=True,  # Warning, not error
                        severity=ValidationSeverity.WARNING,
                        message=f"场景 {scene_num}: 景别缺乏变化，{most_common_type} 占比 {ratio:.0%}",
                        details={
                            "scene_number": scene_num,
                            "dominant_type": most_common_type,
                            "ratio": ratio,
                            "distribution": dict(counter),
                        },
                        suggestions=[
                            "增加景别变化以丰富视觉节奏",
                            f"减少 {most_common_type} 的使用，添加其他景别",
                            "考虑在对话场景中交替使用近景和中景",
                        ],
                    )
                )

        return results

    def _check_lighting_continuity(
        self, scenes: Dict[int, List[Dict[str, Any]]]
    ) -> List[ValidationResult]:
        """
        Check lighting continuity within scenes.

        Detects sudden day/night changes without transition.
        """
        results: List[ValidationResult] = []

        for scene_num, frames in scenes.items():
            if len(frames) < 2:
                continue

            prev_lighting: Optional[str] = None
            for i, frame in enumerate(frames):
                current_lighting = self._detect_lighting(frame)
                if current_lighting and prev_lighting:
                    if current_lighting != prev_lighting:
                        results.append(
                            ValidationResult(
                                validator_name=self.name,
                                passed=False,
                                severity=ValidationSeverity.ERROR,
                                message=f"场景 {scene_num} 帧 {i}: 光线突变 ({prev_lighting} → {current_lighting})",
                                details={
                                    "scene_number": scene_num,
                                    "frame_index": i,
                                    "from_lighting": prev_lighting,
                                    "to_lighting": current_lighting,
                                },
                                suggestions=[
                                    "确保同一场景内光线条件一致",
                                    "如需日夜变化，添加过渡场景或时间标记",
                                    "检查分镜描述中的光线/时间关键词",
                                ],
                            )
                        )
                if current_lighting:
                    prev_lighting = current_lighting

        return results

    def _check_shot_rhythm(
        self, scenes: Dict[int, List[Dict[str, Any]]]
    ) -> List[ValidationResult]:
        """
        Check shot rhythm to avoid jump cuts.

        Jump cuts occur when two similar shots are placed consecutively,
        creating a jarring visual effect.
        """
        results: List[ValidationResult] = []

        for scene_num, frames in scenes.items():
            if len(frames) < 2:
                continue

            consecutive_same = 0
            prev_shot_type: Optional[str] = None
            jump_cut_warnings: List[int] = []

            for i, frame in enumerate(frames):
                shot_type = self._classify_shot_type(frame)
                if shot_type:
                    if shot_type == prev_shot_type:
                        consecutive_same += 1
                        if consecutive_same >= 3:
                            jump_cut_warnings.append(i)
                    else:
                        consecutive_same = 0
                    prev_shot_type = shot_type

            if jump_cut_warnings:
                results.append(
                    ValidationResult.warning(
                        validator_name=self.name,
                        message=f"场景 {scene_num}: 连续使用相同景别可能造成跳切感",
                        details={
                            "scene_number": scene_num,
                            "problem_frames": jump_cut_warnings,
                            "consecutive_same_type": consecutive_same,
                        },
                        suggestions=[
                            "在相同景别之间插入不同景别的镜头",
                            "使用过渡镜头打破单调节奏",
                            "考虑使用运动镜头增加动态感",
                        ],
                    )
                )

        return results

    def can_auto_fix(self) -> bool:
        """This validator provides suggestions but cannot auto-fix."""
        return False
