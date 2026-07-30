"""Service-compiled typed effect manifest for one chapter contract."""

from __future__ import annotations

from .story_novel_chapter_effect_coverage import effect_catalog
from .story_novel_context_utils import value_hash

VERSION = 1
MODE = "service_compiled"


def compile_effect_manifest(contract: dict, canon: dict) -> dict:
    items = [
        {
            "effect_ref": effect_ref,
            "subject_id": pair[0],
            "field": pair[1],
            "source_event_id": source_event_id,
            "expected": expected,
        }
        for effect_ref, (pair, source_event_id, expected) in effect_catalog(
            contract, canon
        ).items()
    ]
    payload = {"version": VERSION, "mode": MODE, "items": items}
    payload["manifest_hash"] = value_hash(payload)
    return payload


def effect_manifest_checkpoint_valid(chapter: dict) -> bool:
    manifest = chapter.get("effect_manifest") or {}
    candidate = {
        "version": manifest.get("version"),
        "mode": manifest.get("mode"),
        "items": manifest.get("items"),
    }
    if (
        candidate["version"] != VERSION
        or candidate["mode"] != MODE
        or not isinstance(candidate["items"], list)
        or manifest.get("manifest_hash") != value_hash(candidate)
    ):
        return False
    items = candidate["items"]
    refs = [item.get("effect_ref") for item in items if isinstance(item, dict)]
    if len(refs) != len(items) or len(refs) != len(set(refs)):
        return False
    expected = {
        *(
            f"state:{index}"
            for index, _ in enumerate(chapter.get("state_transitions") or [], 1)
        ),
        *(
            f"location:{index}"
            for index, _ in enumerate(chapter.get("location_transitions") or [], 1)
        ),
        *(
            f"knowledge:{index}"
            for index, _ in enumerate(chapter.get("knowledge_grants") or [], 1)
        ),
    }
    if {ref for ref in refs if not str(ref).startswith("milestone:")} != expected:
        return False
    consumed = set(chapter.get("milestones_consumed") or [])
    return all(
        len(parts := str(ref).split(":")) == 4
        and parts[1] in consumed
        and all(str(item.get(key) or "").strip() for key in ("subject_id", "field"))
        for ref, item in zip(refs, items, strict=True)
        if str(ref).startswith("milestone:")
    )
