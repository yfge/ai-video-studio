"""Extract typed state changes from the actual generated chapter body."""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.schemas.story_novel_longform import StoryNovelStateDelta
from app.services.story.story_novel_evidence_alignment import (
    normalize_extracted_evidence,
)
from app.services.story.story_novel_evidence_rules import (
    evidence_violations,
    timeline_evidence_violations,
)
from app.services.story.story_novel_future_claims import (
    future_audit_id_violations,
    is_future_audit_id_issue,
)
from app.services.story.story_novel_state_evidence_diagnostics import (
    evidence_repair_diagnostics as _evidence_repair_diagnostics,
)
from app.services.story.story_novel_state_evidence_diagnostics import (
    only_evidence_issues as _only_evidence_issues,
)
from app.services.story.story_novel_state_evidence_repair import (
    quote_maps_match_ids,
    repair_state_evidence,
)
from app.services.story.story_novel_state_extraction_prompt import (
    build_state_extraction_prompt,
)
from app.utils.json_utils import extract_json_block

STATE_EXTRACTION_MAX_TOKENS = 16000


class StateExtractionError(ValueError):
    def __init__(self, message: str, *, repair_count: int, evidence_only=False):
        super().__init__(message)
        self.repair_count = repair_count
        self.evidence_only = evidence_only


async def extract_chapter_state(
    revision,
    *,
    chapter_plan: dict,
    state_before: dict,
    content_text: str,
    future_event_catalog: list[dict],
    current_timeline: list[dict] | None = None,
    generate_text,
) -> tuple[dict, int]:
    prompt = build_state_extraction_prompt(
        chapter_plan,
        state_before,
        content_text,
        future_event_catalog,
        current_timeline or [],
    )
    text = await generate_text(
        revision,
        prompt,
        max_tokens=STATE_EXTRACTION_MAX_TOKENS,
        temperature=0.0,
    )
    normalized, error, issues = _validation_result(
        text,
        chapter_plan=chapter_plan,
        content_text=content_text,
        current_timeline=current_timeline or [],
        future_event_catalog=future_event_catalog,
    )
    if normalized and not issues:
        return normalized, 0
    diagnostics = _evidence_repair_diagnostics(content_text, normalized or {}, issues)
    if (
        normalized
        and _only_evidence_issues(issues)
        and not normalized.get("premature_future_event_ids")
        and quote_maps_match_ids(
            normalized,
            chapter_plan,
            current_timeline or [],
        )
    ):
        try:
            text = await repair_state_evidence(
                revision,
                chapter_plan=chapter_plan,
                content_text=content_text,
                current_timeline=current_timeline or [],
                delta=normalized,
                diagnostics=diagnostics,
                error=error,
                generate_text=generate_text,
            )
        except (TypeError, ValueError) as exc:
            raise StateExtractionError(
                f"章节状态证据返修失败: {exc}",
                repair_count=1,
                evidence_only=True,
            ) from exc
        normalized, error, issues = _validation_result(
            text,
            chapter_plan=chapter_plan,
            content_text=content_text,
            current_timeline=current_timeline or [],
            future_event_catalog=future_event_catalog,
        )
        if not normalized or issues:
            raise StateExtractionError(
                f"章节状态提取失败: {error}",
                repair_count=1,
                evidence_only=True,
            )
        return normalized, 1
    repair = (
        prompt + "\n\n上一次状态提取无效，只修复 typed JSON 与逐字 evidence，"
        "不得改写正文或虚构正文中没有的事实。"
        "校验错误中的每个“事件缺少可核对的正文证据”或时间线 evidence 错误"
        "都必须替换对应 evidence，禁止原样返回无效值。"
        "先按“……”拆分错误 evidence，逐段核对 content_text，删除每一个"
        "不能从正文逐字找到的片段；若剩余某个逐字片段已能独立证明该事件，"
        "只保留该片段，不得补写概括、动作或说话人。"
        "使用“……”连接时，各逐字片段在正文中的起始 offset 必须严格递增；"
        "若一个连续短句已经同时包含固定日期和对应事件，删除多余的日期前缀，"
        "直接使用该完整短句。timeline_evidence[timeline-id] 必须复用 "
        "evidence[chapter_plan.timeline_event_bindings[timeline-id]] 的已修正正文"
        "逐字片段，并在它前面连接正文中更早出现的固定日期逐字片段；"
        "不得复制 chapter_plan 的 label 或 key_events。"
        "若固定日期位于已选事件片段之后，改选该日期之后的同一事件正文复述，"
        "并同步扩展 evidence 与 timeline_evidence；禁止把后出现的日期移到前面。"
        "诊断中的 failure_kind=quote_rewrite 表示正文已有部分逐字事件证据，"
        "只修 quote；body_event_unverified 表示没有片段逐字命中，必须重扫正文，"
        "若仍找不到该事件就删除 occurred event ID 与 evidence，禁止伪造，"
        "交给后续 required-event 门禁判断正文是否缺事件。"
        + "\n证据逐片诊断："
        + json.dumps(diagnostics, ensure_ascii=False, separators=(",", ":"))
        + f"\n校验错误：{error}\n上一次输出：{text[:6000]}"
    )
    text = await generate_text(
        revision,
        repair,
        max_tokens=STATE_EXTRACTION_MAX_TOKENS,
        temperature=0.0,
    )
    normalized, error, issues = _validation_result(
        text,
        chapter_plan=chapter_plan,
        content_text=content_text,
        current_timeline=current_timeline or [],
        future_event_catalog=future_event_catalog,
    )
    if not normalized or issues:
        raise StateExtractionError(
            f"章节状态提取失败: {error}",
            repair_count=1,
            evidence_only=_only_audit_output_issues(issues),
        )
    return normalized, 1


