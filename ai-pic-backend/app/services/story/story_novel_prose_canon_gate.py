"""Deterministic Canon checks against generated long-form prose."""

from __future__ import annotations

import json
import re

_LIST_SEPARATOR = re.compile(r"[、，,]|(?:或|以及|及|与|和)")
_FORBIDDEN_LIST = re.compile(
    r"(?:不存在|禁止(?:出现|存在)?|不得(?:出现|存在)?)([^。；]+)"
)
_NON_ADJACENT = re.compile(r"不临(?:天然)?([\u4e00-\u9fff]{2,6})")
_EXPLICIT_NON = re.compile(r"(?:并非|而非|非)([\u4e00-\u9fff]{2,6})(?=[，。；、）)\s])")


def prose_canon_violations(
    canon: dict,
    chapter_plan: dict,
    content_text: str,
    *,
    visible_chapter_plans: list[dict] | None = None,
) -> list[dict]:
    """Return current-text-only violations without exposing future plan details."""
    violations = _world_rule_violations(canon, content_text)
    violations.extend(
        _unauthorized_character_violations(
            canon,
            [*(visible_chapter_plans or []), chapter_plan],
            content_text,
        )
    )
    return violations


def revision_prose_canon_violations(
    revision, chapter_plan: dict, content_text: str
) -> list[dict]:
    plan = revision.generation_plan or {}
    position = int(chapter_plan.get("position") or 0)
    visible = [
        item
        for item in plan.get("chapters") or []
        if int(item.get("position") or 0) < position
    ]
    return prose_canon_violations(
        plan.get("canon") or {},
        chapter_plan,
        content_text,
        visible_chapter_plans=visible,
    )


def _world_rule_violations(canon: dict, content_text: str) -> list[dict]:
    violations = []
    seen = set()
    for rule in canon.get("world_rules") or []:
        statement = str(rule.get("statement") or "")
        for term in sorted(_forbidden_terms(statement)):
            if (
                not _asserted_term_occurs(content_text, term)
                or (rule.get("id"), term) in seen
            ):
                continue
            seen.add((rule.get("id"), term))
            violations.append(
                _violation(
                    f"正文违反 Canon 世界规则 {rule.get('id') or '未编号'}，"
                    f"命中禁项: {term}"
                )
            )
    return violations


def _asserted_term_occurs(content_text: str, term: str) -> bool:
    negation = re.compile(r"(?:不存在|没有|并非|不是|非|禁止|不见|无)\s*$")
    metaphor = re.compile(r"(?:像|如同|宛如|仿佛|犹如|好似)[^。！？!?]{0,12}$")
    return any(
        not negation.search(content_text[max(0, match.start() - 8) : match.start()])
        and not metaphor.search(
            content_text[max(0, match.start() - 16) : match.start()]
        )
        and not re.match(r"(?:般|一样|似的)", content_text[match.end() :])
        for match in re.finditer(re.escape(term), content_text)
    )


def _forbidden_terms(statement: str) -> set[str]:
    terms = {
        _clean_term(item)
        for clause in _FORBIDDEN_LIST.findall(statement)
        for item in _LIST_SEPARATOR.split(clause)
    }
    terms.update(_NON_ADJACENT.findall(statement))
    terms.update(_EXPLICIT_NON.findall(statement))
    if re.search(r"[“\"']?港[”\"']?\s*指", statement) and all(
        marker in statement for marker in ("内陆", "海洋")
    ):
        terms.add("海港")
    return {term for term in terms if len(term) >= 2}


def _clean_term(value: str) -> str:
    return re.sub(
        r"^(?:任何|天然|相关|一切|出现|存在|使用|拥有|有)|(?:等|之类)$",
        "",
        value.strip(" “”。；（）()"),
    )


def _unauthorized_character_violations(
    canon: dict, visible_chapter_plans: list[dict], content_text: str
) -> list[dict]:
    plan_surface = json.dumps(visible_chapter_plans, ensure_ascii=False, default=str)
    character_names = {
        (str(entity.get("id") or ""), str(name))
        for entity in canon.get("entities") or []
        if entity.get("kind") == "character"
        for name in [entity.get("name"), *(entity.get("aliases") or [])]
        if name and len(str(name)) >= 2
    }
    allowed = {
        name
        for entity_id, name in character_names
        if name in plan_surface or (entity_id and entity_id in plan_surface)
    }
    all_names = {name for _entity_id, name in character_names}
    unauthorized = {name for name in all_names - allowed if name in content_text}
    return [
        _violation(f"正文引入未授权具名角色: {name}") for name in sorted(unauthorized)
    ]


def _violation(message: str) -> dict:
    return {"code": "canon_violation", "message": message}
