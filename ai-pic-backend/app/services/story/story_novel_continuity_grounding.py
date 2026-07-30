"""Ground model continuity findings in persisted chapter and Canon evidence."""

from __future__ import annotations

import json

from .story_novel_sentence_spans import sentence_spans

_MISSING = object()


def chapter_evidence_catalog(chapters: list) -> dict[str, set[str]]:
    return {
        str(row.business_id): {
            item["sentence_id"] for item in sentence_spans(row.content_text or "")
        }
        for row in chapters
    }


def payload_evidence_catalog(payload: dict) -> dict[str, set[str]]:
    catalog: dict[str, set[str]] = {}
    for chapter in payload.get("chapters") or []:
        chapter_id = str(chapter.get("business_id") or "")
        if not chapter_id:
            continue
        catalog.setdefault(chapter_id, set()).update(
            str(item["sentence_id"])
            for item in chapter.get("sentence_index") or []
            if item.get("sentence_id")
        )
        _collect_sentence_ids(chapter.get("proof_spans"), catalog[chapter_id])
    for report in payload.get("window_findings") or []:
        for issue in report.get("issues") or []:
            for ref in issue.get("evidence_refs") or []:
                chapter_id = str(ref.get("chapter_business_id") or "")
                catalog.setdefault(chapter_id, set()).update(
                    str(value) for value in ref.get("sentence_ids") or []
                )
    return catalog


def contract_reference_catalog(revision, chapters: list) -> set[str]:
    plan = revision.generation_plan or {}
    canon = plan.get("canon") or {}
    refs = set()
    for section, label in (
        ("entities", "entity"),
        ("timeline", "timeline"),
        ("world_rules", "world_rule"),
        ("milestones", "milestone"),
    ):
        for item in canon.get(section) or []:
            item_id = item.get("id")
            if not item_id:
                continue
            refs.add(f"canon:{label}:{item_id}")
            refs.update(f"canon:{label}:{item_id}:{key}" for key in item if key != "id")
            refs.update(
                f"canon:{label}:{item_id}:attributes.{key}"
                for key in (item.get("attributes") or {})
            )
    for subject_id, state in (canon.get("initial_state") or {}).items():
        refs.add(f"canon:initial_state:{subject_id}")
        refs.update(f"canon:initial_state:{subject_id}:{field}" for field in state)
    for row in chapters:
        base = f"chapter:{row.business_id}"
        refs.update(
            {
                f"{base}:contract",
                f"{base}:expected_delta",
                f"{base}:state_before",
                f"{base}:state_after",
            }
        )
    return refs


def ground_issue(
    item: dict,
    evidence_catalog: dict[str, set[str]],
    contract_catalog: set[str],
) -> dict:
    result = dict(item)
    evidence = _valid_evidence_refs(result.get("evidence_refs"), evidence_catalog)
    contracts = [
        str(value)
        for value in result.get("contract_refs") or []
        if str(value) in contract_catalog
    ]
    chapter_ids = [
        str(value)
        for value in result.get("chapter_business_ids") or []
        if str(value) in evidence_catalog
    ]
    if not chapter_ids:
        chapter_ids = [ref["chapter_business_id"] for ref in evidence]
    result["chapter_business_ids"] = list(dict.fromkeys(chapter_ids))
    result["evidence_refs"] = evidence
    result["contract_refs"] = list(dict.fromkeys(contracts))
    grounded = _blocking_grounded(result)
    if result.get("severity") == "blocking" and not grounded:
        result["severity"] = "warning"
        result["grounding_status"] = "unverified"
    else:
        result["grounding_status"] = "verified" if grounded else "not_required"
    return result


def normalize_repair_groups(
    raw,
    prefix: str,
    issues: list[dict],
    canon: dict,
) -> list[dict]:
    known = {item["id"]: item for item in issues if item["severity"] == "blocking"}
    result = []
    for index, item in enumerate(raw or [], start=1):
        if not isinstance(item, dict):
            continue
        issue_ids = [
            value if str(value).startswith(f"{prefix}-") else f"{prefix}-{value}"
            for value in item.get("issue_ids") or []
        ]
        issue_ids = [value for value in issue_ids if value in known]
        target = item.get("canon_target") or {}
        current = _canon_target_value(canon, target)
        suggested = item.get("suggested_value", _MISSING)
        if not issue_ids or current is _MISSING or suggested is _MISSING:
            continue
        if json.dumps(
            current, sort_keys=True, ensure_ascii=False, default=str
        ) == json.dumps(suggested, sort_keys=True, ensure_ascii=False, default=str):
            continue
        result.append(
            {
                **item,
                "id": f"{prefix}-repair-{item.get('id') or index}",
                "issue_ids": issue_ids,
            }
        )
    return result


def _valid_evidence_refs(raw, catalog) -> list[dict]:
    result = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        chapter_id = str(item.get("chapter_business_id") or "")
        allowed = catalog.get(chapter_id) or set()
        sentence_ids = list(
            dict.fromkeys(
                str(value)
                for value in item.get("sentence_ids") or []
                if str(value) in allowed
            )
        )
        if sentence_ids:
            result.append(
                {"chapter_business_id": chapter_id, "sentence_ids": sentence_ids}
            )
    return result


def _blocking_grounded(item: dict) -> bool:
    refs = item.get("evidence_refs") or []
    if not refs:
        return False
    expected = set(item.get("chapter_business_ids") or [])
    covered = {ref["chapter_business_id"] for ref in refs}
    if expected and not expected.issubset(covered):
        return False
    sentence_count = sum(len(ref["sentence_ids"]) for ref in refs)
    return len(covered) >= 2 or sentence_count >= 2 or bool(item.get("contract_refs"))


def _canon_target_value(canon: dict, target: dict):
    section = target.get("section")
    item_id = target.get("item_id")
    field = str(target.get("field") or "")
    if section == "initial_state":
        value = (canon.get(section) or {}).get(item_id, _MISSING)
    else:
        value = next(
            (
                item
                for item in canon.get(section) or []
                if str(item.get("id")) == str(item_id)
            ),
            _MISSING,
        )
    if value is _MISSING or not field:
        return _MISSING
    for part in field.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _collect_sentence_ids(value, result: set[str]) -> None:
    if isinstance(value, dict):
        result.update(str(item) for item in value.get("sentence_ids") or [])
        for nested in value.values():
            _collect_sentence_ids(nested, result)
    elif isinstance(value, list):
        for nested in value:
            _collect_sentence_ids(nested, result)