def _parse(text: str) -> tuple[dict | None, str | None]:
    try:
        payload = extract_json_block(text)
        if not payload:
            raise ValueError("missing JSON object")
        normalized = StoryNovelStateDelta.model_validate(payload).model_dump()
        normalized["location_transitions"] = [
            item
            for item in normalized["location_transitions"]
            if item["from_location_id"] != item["to_location_id"]
        ]
        return normalized, None
    except (ValidationError, ValueError, TypeError) as exc:
        return None, str(exc)


def _validated_parse(
    text: str,
    *,
    chapter_plan: dict,
    content_text: str,
    current_timeline: list[dict],
) -> tuple[dict | None, str | None]:
    normalized, error, issues = _validation_result(
        text,
        chapter_plan=chapter_plan,
        content_text=content_text,
        current_timeline=current_timeline,
    )
    return (None if issues else normalized), error


def _validation_result(
    text: str,
    *,
    chapter_plan: dict,
    content_text: str,
    current_timeline: list[dict],
    future_event_catalog: list[dict] | None = None,
) -> tuple[dict | None, str | None, list[dict]]:
    normalized, error = _parse(text)
    if not normalized:
        return None, error, []
    canon = {"timeline": current_timeline}
    normalize_extracted_evidence(content_text, canon, chapter_plan, normalized)
    issues = [
        *(
            future_audit_id_violations(future_event_catalog, normalized)
            if future_event_catalog is not None
            else []
        ),
        *_typed_delta_contract_violations(normalized),
        *evidence_violations(content_text, normalized),
        *timeline_evidence_violations(
            content_text,
            canon,
            chapter_plan,
            normalized,
        ),
    ]
    if issues:
        return normalized, "；".join(item["message"] for item in issues), issues
    return normalized, None, []


def _typed_delta_contract_violations(delta: dict) -> list[dict]:
    return [
        {
            "code": "canon_violation",
            "message": (
                f"{item.get('field')} 不能写入 state_transitions: "
                f"{item.get('subject_id')}"
            ),
        }
        for item in delta.get("state_transitions") or []
        if item.get("field") in {"knowledge", "location", "possessions"}
    ]


def _only_audit_output_issues(issues: list[dict]) -> bool:
    return bool(issues) and all(
        _only_evidence_issues([issue]) or is_future_audit_id_issue(issue)
        for issue in issues
    )
