from __future__ import annotations

from app.schemas.script_quality import (
    ScriptLintIssue,
    ScriptLintOptions,
    ScriptLintRuleResult,
)
from app.services.script_quality.constants import (
    COMMERCIAL_ACTION_MARKERS,
    EMOTION_TAG_KEYWORDS,
    HOOK_MARKERS,
    SCENE_HEADER_RE,
    SFX_TAG_KEYWORDS,
    TEMPO_TAGS,
)
from app.services.script_quality.cliffhanger import check_cliffhanger
from app.services.script_quality.utils import estimate_visible_chars
from app.services.script_quality.visual_language import check_visual_language


def check_scene_headers(
    non_empty: list[tuple[int, str]],
) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    has_scene_headers = any(SCENE_HEADER_RE.search(ln) for _no, ln in non_empty)
    issues: list[ScriptLintIssue] = []
    if not has_scene_headers:
        issues.append(
            ScriptLintIssue(
                severity="info",
                rule_id="scene_headers",
                message="未检测到明确的场次/场景标记（建议使用 [第1场] / 场景1 / INT./EXT.）。",
                suggestion="补充场次/场景头部，便于分镜/制作拆解。",
            )
        )
    return (
        ScriptLintRuleResult(
            rule_id="scene_headers",
            title="场次/场景标记",
            weight=0.25,
            score=1.0 if has_scene_headers else 0.5,
            passed=has_scene_headers,
            details={"detected": has_scene_headers},
        ),
        issues,
    )

def check_tempo_tags(
    all_tags: list[str],
    non_empty: list[tuple[int, str]],
) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    has_tempo = any(
        any(tag.startswith(k) or k in tag for k in TEMPO_TAGS) for tag in all_tags
    )
    has_commercial_pacing = (
        sum(
            1
            for _no, ln in non_empty
            if ln.startswith("▲")
            or any(marker in ln for marker in COMMERCIAL_ACTION_MARKERS)
        )
        >= 2
    )
    issues: list[ScriptLintIssue] = []
    if not has_tempo and not has_commercial_pacing:
        issues.append(
            ScriptLintIssue(
                severity="warn",
                rule_id="pacing_markers",
                message="未检测到【快/慢】节奏标注或商用正文动作标记。",
                suggestion="使用【快/慢】或 `▲动作/镜头/音效` 标记关键节奏点。",
            )
        )
    return (
        ScriptLintRuleResult(
            rule_id="pacing_markers",
            title="节奏区/商用动作标记",
            weight=1.0,
            score=1.0 if (has_tempo or has_commercial_pacing) else 0.0,
            passed=has_tempo or has_commercial_pacing,
            details={
                "tempo_tags": has_tempo,
                "commercial_action_markers": has_commercial_pacing,
            },
        ),
        issues,
    )


def check_emotion_goal(
    all_tags: list[str],
    dialogue_lines: list[tuple[int, str, str]],
) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    has_emotion_goal = any(
        any(k in tag for k in EMOTION_TAG_KEYWORDS) for tag in all_tags
    )
    has_dialogue_state = any(
        "(" in ln and ")" in ln.split("：", 1)[0] for _no, ln, _c in dialogue_lines
    )
    issues: list[ScriptLintIssue] = []
    if not has_emotion_goal and not has_dialogue_state:
        issues.append(
            ScriptLintIssue(
                severity="warn",
                rule_id="emotion_goal",
                message="未检测到【情绪目的】标注或角色状态括注。",
                suggestion="用【情绪目的】或 `角色(状态)：对白` 标清表演状态。",
            )
        )
    return (
        ScriptLintRuleResult(
            rule_id="emotion_goal",
            title="情绪目的/角色状态",
            weight=0.5,
            score=1.0 if (has_emotion_goal or has_dialogue_state) else 0.0,
            passed=has_emotion_goal or has_dialogue_state,
            details={
                "emotion_goal_tag": has_emotion_goal,
                "dialogue_state": has_dialogue_state,
            },
        ),
        issues,
    )


def check_sfx_lines(
    stage_lines: list[tuple[int, str]],
) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    has_sfx = any(
        any(k in ln for k in SFX_TAG_KEYWORDS)
        or any(marker in ln for marker in COMMERCIAL_ACTION_MARKERS)
        for _no, ln in stage_lines
    )
    issues: list[ScriptLintIssue] = []
    if not has_sfx:
        issues.append(
            ScriptLintIssue(
                severity="info",
                rule_id="sfx_lines",
                message="未检测到明确的【音效/氛围音】或商用动作/镜头行。",
                suggestion="关键节拍前置音效或 `▲动作/镜头` 行，便于制作拆解。",
            )
        )
    return (
        ScriptLintRuleResult(
            rule_id="sfx_lines",
            title="音效/动作/镜头行",
            weight=0.25,
            score=1.0 if has_sfx else 0.5,
            passed=has_sfx,
            details={"detected": has_sfx},
        ),
        issues,
    )


def check_hook_3s(
    non_empty: list[tuple[int, str]],
) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    first_five = [ln for _no, ln in non_empty[:5]]
    has_hook = any(any(m in ln for m in HOOK_MARKERS) for ln in first_five)
    issues: list[ScriptLintIssue] = []
    if not has_hook:
        issues.append(
            ScriptLintIssue(
                severity="error",
                rule_id="hook_3s",
                message="前五行未检测到强钩子（冲突/惊呼/命令/巨响）。",
                suggestion="用“质问/耳光/摔杯/警报”等强事件开场，禁止寒暄。",
            )
        )
    return (
        ScriptLintRuleResult(
            rule_id="hook_3s",
            title="黄金3秒钩子（前五行）",
            weight=1.5,
            score=1.0 if has_hook else 0.0,
            passed=has_hook,
            details={"detected": has_hook},
        ),
        issues,
    )


def check_dialogue_length(
    dialogue_lines: list[tuple[int, str, str]],
    options: ScriptLintOptions,
) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    too_long = []
    issues: list[ScriptLintIssue] = []
    for ln_no, ln, content in dialogue_lines:
        length = estimate_visible_chars(content)
        if length > options.max_dialogue_chars:
            too_long.append((ln_no, ln, length))
            issues.append(
                ScriptLintIssue(
                    severity="warn",
                    rule_id="dialogue_length",
                    message=f"台词过长（>{options.max_dialogue_chars} 字）：{length} 字",
                    line=ln_no,
                    excerpt=ln[:120],
                    suggestion="拆成短句/打断/抢白，或改为动作表达。",
                )
            )

    score_dialogue = (
        1.0 if not too_long else max(0.0, 1.0 - min(1.0, len(too_long) / 3.0))
    )
    return (
        ScriptLintRuleResult(
            rule_id="dialogue_length",
            title=f"台词长度（≤{options.max_dialogue_chars}字）",
            weight=2.0,
            score=score_dialogue,
            passed=len(too_long) == 0,
            details={"too_long_lines": len(too_long)},
        ),
        issues,
    )
