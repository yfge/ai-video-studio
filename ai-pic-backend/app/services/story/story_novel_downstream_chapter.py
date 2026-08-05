from app.services.narrative_memory.source_hash import novel_chapter_source_hash


def chapter_is_ready(chapter, entry: dict, *, require_v5: bool = False) -> bool:
    common = bool(
        chapter.review_status in {"ready", "target_changed"}
        and entry.get("status") == "ready"
        and entry.get("extraction_status") == "ready"
        and entry.get("body_hash") == chapter.content_hash
        and entry.get("source_hash") == novel_chapter_source_hash(chapter)
    )
    if not require_v5:
        return common
    return bool(
        common
        and entry.get("consistency_report", {}).get("status") == "passed"
        and entry.get("readability_report", {}).get("status") == "passed"
        and entry.get("length_report", {}).get("status") == "passed"
        and entry.get("state_patch")
        and entry.get("snapshot_before_hash")
        and entry.get("snapshot_after_hash")
    )
