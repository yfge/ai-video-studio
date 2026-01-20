from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from app.services.story.story_novel_export_utils import (
    ZH_CLIFFHANGER_MARKER,
    ZH_SUMMARY_MARKER,
)


def init_continuity_ledger(*, story_payload: Dict[str, Any]) -> Dict[str, Any]:
    characters: Dict[str, Any] = {}
    for item in story_payload.get("characters") or []:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        if not name:
            vip = item.get("virtual_ip") if isinstance(item.get("virtual_ip"), dict) else {}
            name = str(vip.get("name") or "").strip()
        if not name or name in characters:
            continue
        characters[name] = {
            "status": "",
            "goal": "",
            "relationships": {},
        }

    return {
        "version": 1,
        "facts": [],
        "timeline": [],
        "characters": characters,
        "info_acquisition_events": [],
        "open_threads": [],
        "resolved_threads": [],
    }


def extract_chapter_markers(text: str) -> Tuple[str, str, str]:
    value = (text or "").strip()
    if not value:
        return "", "", ""

    if ZH_SUMMARY_MARKER not in value:
        return value, "", ""

    body_part, tail = value.rsplit(ZH_SUMMARY_MARKER, 1)
    body = body_part.strip()
    tail = tail.strip()
    summary = ""
    cliffhanger = ""

    if ZH_CLIFFHANGER_MARKER in tail:
        summary_part, rest = tail.split(ZH_CLIFFHANGER_MARKER, 1)
        summary = summary_part.strip()
        rest = rest.strip()
        if body:
            cliffhanger = rest
        else:
            cliff_line, _, remainder = rest.partition("\n\n")
            cliffhanger = cliff_line.strip()
            body = remainder.strip()
    else:
        summary = tail
        if not body:
            summary_line, _, remainder = summary.partition("\n\n")
            summary = summary_line.strip()
            body = remainder.strip()

    # Strip accidental leading marker blocks (model sometimes puts them at chapter start).
    stripped = body.lstrip()
    if stripped.startswith(ZH_SUMMARY_MARKER):
        _, _, after_summary = stripped.partition(ZH_SUMMARY_MARKER)
        if ZH_CLIFFHANGER_MARKER in after_summary:
            _, _, after_cliff = after_summary.partition(ZH_CLIFFHANGER_MARKER)
            _, _, remainder = after_cliff.lstrip().partition("\n\n")
            body = remainder.strip()
        else:
            _, _, remainder = after_summary.lstrip().partition("\n\n")
            body = remainder.strip()

    return body, summary, cliffhanger


def tail_text(text: str, limit: int) -> str:
    value = (text or "").strip()
    if not value:
        return ""
    if len(value) <= limit:
        return value
    return value[-limit:]


def format_summary_lines(lines: List[str]) -> str:
    cleaned: list[str] = []
    for raw in lines:
        line = str(raw or "").strip()
        if not line:
            continue
        line = re.sub(r"^[-*•\d.\s]+", "", line).strip()
        if line:
            cleaned.append(f"- {line}")
    return "\n".join(cleaned)


def build_plan_context(plan: Dict[str, Any], *, chapters: List[Dict[str, Any]], index: int) -> Dict[str, Any]:
    overview: list[dict[str, Any]] = []
    for ch in chapters:
        if not isinstance(ch, dict):
            continue
        overview.append(
            {
                "chapter_number": ch.get("chapter_number"),
                "title": ch.get("title"),
                "target_words": ch.get("target_words"),
                "chapter_goal": ch.get("chapter_goal"),
                "cliffhanger_hint": ch.get("cliffhanger_hint") or ch.get("cliffhanger"),
            }
        )

    current = chapters[index] if 0 <= index < len(chapters) else {}
    next_ch = chapters[index + 1] if 0 <= index + 1 < len(chapters) else None

    return {
        "question_title": plan.get("question_title"),
        "question_detail": plan.get("question_detail"),
        "narrator_profile": plan.get("narrator_profile"),
        "running_summary_seed": plan.get("running_summary_seed"),
        "chapter_total": len(chapters),
        "chapters_overview": overview,
        "current_chapter": {
            "chapter_number": current.get("chapter_number"),
            "title": current.get("title"),
            "target_words": current.get("target_words"),
            "chapter_goal": current.get("chapter_goal"),
            "key_beats": current.get("key_beats") or current.get("beats"),
            "cliffhanger_hint": current.get("cliffhanger_hint") or current.get("cliffhanger"),
        },
        "next_chapter": (
            {
                "chapter_number": next_ch.get("chapter_number"),
                "title": next_ch.get("title"),
                "target_words": next_ch.get("target_words"),
                "chapter_goal": next_ch.get("chapter_goal"),
                "key_beats": next_ch.get("key_beats") or next_ch.get("beats"),
                "cliffhanger_hint": next_ch.get("cliffhanger_hint") or next_ch.get("cliffhanger"),
            }
            if isinstance(next_ch, dict)
            else None
        ),
    }


def _truncate_list(values: Any, max_items: int) -> list:
    if not isinstance(values, list):
        return []
    return values[:max_items]


def compact_ledger_for_prompt(ledger: Dict[str, Any]) -> Dict[str, Any]:
    base: dict[str, Any] = ledger if isinstance(ledger, dict) else {}
    characters = base.get("characters") if isinstance(base.get("characters"), dict) else {}

    facts = _truncate_list(base.get("facts"), 25)
    open_threads = _truncate_list(base.get("open_threads"), 25)
    resolved_threads = _truncate_list(base.get("resolved_threads"), 25)
    timeline = _truncate_list(base.get("timeline"), 30)
    info_events = _truncate_list(base.get("info_acquisition_events"), 60)

    return {
        "version": int(base.get("version") or 1),
        "facts": facts,
        "timeline": timeline,
        "characters": characters,
        "info_acquisition_events": info_events,
        "open_threads": open_threads,
        "resolved_threads": resolved_threads,
    }


def normalize_ledger_update_payload(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], str, str]:
    ledger_raw = payload.get("ledger")
    ledger = (
        compact_ledger_for_prompt(ledger_raw)
        if isinstance(ledger_raw, dict) and ledger_raw
        else {}
    )
    summary_lines: list[str] = []
    summary_raw = payload.get("chapter_summary")
    if isinstance(summary_raw, list):
        summary_lines = [str(x) for x in summary_raw]
    elif isinstance(summary_raw, str) and summary_raw.strip():
        summary_lines = [summary_raw.strip()]
    cliffhanger = (
        str(payload.get("chapter_cliffhanger")).strip()
        if isinstance(payload.get("chapter_cliffhanger"), str)
        else ""
    )

    return ledger, format_summary_lines(summary_lines), cliffhanger


def ensure_markers(body: str, *, summary_text: str, cliffhanger_text: str) -> str:
    text = (body or "").rstrip() + "\n"
    if summary_text:
        text += f"\n{ZH_SUMMARY_MARKER}\n{summary_text.strip()}\n"
    if cliffhanger_text:
        text += f"\n{ZH_CLIFFHANGER_MARKER}\n{cliffhanger_text.strip()}\n"
    return text.strip() + "\n"
