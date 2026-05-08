from __future__ import annotations

from app.schemas.script_quality import ScriptLintIssue, ScriptLintRuleResult
from app.services.script_quality.constants import UNFILMABLE_PHRASES
from app.services.script_quality.utils import is_dialogue


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

    score_visual = 1.0 if hits == 0 else max(0.0, 1.0 - min(1.0, hits / 5.0))
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
