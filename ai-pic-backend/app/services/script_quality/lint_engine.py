from __future__ import annotations

from app.schemas.script_quality import (
    ScriptLintMetrics,
    ScriptLintOptions,
    ScriptLintResult,
)
from app.services.script_quality.checks import (
    check_cliffhanger,
    check_dialogue_length,
    check_emotion_goal,
    check_hook_3s,
    check_scene_headers,
    check_sfx_lines,
    check_tempo_tags,
    check_visual_language,
)
from app.services.script_quality.constants import SFX_TAG_KEYWORDS, UNIMPLEMENTED_CHECKS
from app.services.script_quality.utils import (
    collect_tags,
    estimate_visible_chars,
    is_dialogue,
)


def lint_script_content(
    script_content: str, options: ScriptLintOptions | None = None
) -> ScriptLintResult:
    """Deterministic script lint focused on industrial constraints (no LLM)."""

    opts = options or ScriptLintOptions()
    raw_lines = script_content.splitlines()
    lines = [(idx + 1, ln.rstrip("\n")) for idx, ln in enumerate(raw_lines)]
    non_empty = [(ln_no, ln.strip()) for ln_no, ln in lines if ln.strip()]

    dialogue_lines = []
    stage_lines = []
    all_tags: list[str] = []

    for ln_no, ln in non_empty:
        tags = collect_tags(ln)
        all_tags.extend(tags)
        is_dialogue_line, _speaker, content = is_dialogue(ln)
        if is_dialogue_line:
            dialogue_lines.append((ln_no, ln, content or ""))
            continue
        if any(key in ln for key in SFX_TAG_KEYWORDS) or ln.startswith(
            ("（", "(", "[")
        ):
            stage_lines.append((ln_no, ln))

    rule_results = []
    issues = []

    for rule, found in (
        check_scene_headers(non_empty),
        check_tempo_tags(all_tags),
        check_emotion_goal(all_tags),
        check_sfx_lines(stage_lines),
        check_hook_3s(non_empty),
        check_cliffhanger(non_empty),
        check_dialogue_length(dialogue_lines, opts),
        check_visual_language(non_empty),
    ):
        rule_results.append(rule)
        issues.extend(found)

    # ---------- Optional: word count target ----------
    estimated_words = estimate_visible_chars(script_content)
    word_range_ok = True
    if opts.target_word_min is not None and estimated_words < opts.target_word_min:
        word_range_ok = False
    if opts.target_word_max is not None and estimated_words > opts.target_word_max:
        word_range_ok = False

    # ---------- Score aggregation ----------
    total_weight = sum(r.weight for r in rule_results) or 1.0
    overall = 10.0 * sum(r.score * r.weight for r in rule_results) / total_weight
    passed = overall >= opts.pass_threshold

    if opts.target_word_min is not None or opts.target_word_max is not None:
        issues.append(
            ScriptLintIssue(
                severity="info" if word_range_ok else "warn",
                rule_id="word_count",
                message=(
                    f"估算字数={estimated_words}（目标范围："
                    f"{opts.target_word_min or '-'}~{opts.target_word_max or '-'}）"
                ),
                suggestion="字数仅为估算；若时长/镜头密度不匹配，可调节 Beat 密度与对白长度。",
            )
        )

    metrics = ScriptLintMetrics(
        non_empty_lines=len(non_empty),
        dialogue_lines=len(dialogue_lines),
        stage_lines=len(stage_lines),
        estimated_words=estimated_words,
        estimated_dialogue_chars=sum(
            estimate_visible_chars(c) for _no, _ln, c in dialogue_lines
        ),
    )

    return ScriptLintResult(
        options=opts,
        overall_score=round(overall, 2),
        passed=passed,
        rules=rule_results,
        issues=issues,
        metrics=metrics,
        unimplemented_checks=UNIMPLEMENTED_CHECKS,
    )
