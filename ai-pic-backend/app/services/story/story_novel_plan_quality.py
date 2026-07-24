"""Non-semantic capacity gates for executable long-form plans."""

MAX_PAYOFFS_PER_CHAPTER = 3


def plan_quality_diagnostics(chapters: list[dict]) -> list[str]:
    errors = []
    for chapter in chapters:
        position = int(chapter["position"])
        payoffs = list(chapter.get("payoffs_due") or [])
        if len(payoffs) > MAX_PAYOFFS_PER_CHAPTER:
            errors.append(
                f"第 {position} 章集中回收 {len(payoffs)} 条伏笔，"
                f"超过单章上限 {MAX_PAYOFFS_PER_CHAPTER}"
            )
    return errors


def validate_plan_quality(chapters: list[dict]) -> None:
    errors = plan_quality_diagnostics(chapters)
    if errors:
        raise ValueError("；".join(errors))
