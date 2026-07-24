"""Bounded formatting for chapter-plan repair diagnostics."""

_MAX_ISSUES, _MAX_ITEM_CHARS = 48, 420


def format_plan_diagnostics(errors: list[str]) -> str:
    unique = list(dict.fromkeys(errors))
    prefix = f"章节计划确定性诊断失败（共 {len(unique)} 项）: "
    visible = [
        (
            item
            if len(item) <= _MAX_ITEM_CHARS
            else item[: _MAX_ITEM_CHARS - 9] + "…[单项已截断]"
        )
        for item in unique[:_MAX_ISSUES]
    ]
    omitted = len(unique) - len(visible)
    suffix = f"；[诊断已截断：另有 {omitted} 项未展示]" if omitted else ""
    return prefix + "；".join(visible) + suffix
