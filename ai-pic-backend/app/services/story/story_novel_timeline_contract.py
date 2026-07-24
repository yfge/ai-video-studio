"""Deterministic timeline-to-event bindings for long-form chapter plans."""

from __future__ import annotations


def immutable_timeline_ids(canon: dict) -> set[str]:
    return {
        str(item["id"])
        for item in canon.get("timeline") or []
        if item.get("immutable") and item.get("id")
    }


def immutable_timeline_contract(canon: dict) -> dict[str, dict]:
    return {
        str(item["id"]): item
        for item in canon.get("timeline") or []
        if item.get("immutable") and item.get("id")
    }


def compile_timeline_bindings(canon: dict, chapters: list[dict]) -> list[dict]:
    """Derive timeline refs from frozen source events, never model placeholders."""
    timeline = immutable_timeline_contract(canon)
    by_position: dict[int, list[tuple[str, dict]]] = {}
    for timeline_id, item in timeline.items():
        by_position.setdefault(
            int(item.get("source_chapter_position") or 0), []
        ).append((timeline_id, item))
    compiled = []
    for chapter in chapters:
        row = dict(chapter)
        refs = list(row.get("canon_refs") or [])
        refs = [ref for ref in refs if ref not in timeline]
        bindings: dict[str, str] = {}
        key_events = list(row.get("key_events") or [])
        required = list(row.get("required_event_ids") or [])
        for timeline_id, item in by_position.get(int(row.get("position") or 0), []):
            matches = [
                index
                for index, event in enumerate(key_events)
                if event == item.get("source_key_event")
            ]
            if len(matches) != 1 or matches[0] >= len(required):
                continue
            refs.append(timeline_id)
            bindings[timeline_id] = required[matches[0]]
        row["canon_refs"] = list(dict.fromkeys(refs))
        row["timeline_event_bindings"] = bindings
        compiled.append(row)
    return compiled


def visible_timeline_refs(canon: dict, refs: set[str], position: int) -> set[str]:
    """Hide timeline entries whose source chapter has not happened yet."""
    sources = {
        str(item["id"]): item.get("source_chapter_position")
        for item in canon.get("timeline") or []
        if item.get("id")
    }
    gate_v2 = int(canon.get("gate_version") or 0) >= 2
    return {
        ref
        for ref in refs
        if ref not in sources
        or (sources[ref] is not None and int(sources[ref]) <= int(position))
        or (sources[ref] is None and not gate_v2)
    }


def prompt_visible_chapter_contract(canon: dict, chapter: dict) -> dict:
    """Defense in depth: never serialize future timeline details into prose prompts."""
    result = dict(chapter)
    refs = visible_timeline_refs(
        canon, set(result.get("canon_refs") or []), int(result.get("position") or 0)
    )
    result["canon_refs"] = [
        ref for ref in result.get("canon_refs") or [] if ref in refs
    ]
    result["timeline_event_bindings"] = {
        timeline_id: event_id
        for timeline_id, event_id in (
            result.get("timeline_event_bindings") or {}
        ).items()
        if timeline_id in refs
    }
    return result


def chapter_timeline_binding_issues(chapter: dict, timeline_ids: set[str]) -> list[str]:
    position = int(chapter.get("position") or 0)
    expected = set(chapter.get("canon_refs") or []).intersection(timeline_ids)
    bindings = chapter.get("timeline_event_bindings")
    if not isinstance(bindings, dict):
        return [f"第 {position} 章缺少 timeline_event_bindings object"]
    actual = set(bindings)
    issues: list[str] = []
    if any(
        not isinstance(timeline_id, str)
        or not timeline_id.strip()
        or not isinstance(event_id, str)
        or not event_id.strip()
        for timeline_id, event_id in bindings.items()
    ):
        issues.append(f"第 {position} 章 timeline_event_bindings 包含空 ID")
    missing, extra = expected - actual, actual - expected
    if missing:
        issues.append(f"第 {position} 章时间线缺少事件绑定: {sorted(missing)}")
    if extra:
        issues.append(f"第 {position} 章时间线包含无效事件绑定: {sorted(extra)}")
    required = set(chapter.get("required_event_ids") or [])
    invalid = {
        timeline_id: event_id
        for timeline_id, event_id in bindings.items()
        if timeline_id in expected and event_id not in required
    }
    if invalid:
        issues.append(f"第 {position} 章时间线绑定非本章事件: {invalid}")
    return issues


def generation_timeline_binding_issues(canon: dict, chapters: list[dict]) -> list[str]:
    timeline = immutable_timeline_contract(canon)
    issues = [
        issue
        for chapter in chapters
        for issue in (
            *chapter_timeline_binding_issues(chapter, set(timeline)),
            *_timeline_source_issues(chapter, timeline),
        )
    ]
    if int(canon.get("gate_version") or 0) >= 2:
        issues.extend(_timeline_coverage_issues(chapters, timeline))
    return issues


def _timeline_coverage_issues(
    chapters: list[dict], timeline: dict[str, dict]
) -> list[str]:
    references = {
        timeline_id: [
            int(chapter.get("position") or 0)
            for chapter in chapters
            for ref in chapter.get("canon_refs") or []
            if ref == timeline_id
        ]
        for timeline_id in timeline
    }
    return [
        (
            f"immutable timeline 必须且只能在来源章节引用: {timeline_id} "
            f"expected={[int(source.get('source_chapter_position') or 0)]} "
            f"actual={references[timeline_id]}"
        )
        for timeline_id, source in timeline.items()
        if references[timeline_id] != [int(source.get("source_chapter_position") or 0)]
    ]


def _timeline_source_issues(chapter: dict, timeline: dict[str, dict]) -> list[str]:
    position = int(chapter.get("position") or 0)
    key_events = list(chapter.get("key_events") or [])
    required = list(chapter.get("required_event_ids") or [])
    bindings = chapter.get("timeline_event_bindings") or {}
    issues = []
    for timeline_id in set(chapter.get("canon_refs") or []).intersection(timeline):
        source = timeline[timeline_id]
        if int(source.get("source_chapter_position") or 0) != position:
            issues.append(f"第 {position} 章时间线引用来源章节不匹配: {timeline_id}")
            continue
        matches = [
            index
            for index, key_event in enumerate(key_events)
            if key_event == source.get("source_key_event")
        ]
        if len(matches) != 1:
            issues.append(f"第 {position} 章时间线来源事件不唯一: {timeline_id}")
            continue
        index = matches[0]
        if index >= len(required) or bindings.get(timeline_id) != required[index]:
            issues.append(f"第 {position} 章时间线绑定未对应来源事件: {timeline_id}")
    return issues


def bound_event_id(chapter: dict, timeline_id: str) -> str | None:
    bindings = chapter.get("timeline_event_bindings")
    if not isinstance(bindings, dict):
        return None
    value = bindings.get(timeline_id)
    return str(value) if isinstance(value, str) and value else None
