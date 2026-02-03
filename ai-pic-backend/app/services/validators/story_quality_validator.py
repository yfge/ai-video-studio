"""Story Quality Validator - validates story structure, pacing, and content quality.

This validator ensures that generated stories:
1. Follow proper three-act structure with balanced proportions
2. Have good pacing with clear opening, climax, and resolution
3. Include effective hooks and cliffhangers
4. Maintain world-building consistency
5. Avoid prohibited content
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class StoryQualitySeverity(str, Enum):
    """Severity levels for story quality issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


class StoryQualityIssueType(str, Enum):
    """Types of story quality issues."""

    STRUCTURE_IMBALANCE = "structure_imbalance"
    PACING_ISSUE = "pacing_issue"
    WEAK_HOOK = "weak_hook"
    WEAK_CLIFFHANGER = "weak_cliffhanger"
    WORLDBUILDING_INCONSISTENCY = "worldbuilding_inconsistency"
    PROHIBITED_CONTENT = "prohibited_content"
    MISSING_ELEMENT = "missing_element"


@dataclass
class StoryQualityIssue:
    """A single story quality issue."""

    issue_type: StoryQualityIssueType
    severity: StoryQualitySeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    location: Optional[str] = None  # e.g., "episode_1", "act_2"

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "issue_type": self.issue_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
            "location": self.location,
        }


@dataclass
class ThreeActAnalysis:
    """Analysis of three-act structure."""

    act1_ratio: float  # Setup (typically 25%)
    act2_ratio: float  # Confrontation (typically 50%)
    act3_ratio: float  # Resolution (typically 25%)
    is_balanced: bool
    imbalance_details: str = ""


@dataclass
class PacingAnalysis:
    """Analysis of story pacing."""

    opening_score: float  # 0-1, how engaging is the opening
    buildup_score: float  # 0-1, tension building effectiveness
    climax_score: float  # 0-1, climax impact
    resolution_score: float  # 0-1, resolution satisfaction
    overall_score: float  # 0-1, overall pacing quality


@dataclass
class StoryQualityResult:
    """Complete story quality validation result."""

    passed: bool
    issues: List[StoryQualityIssue] = field(default_factory=list)
    three_act_analysis: Optional[ThreeActAnalysis] = None
    pacing_analysis: Optional[PacingAnalysis] = None
    hook_score: float = 0.0
    cliffhanger_score: float = 0.0
    worldbuilding_score: float = 0.0
    content_check_passed: bool = True

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "passed": self.passed,
            "issues": [i.to_dict() for i in self.issues],
            "three_act_analysis": {
                "act1_ratio": self.three_act_analysis.act1_ratio,
                "act2_ratio": self.three_act_analysis.act2_ratio,
                "act3_ratio": self.three_act_analysis.act3_ratio,
                "is_balanced": self.three_act_analysis.is_balanced,
            } if self.three_act_analysis else None,
            "pacing_analysis": {
                "opening_score": self.pacing_analysis.opening_score,
                "buildup_score": self.pacing_analysis.buildup_score,
                "climax_score": self.pacing_analysis.climax_score,
                "resolution_score": self.pacing_analysis.resolution_score,
                "overall_score": self.pacing_analysis.overall_score,
            } if self.pacing_analysis else None,
            "hook_score": self.hook_score,
            "cliffhanger_score": self.cliffhanger_score,
            "worldbuilding_score": self.worldbuilding_score,
            "content_check_passed": self.content_check_passed,
        }


