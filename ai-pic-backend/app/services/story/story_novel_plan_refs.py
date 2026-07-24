"""Canon reference diagnostics shared by plan compilation and repair."""

from __future__ import annotations


def known_canon_ids(canon: dict) -> set[str]:
    return {
        str(item["character_id"] if section == "character_arcs" else item["id"])
        for section in (
            "timeline",
            "entities",
            "world_rules",
            "milestones",
            "character_arcs",
        )
        for item in canon.get(section) or []
    }


def generation_canon_ref_issues(canon: dict, chapters: list[dict]) -> list[str]:
    known = known_canon_ids(canon)
    milestones = {item["id"] for item in canon.get("milestones") or []}
    timeline_sources = {
        item["id"]: item.get("source_chapter_position")
        for item in canon.get("timeline") or []
        if item.get("id")
    }
    issues = []
    invalid_rows: list[tuple[int, list[str]]] = []
    for chapter in chapters:
        position = int(chapter.get("position") or 0)
        refs = set(chapter.get("canon_refs") or [])
        invalid = refs - known
        if invalid:
            invalid_rows.append((position, sorted(invalid)))
        future = refs.intersection(milestones) - set(
            chapter.get("milestones_consumed") or []
        )
        if future:
            issues.append(f"第 {position} 章提前引用里程碑: {sorted(future)}")
        future_timeline = {
            ref
            for ref in refs.intersection(timeline_sources)
            if timeline_sources[ref] is not None
            and position < int(timeline_sources[ref])
        }
        if future_timeline:
            issues.append(
                f"第 {position} 章提前引用未来 timeline: {sorted(future_timeline)}"
            )
    if len(invalid_rows) == 1:
        position, values = invalid_rows[0]
        issues.insert(0, f"第 {position} 章引用未知 Canon: {values}")
    elif invalid_rows:
        issues.insert(0, f"{len(invalid_rows)} 章引用未知 Canon: {invalid_rows}")
    return issues
