"""Strict source evidence for one character acquiring one typed fact."""

from __future__ import annotations

import re

from app.services.narrative_memory.source_evidence import source_contains_evidence

_ELLIPSIS = re.compile(r"(?:…+|\.{3,})")
_ACQUIRE = (
    r"(?:得知|获悉|知道|明白|发现|确认|意识到|听见|听到|看见|目睹|读到|收到|记住|了解)"
)
_TRANSFER = r"(?:告诉|告知|通知|透露|说明|宣布|交代)"


def knowledge_grant_key(item: dict) -> tuple[str, str, str]:
    return (
        str(item.get("character_id") or ""),
        str(item.get("fact_id") or ""),
        str(item.get("source_event_id") or ""),
    )


def knowledge_evidence_key(item: dict) -> str:
    return "|".join(knowledge_grant_key(item))


def explicit_knowledge_acquisition(source_quote: str, names: list[str]) -> bool:
    if re.search(r"(?:…+|\.{3,})", source_quote):
        return False
    clauses = [
        semantic_text(item)
        for item in re.split(r"[。！？!?；;]+", source_quote)
        if semantic_text(item)
    ]
    name_pattern = "|".join(re.escape(name) for name in names if name)
    if len(clauses) != 1 or not name_pattern:
        return False
    return bool(
        re.search(rf"(?:{name_pattern}).{{0,4}}{_ACQUIRE}", clauses[0])
        or re.search(
            rf"{_TRANSFER}(?:了|给|向|对)?.{{0,4}}(?:{name_pattern})",
            clauses[0],
        )
        or re.search(
            rf"(?:向|对)(?:{name_pattern}).{{0,4}}{_TRANSFER}",
            clauses[0],
        )
    )


def knowledge_evidence_violations(
    content_text: str,
    delta: dict,
    canon: dict,
) -> list[dict]:
    grants = {
        knowledge_evidence_key(item): item
        for item in delta.get("knowledge_grants") or []
    }
    evidence = delta.get("knowledge_evidence") or {}
    entities = {
        item.get("id"): item
        for item in canon.get("entities") or []
        if item.get("kind") == "character"
    }
    violations = []
    if set(evidence) != set(grants):
        violations.append(
            {
                "code": "canon_violation",
                "message": "角色获知证据必须逐项等于 knowledge_grants",
            }
        )
    for item_key, grant in grants.items():
        quote = str(evidence.get(item_key) or "")
        if not quote or not source_contains_evidence(content_text, quote):
            violations.append(_issue("角色获知缺少可核对的正文证据", item_key))
            continue
        event_quote = str(
            (delta.get("evidence") or {}).get(grant.get("source_event_id")) or ""
        )
        semantic_quote = semantic_text(quote)
        event_fragments = [
            semantic_text(fragment)
            for fragment in _ELLIPSIS.split(event_quote)
            if semantic_text(fragment)
        ]
        if not semantic_quote or not any(
            semantic_quote in fragment for fragment in event_fragments
        ):
            violations.append(_issue("角色获知证据未绑定来源事件", item_key))
        entity = entities.get(grant.get("character_id")) or {}
        names = [
            semantic_text(value)
            for value in [entity.get("name"), *(entity.get("aliases") or [])]
            if semantic_text(str(value or ""))
        ]
        if not explicit_knowledge_acquisition(quote, names):
            violations.append(_issue("角色获知证据未明确对应角色获知关系", item_key))
    return violations


def semantic_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", str(value or ""))


def _issue(message: str, item_key: str) -> dict:
    return {"code": "canon_violation", "message": f"{message}: {item_key}"}
