from __future__ import annotations

from app.schemas.script_quality import ScriptLintIssue, ScriptLintOptions, ScriptLintRuleResult
from app.services.script_quality.constants import (
    EMOTION_TAG_KEYWORDS,
    HOOK_MARKERS,
    SCENE_HEADER_RE,
    SFX_TAG_KEYWORDS,
    TEMPO_TAGS,
    UNFILMABLE_PHRASES,
)
from app.services.script_quality.utils import estimate_visible_chars, is_dialogue


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


def check_tempo_tags(all_tags: list[str]) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    has_tempo = any(any(tag.startswith(k) or k in tag for k in TEMPO_TAGS) for tag in all_tags)
    issues: list[ScriptLintIssue] = []
    if not has_tempo:
        issues.append(
            ScriptLintIssue(
                severity="warn",
                rule_id="tempo_tags",
                message="未检测到【快/慢】或【加速区/减速区】标注。",
                suggestion="在打斗/争吵段落标【快】，情绪酝酿段落标【慢】。",
            )
        )
    return (
        ScriptLintRuleResult(
            rule_id="tempo_tags",
            title="【快/慢】节奏区标注",
            weight=1.0,
            score=1.0 if has_tempo else 0.0,
            passed=has_tempo,
            details={"detected": has_tempo},
        ),
        issues,
    )


def check_emotion_goal(all_tags: list[str]) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    has_emotion_goal = any(any(k in tag for k in EMOTION_TAG_KEYWORDS) for tag in all_tags)
    issues: list[ScriptLintIssue] = []
    if not has_emotion_goal:
        issues.append(
            ScriptLintIssue(
                severity="warn",
                rule_id="emotion_goal",
                message="未检测到【情绪目的】/【情绪目标】标注。",
                suggestion="每个 Beat 标注本段的情绪目的（恐惧/诱惑/羞辱/反击等）。",
            )
        )
    return (
        ScriptLintRuleResult(
            rule_id="emotion_goal",
            title="【情绪目的】标注",
            weight=0.5,
            score=1.0 if has_emotion_goal else 0.0,
            passed=has_emotion_goal,
            details={"detected": has_emotion_goal},
        ),
        issues,
    )


def check_sfx_lines(
    stage_lines: list[tuple[int, str]],
) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    has_sfx = any(any(k in ln for k in SFX_TAG_KEYWORDS) for _no, ln in stage_lines)
    issues: list[ScriptLintIssue] = []
    if not has_sfx:
        issues.append(
            ScriptLintIssue(
                severity="info",
                rule_id="sfx_lines",
                message="未检测到明确的【音效/氛围音】单独标注行。",
                suggestion="关键节拍前置音效行，便于导演/音效师设计节奏与情绪。",
            )
        )
    return (
        ScriptLintRuleResult(
            rule_id="sfx_lines",
            title="【音效/氛围音】单独行",
            weight=0.25,
            score=1.0 if has_sfx else 0.5,
            passed=has_sfx,
            details={"detected": has_sfx},
        ),
        issues,
    )


def check_hook_3s(non_empty: list[tuple[int, str]]) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    first_three = [ln for _no, ln in non_empty[:3]]
    has_hook = any(any(m in ln for m in HOOK_MARKERS) for ln in first_three)
    issues: list[ScriptLintIssue] = []
    if not has_hook:
        issues.append(
            ScriptLintIssue(
                severity="error",
                rule_id="hook_3s",
                message="前三行未检测到强钩子（冲突/惊呼/命令/巨响）。",
                suggestion="用“质问/耳光/摔杯/警报”等强事件开场，禁止寒暄。",
            )
        )
    return (
        ScriptLintRuleResult(
            rule_id="hook_3s",
            title="黄金3秒钩子（前三行）",
            weight=1.5,
            score=1.0 if has_hook else 0.0,
            passed=has_hook,
            details={"detected": has_hook},
        ),
        issues,
    )


def check_cliffhanger(non_empty: list[tuple[int, str]]) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    last_line = non_empty[-1][1] if non_empty else ""
    has_cliff = bool(last_line) and (
        ("?" in last_line)
        or ("？" in last_line)
        or last_line.rstrip().endswith(("…", "...", "——", "？！", "!?"))
    )
    issues: list[ScriptLintIssue] = []
    if not has_cliff:
        issues.append(
            ScriptLintIssue(
                severity="error",
                rule_id="cliffhanger",
                message="结尾未检测到强悬念/新问题。",
                suggestion="最后一句/最后一个动作提出新问题或爆点揭示，避免收束。",
            )
        )
    return (
        ScriptLintRuleResult(
            rule_id="cliffhanger",
            title="悬念结尾（最后一行）",
            weight=1.5,
            score=1.0 if has_cliff else 0.0,
            passed=has_cliff,
            details={"detected": has_cliff, "last_line": last_line[:80]},
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


def check_visual_language(
    non_empty: list[tuple[int, str]],
) -> tuple[ScriptLintRuleResult, list[ScriptLintIssue]]:
    hits = 0
    issues: list[ScriptLintIssue] = []

    for ln_no, ln in non_empty:
        is_dialogue_line, _speaker, _content = is_dialogue(ln)
        if is_dialogue_line:
            continue
        for rule in UNFILMABLE_PHRASES:
            if rule.phrase in ln:
                hits += 1
                issues.append(
                    ScriptLintIssue(
                        severity=rule.severity,  # type: ignore[arg-type]
                        rule_id="visual_language",
                        message=f"疑似不可拍表述：包含「{rule.phrase}」",
                        line=ln_no,
                        excerpt=ln[:160],
                        suggestion=rule.suggestion,
                    )
                )

    score_visual = (
        1.0 if hits == 0 else max(0.0, 1.0 - min(1.0, hits / 5.0))
    )
    return (
        ScriptLintRuleResult(
            rule_id="visual_language",
            title="拒绝不可拍心理/氛围词（视觉指令化）",
            weight=3.0,
            score=score_visual,
            passed=hits == 0,
            details={"hits": hits},
        ),
        issues,
    )