class StoryQualityValidator:
    """Validates story quality including structure, pacing, and content.

    Provides comprehensive quality checks for generated stories to ensure
    they meet professional storytelling standards.
    """

    # Three-act structure ideal proportions
    ACT1_IDEAL = 0.25  # Setup: 25%
    ACT2_IDEAL = 0.50  # Confrontation: 50%
    ACT3_IDEAL = 0.25  # Resolution: 25%
    STRUCTURE_TOLERANCE = 0.10  # Allow 10% deviation

    # Hook quality indicators
    HOOK_KEYWORDS = {
        "strong": [
            "突然", "震惊", "意外", "神秘", "危机", "紧急", "发现",
            "sudden", "shocking", "mysterious", "crisis", "urgent", "discovery",
            "问题", "冲突", "秘密", "悬念", "疑问",
            "conflict", "secret", "suspense", "question",
        ],
        "weak": [
            "平静", "普通", "日常", "一如既往",
            "ordinary", "usual", "normal", "routine",
        ],
    }

    # Cliffhanger quality indicators
    CLIFFHANGER_KEYWORDS = {
        "strong": [
            "但是", "然而", "突然", "谁知", "没想到", "危险", "紧张",
            "but", "however", "suddenly", "unexpectedly", "danger", "tension",
            "悬念", "未知", "等待", "即将", "转折",
            "suspense", "unknown", "waiting", "turning point",
        ],
        "weak": [
            "结束", "完成", "解决", "平静",
            "ended", "completed", "resolved", "calm",
        ],
    }

    # Prohibited content patterns (simplified - real implementation would be more comprehensive)
    PROHIBITED_PATTERNS = [
        # Violence extremes
        r"详细.*?酷刑|torture.*?detail",
        r"虐待.*?儿童|child.*?abuse",
        # Illegal activities promotion
        r"如何.*?制造.*?毒品|how.*?make.*?drug",
        r"如何.*?制造.*?爆炸|how.*?make.*?explos",
    ]

    # Pacing keywords for analysis
    PACING_KEYWORDS = {
        "tension_build": [
            "紧张", "压力", "危机", "冲突", "对抗", "升级",
            "tension", "pressure", "crisis", "conflict", "escalate",
        ],
        "climax": [
            "高潮", "决战", "对决", "真相", "揭示", "爆发",
            "climax", "showdown", "confrontation", "truth", "reveal", "explosion",
        ],
        "resolution": [
            "解决", "和解", "结局", "收尾", "完结", "尾声",
            "resolve", "reconcile", "ending", "conclusion", "epilogue",
        ],
    }

    def __init__(self) -> None:
        """Initialize the validator."""
        self._worldbuilding_facts: Dict[str, str] = {}

    def validate(
        self,
        story: Dict[str, Any],
        hook_plan: Optional[Dict[str, Any]] = None,
        content_restrictions: Optional[List[str]] = None,
    ) -> StoryQualityResult:
        """Validate story quality comprehensively.

        Args:
            story: Story dict with outline, episodes, etc.
            hook_plan: Optional hook/cliffhanger plan to compare against
            content_restrictions: Optional list of additional content restrictions

        Returns:
            StoryQualityResult with all analysis results
        """
        issues: List[StoryQualityIssue] = []
        result = StoryQualityResult(passed=True, issues=issues)

        # Extract story content for analysis
        episodes = story.get("episodes", [])
        outline = story.get("outline", "") or story.get("summary", "")
        plot_points = story.get("plot_points", [])

        # 1. Three-act structure validation
        three_act = self._analyze_three_act_structure(story)
        result.three_act_analysis = three_act
        if not three_act.is_balanced:
            issues.append(
                StoryQualityIssue(
                    issue_type=StoryQualityIssueType.STRUCTURE_IMBALANCE,
                    severity=StoryQualitySeverity.WARNING,
                    message=f"三幕结构比例不均衡：{three_act.imbalance_details}",
                    details={
                        "act1_ratio": three_act.act1_ratio,
                        "act2_ratio": three_act.act2_ratio,
                        "act3_ratio": three_act.act3_ratio,
                    },
                    suggestions=[
                        "调整各幕内容比例，理想比例为 25%/50%/25%",
                        "第一幕应建立角色和世界观",
                        "第二幕应展开冲突和挑战",
                        "第三幕应解决冲突并收束",
                    ],
                )
            )

        # 2. Pacing analysis
        pacing = self._analyze_pacing(story)
        result.pacing_analysis = pacing
        if pacing.overall_score < 0.6:
            issues.append(
                StoryQualityIssue(
                    issue_type=StoryQualityIssueType.PACING_ISSUE,
                    severity=StoryQualitySeverity.WARNING,
                    message=f"节奏评分较低 ({pacing.overall_score:.0%})",
                    details={
                        "opening": pacing.opening_score,
                        "buildup": pacing.buildup_score,
                        "climax": pacing.climax_score,
                        "resolution": pacing.resolution_score,
                    },
                    suggestions=self._get_pacing_suggestions(pacing),
                )
            )

        # 3. Hook quality evaluation
        hook_score = self._evaluate_hook_quality(story, hook_plan)
        result.hook_score = hook_score
        if hook_score < 0.5:
            issues.append(
                StoryQualityIssue(
                    issue_type=StoryQualityIssueType.WEAK_HOOK,
                    severity=StoryQualitySeverity.WARNING,
                    message=f"开场吸引力不足 (评分: {hook_score:.0%})",
                    suggestions=[
                        "以冲突、悬念或意外事件开场",
                        "在前几句话中建立紧张感",
                        "引入引人入胜的问题或谜团",
                    ],
                )
            )

        # 4. Cliffhanger quality evaluation
        if episodes:
            cliffhanger_score = self._evaluate_cliffhanger_quality(episodes)
            result.cliffhanger_score = cliffhanger_score
            if cliffhanger_score < 0.5:
                issues.append(
                    StoryQualityIssue(
                        issue_type=StoryQualityIssueType.WEAK_CLIFFHANGER,
                        severity=StoryQualitySeverity.INFO,
                        message=f"剧集结尾悬念感不足 (评分: {cliffhanger_score:.0%})",
                        suggestions=[
                            "每集结尾留下未解决的问题",
                            "在关键时刻结束场景",
                            "引入新的冲突或转折",
                        ],
                    )
                )

        # 5. World-building consistency
        worldbuilding_score, wb_issues = self._check_worldbuilding_consistency(story)
        result.worldbuilding_score = worldbuilding_score
        issues.extend(wb_issues)

        # 6. Content restrictions check
        content_passed, content_issues = self._check_content_restrictions(
            story, content_restrictions
        )
        result.content_check_passed = content_passed
        issues.extend(content_issues)

        # Determine overall pass/fail
        error_count = sum(1 for i in issues if i.severity == StoryQualitySeverity.ERROR)
        result.passed = error_count == 0
        result.issues = issues

        return result

    def _analyze_three_act_structure(self, story: Dict[str, Any]) -> ThreeActAnalysis:
        """Analyze three-act structure balance.

        Args:
            story: Story dict

        Returns:
            ThreeActAnalysis with ratio information
        """
        episodes = story.get("episodes", [])
        total_episodes = len(episodes) if episodes else 1

        # Estimate act boundaries based on episode count
        # Or use explicit act markers if available
        act_markers = story.get("act_markers", {})

        if act_markers:
            act1_end = act_markers.get("act1_end", total_episodes // 4)
            act2_end = act_markers.get("act2_end", 3 * total_episodes // 4)
        else:
            # Default estimation
            act1_end = max(1, total_episodes // 4)
            act2_end = max(act1_end + 1, 3 * total_episodes // 4)

        act1_ratio = act1_end / total_episodes if total_episodes > 0 else 0.25
        act2_ratio = (act2_end - act1_end) / total_episodes if total_episodes > 0 else 0.50
        act3_ratio = (total_episodes - act2_end) / total_episodes if total_episodes > 0 else 0.25

        # Check balance
        act1_ok = abs(act1_ratio - self.ACT1_IDEAL) <= self.STRUCTURE_TOLERANCE
        act2_ok = abs(act2_ratio - self.ACT2_IDEAL) <= self.STRUCTURE_TOLERANCE
        act3_ok = abs(act3_ratio - self.ACT3_IDEAL) <= self.STRUCTURE_TOLERANCE

        is_balanced = act1_ok and act2_ok and act3_ok
        imbalance_details = ""
        if not is_balanced:
            parts = []
            if not act1_ok:
                parts.append(f"第一幕 {act1_ratio:.0%} (理想 {self.ACT1_IDEAL:.0%})")
            if not act2_ok:
                parts.append(f"第二幕 {act2_ratio:.0%} (理想 {self.ACT2_IDEAL:.0%})")
            if not act3_ok:
                parts.append(f"第三幕 {act3_ratio:.0%} (理想 {self.ACT3_IDEAL:.0%})")
            imbalance_details = "，".join(parts)

        return ThreeActAnalysis(
            act1_ratio=act1_ratio,
            act2_ratio=act2_ratio,
            act3_ratio=act3_ratio,
            is_balanced=is_balanced,
            imbalance_details=imbalance_details,
        )

    def _analyze_pacing(self, story: Dict[str, Any]) -> PacingAnalysis:
        """Analyze story pacing.

        Args:
            story: Story dict

        Returns:
            PacingAnalysis with scores
        """
        episodes = story.get("episodes", [])
        outline = story.get("outline", "") or story.get("summary", "")

        # Combine all text for analysis
        all_text = outline
        for ep in episodes:
            all_text += " " + str(ep.get("summary", ""))
            all_text += " " + str(ep.get("plot_points", ""))

        all_text_lower = all_text.lower()

        # Score opening (first 20% of content)
        opening_text = all_text[: len(all_text) // 5]
        opening_score = self._score_text_engagement(opening_text)

        # Score buildup (middle 50%)
        buildup_text = all_text[len(all_text) // 5 : 7 * len(all_text) // 10]
        buildup_keywords = self.PACING_KEYWORDS["tension_build"]
        buildup_score = self._count_keyword_density(buildup_text, buildup_keywords)

        # Score climax (around 70-80%)
        climax_text = all_text[7 * len(all_text) // 10 : 4 * len(all_text) // 5]
        climax_keywords = self.PACING_KEYWORDS["climax"]
        climax_score = self._count_keyword_density(climax_text, climax_keywords)

        # Score resolution (last 20%)
        resolution_text = all_text[4 * len(all_text) // 5 :]
        resolution_keywords = self.PACING_KEYWORDS["resolution"]
        resolution_score = self._count_keyword_density(resolution_text, resolution_keywords)

        # Overall score
        overall_score = (
            opening_score * 0.25
            + buildup_score * 0.25
            + climax_score * 0.30
            + resolution_score * 0.20
        )

        return PacingAnalysis(
            opening_score=min(1.0, opening_score),
            buildup_score=min(1.0, buildup_score),
            climax_score=min(1.0, climax_score),
            resolution_score=min(1.0, resolution_score),
            overall_score=min(1.0, overall_score),
        )

    def _score_text_engagement(self, text: str) -> float:
        """Score text engagement level.

        Args:
            text: Text to score

        Returns:
            Score between 0 and 1
        """
        if not text:
            return 0.0

        strong_count = sum(
            1 for kw in self.HOOK_KEYWORDS["strong"] if kw in text.lower()
        )
        weak_count = sum(
            1 for kw in self.HOOK_KEYWORDS["weak"] if kw in text.lower()
        )

        # Normalize score
        score = (strong_count - weak_count * 0.5) / max(1, len(text.split()) / 50)
        return max(0.0, min(1.0, score + 0.5))  # Baseline of 0.5

    def _count_keyword_density(self, text: str, keywords: List[str]) -> float:
        """Count keyword density in text.

        Args:
            text: Text to analyze
            keywords: Keywords to look for

        Returns:
            Density score between 0 and 1
        """
        if not text:
            return 0.0

        text_lower = text.lower()
        count = sum(1 for kw in keywords if kw in text_lower)
        word_count = max(1, len(text.split()))

        # Normalize: expect 1 keyword per 100 words for full score
        density = count / (word_count / 100)
        return min(1.0, density)

    def _get_pacing_suggestions(self, pacing: PacingAnalysis) -> List[str]:
        """Get suggestions based on pacing analysis.

        Args:
            pacing: Pacing analysis result

        Returns:
            List of suggestions
        """
        suggestions = []

        if pacing.opening_score < 0.5:
            suggestions.append("加强开场吸引力，以冲突或悬念开始")
        if pacing.buildup_score < 0.5:
            suggestions.append("增加第二幕的紧张感和冲突升级")
        if pacing.climax_score < 0.5:
            suggestions.append("强化高潮部分的戏剧性和冲击力")
        if pacing.resolution_score < 0.5:
            suggestions.append("确保结局有足够的收束感和满足感")

        return suggestions

    def _evaluate_hook_quality(
        self,
        story: Dict[str, Any],
        hook_plan: Optional[Dict[str, Any]],
    ) -> float:
        """Evaluate opening hook quality.

        Args:
            story: Story dict
            hook_plan: Optional hook plan to compare

        Returns:
            Quality score between 0 and 1
        """
        # Get opening content
        opening = story.get("opening", "") or story.get("summary", "")[:200]
        episodes = story.get("episodes", [])
        if episodes:
            first_ep = episodes[0]
            opening += " " + str(first_ep.get("summary", ""))[:200]

        # Score based on keywords
        score = self._score_text_engagement(opening)

        # Compare with hook_plan if provided
        if hook_plan:
            planned_hooks = hook_plan.get("hooks", [])
            for hook in planned_hooks:
                if isinstance(hook, str) and hook.lower() in opening.lower():
                    score += 0.1  # Bonus for matching planned hooks

        return min(1.0, score)

    def _evaluate_cliffhanger_quality(self, episodes: List[Dict[str, Any]]) -> float:
        """Evaluate cliffhanger quality across episodes.

        Args:
            episodes: List of episode dicts

        Returns:
            Average cliffhanger quality score
        """
        if not episodes:
            return 0.5

        scores = []
        for ep in episodes[:-1]:  # Exclude last episode
            ending = ep.get("ending", "") or ep.get("summary", "")[-200:]

            strong_count = sum(
                1 for kw in self.CLIFFHANGER_KEYWORDS["strong"]
                if kw in ending.lower()
            )
            weak_count = sum(
                1 for kw in self.CLIFFHANGER_KEYWORDS["weak"]
                if kw in ending.lower()
            )

            score = 0.5 + (strong_count - weak_count) * 0.1
            scores.append(max(0.0, min(1.0, score)))

        return sum(scores) / len(scores) if scores else 0.5

    def _check_worldbuilding_consistency(
        self, story: Dict[str, Any]
    ) -> tuple[float, List[StoryQualityIssue]]:
        """Check world-building consistency.

        Args:
            story: Story dict

        Returns:
            Tuple of (score, list of issues)
        """
        issues: List[StoryQualityIssue] = []
        score = 1.0

        # Extract world-building elements
        setting = story.get("setting", {})
        world = story.get("world", {})
        rules = story.get("rules", []) or story.get("world_rules", [])

        # Check for contradictory settings
        time_period = setting.get("time_period", "")
        technology = setting.get("technology", [])

        # Simple consistency checks
        if time_period:
            if "古代" in time_period or "ancient" in time_period.lower():
                modern_tech = ["手机", "电脑", "网络", "phone", "computer", "internet"]
                for tech in modern_tech:
                    for t in technology if isinstance(technology, list) else []:
                        if tech in str(t).lower():
                            issues.append(
                                StoryQualityIssue(
                                    issue_type=StoryQualityIssueType.WORLDBUILDING_INCONSISTENCY,
                                    severity=StoryQualitySeverity.WARNING,
                                    message=f"世界观矛盾：古代设定中出现现代科技 '{t}'",
                                    suggestions=["移除不符合时代设定的元素", "调整时代设定"],
                                )
                            )
                            score -= 0.2

        return max(0.0, score), issues

    def _check_content_restrictions(
        self,
        story: Dict[str, Any],
        additional_restrictions: Optional[List[str]] = None,
    ) -> tuple[bool, List[StoryQualityIssue]]:
        """Check for prohibited content.

        Args:
            story: Story dict
            additional_restrictions: Additional content patterns to check

        Returns:
            Tuple of (passed, list of issues)
        """
        issues: List[StoryQualityIssue] = []
        passed = True

        # Combine all story text
        all_text = str(story)

        # Check built-in prohibited patterns
        for pattern in self.PROHIBITED_PATTERNS:
            if re.search(pattern, all_text, re.IGNORECASE):
                issues.append(
                    StoryQualityIssue(
                        issue_type=StoryQualityIssueType.PROHIBITED_CONTENT,
                        severity=StoryQualitySeverity.ERROR,
                        message="检测到禁止内容",
                        details={"pattern": pattern},
                        suggestions=["移除违规内容", "修改相关描述"],
                    )
                )
                passed = False

        # Check additional restrictions
        if additional_restrictions:
            for restriction in additional_restrictions:
                if restriction.lower() in all_text.lower():
                    issues.append(
                        StoryQualityIssue(
                            issue_type=StoryQualityIssueType.PROHIBITED_CONTENT,
                            severity=StoryQualitySeverity.WARNING,
                            message=f"内容包含受限关键词: {restriction}",
                            suggestions=["检查并修改相关内容"],
                        )
                    )

        return passed, issues
