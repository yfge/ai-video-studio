from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

STRONG_HOOK_KEYWORDS = (
    "突然",
    "震惊",
    "意外",
    "危机",
    "紧急",
    "发现",
    "冲突",
    "秘密",
    "悬念",
    "背叛",
    "羞辱",
    "真相",
)
WEAK_HOOK_KEYWORDS = ("平静", "普通", "日常", "一如既往")
TENSION_KEYWORDS = ("紧张", "压力", "危机", "冲突", "对抗", "升级")
CLIMAX_KEYWORDS = ("高潮", "决战", "对决", "真相", "揭示", "爆发")
RESOLUTION_KEYWORDS = ("解决", "和解", "结局", "收束", "完结", "尾声")
PROHIBITED_PATTERNS = (
    r"详细.*?酷刑|torture.*?detail",
    r"虐待.*?儿童|child.*?abuse",
    r"如何.*?制造.*?毒品|how.*?make.*?drug",
    r"如何.*?制造.*?爆炸|how.*?make.*?explos",
)


def _text_from_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(
            text for text in (_text_from_value(v) for v in value.values()) if text
        )
    if isinstance(value, list):
        return " ".join(text for text in (_text_from_value(v) for v in value) if text)
    return str(value)


def _score_hook_text(text: str) -> float:
    if not text:
        return 0.0
    lowered = text.lower()
    strong = sum(1 for keyword in STRONG_HOOK_KEYWORDS if keyword in lowered)
    weak = sum(1 for keyword in WEAK_HOOK_KEYWORDS if keyword in lowered)
    score = 0.5 + strong * 0.15 - weak * 0.25
    return max(0.0, min(1.0, score))


def _keyword_score(text: str, keywords: tuple[str, ...]) -> float:
    if not text:
        return 0.0
    lowered = text.lower()
    hits = sum(1 for keyword in keywords if keyword in lowered)
    return min(1.0, hits * 0.35)


def _outline_pacing_scores(story: Dict[str, Any]) -> Dict[str, float]:
    plot_structure = (
        story.get("plot_structure")
        if isinstance(story.get("plot_structure"), dict)
        else {}
    )
    hook_plan = (
        story.get("hook_plan") if isinstance(story.get("hook_plan"), dict) else {}
    )

    opening_text = " ".join(
        part
        for part in (
            _text_from_value(hook_plan.get("opening_hook")),
            _text_from_value(plot_structure.get("act1")),
            _text_from_value(story.get("premise")),
            _text_from_value(story.get("synopsis"))[:200],
        )
        if part
    )
    buildup_text = " ".join(
        part
        for part in (
            _text_from_value(plot_structure.get("act2")),
            _text_from_value(story.get("main_conflict")),
            _text_from_value(hook_plan.get("escalation_plan")),
        )
        if part
    )
    climax_text = " ".join(
        part
        for part in (
            _text_from_value(plot_structure.get("act3")),
            _text_from_value(story.get("resolution")),
            _text_from_value(hook_plan.get("payoff_plan")),
            _text_from_value(story.get("synopsis")),
        )
        if part
    )
    resolution_text = " ".join(
        part
        for part in (
            _text_from_value(story.get("resolution")),
            _text_from_value(plot_structure.get("act3")),
        )
        if part
    )

    opening = _score_hook_text(opening_text)
    buildup = _keyword_score(buildup_text, TENSION_KEYWORDS)
    climax = _keyword_score(climax_text, CLIMAX_KEYWORDS)
    resolution = _keyword_score(resolution_text, RESOLUTION_KEYWORDS)
    overall = opening * 0.25 + buildup * 0.25 + climax * 0.30 + resolution * 0.20
    return {
        "opening_score": opening,
        "buildup_score": buildup,
        "climax_score": climax,
        "resolution_score": resolution,
        "overall_score": min(1.0, overall),
    }


def _hook_score(story: Dict[str, Any], hook_plan: Optional[Dict[str, Any]]) -> float:
    generated_hook_plan = (
        story.get("hook_plan") if isinstance(story.get("hook_plan"), dict) else {}
    )
    opening = (
        _text_from_value(generated_hook_plan.get("opening_hook"))
        or _text_from_value(story.get("premise"))
        or _text_from_value(story.get("synopsis"))[:200]
    )
    score = _score_hook_text(opening)
    if hook_plan and hook_plan.get("opening_hook"):
        score = max(score, _score_hook_text(str(hook_plan["opening_hook"])))
    return score


def _content_restriction_issues(
    story: Dict[str, Any], restrictions: Optional[List[str]]
) -> List[Dict[str, Any]]:
    text = _text_from_value(story)
    issues: List[Dict[str, Any]] = []
    for pattern in PROHIBITED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append({"issue_type": "prohibited_content", "message": pattern})
    for restriction in restrictions or []:
        if restriction and restriction in text:
            issues.append(
                {
                    "issue_type": "prohibited_content",
                    "message": f"包含限制内容: {restriction}",
                }
            )
    return issues


def validate_story_outline_quality(
    parsed: Dict[str, Any],
    hook_plan: Optional[Dict[str, Any]] = None,
    content_restrictions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    pacing = _outline_pacing_scores(parsed)
    hook = _hook_score(parsed, hook_plan)
    issues: List[Dict[str, Any]] = []
    if pacing["overall_score"] < 0.6:
        issues.append(
            {
                "issue_type": "pacing_issue",
                "severity": "error",
                "message": f"节奏评分较低 ({pacing['overall_score']:.0%})",
                "details": pacing,
            }
        )
    if hook < 0.5:
        issues.append(
            {
                "issue_type": "weak_hook",
                "severity": "error",
                "message": f"开场吸引力不足 (评分: {hook:.0%})",
            }
        )
    issues.extend(_content_restriction_issues(parsed, content_restrictions))
    passed = not issues
    return {
        "story_quality_passed": passed,
        "story_quality_result": {
            "passed": passed,
            "issues": issues,
            "pacing_analysis": pacing,
            "hook_score": hook,
        },
        "story_quality_warnings": [issue["message"] for issue in issues],
    }
