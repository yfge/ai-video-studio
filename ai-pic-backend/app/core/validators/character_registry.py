"""Character registry helpers.

These helpers implement the "Story-registered characters only" policy.

We intentionally keep this module free of DB access so it can be reused by
services, prompts, and validators without creating dependency cycles.
"""

from __future__ import annotations

import re
from typing import Iterable

# Allowed generic roles (non-named extras). Keep this list small on purpose.
GENERIC_ROLE_BASES = ("路人", "店员", "旁白")

_GENERIC_ROLE_RE = re.compile(r"^(?P<base>路人|店员)(?P<suffix>[甲乙丙丁A-D]|\d+)?$")
_NAME_SPLIT_RE = re.compile(r"[\s\-_—|/\\\\]+")
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_TIMESTAMPISH_RE = re.compile(r"^[0-9T:.]+$")
_TRAILING_NOTE_RE = re.compile(r"[\(\uff08\u3010].*$")  # (...)/(（...）)/(【...】


def normalize_character_name_token(name: str | None) -> str:
    """Best-effort cleanup for a character name token."""
    if not isinstance(name, str):
        return ""
    value = name.strip().strip("\"'“”‘’")
    value = _TRAILING_NOTE_RE.sub("", value).strip()
    # Common punctuation that may end up attached to a name token.
    value = value.strip("：:，,。.!！?？;；")
    return value.strip()


def normalize_generic_role(name: str | None) -> str | None:
    """Normalize allowed generic roles to their base form."""
    token = normalize_character_name_token(name)
    if not token:
        return None
    if token == "旁白":
        return "旁白"
    match = _GENERIC_ROLE_RE.match(token)
    if not match:
        return None
    return match.group("base")


def extract_name_aliases(name: str | None) -> list[str]:
    """Extract reasonable name aliases for prompt matching.

    Examples:
      - "短剧E2E女主-林雪-2026-01-19T03-52-25-958Z" -> ["短剧E2E女主-林雪-2026-01-19T03-52-25-958Z", "短剧E2E女主", "林雪"]
      - "老拐" -> ["老拐"]
    """
    token = normalize_character_name_token(name)
    if not token:
        return []

    aliases: list[str] = [token]
    parts = [p.strip() for p in _NAME_SPLIT_RE.split(token) if p and p.strip()]
    for part in parts:
        if part == token:
            continue
        if len(part) > 32:
            continue
        if _TIMESTAMPISH_RE.match(part):
            continue
        if _CJK_RE.search(part) or part.isalpha():
            aliases.append(part)

    deduped: list[str] = []
    seen: set[str] = set()
    for item in aliases:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def preferred_display_name(name: str | None) -> str | None:
    """Pick a human-friendly display name from an internal/long name."""
    aliases = extract_name_aliases(name)
    if not aliases:
        return None

    # Prefer short CJK aliases (2-6 chars) when present.
    cjk = [a for a in aliases if _CJK_RE.search(a)]
    cjk_short = [a for a in cjk if 2 <= len(a) <= 6]
    if cjk_short:
        return sorted(cjk_short, key=len)[0]
    if cjk:
        return sorted(cjk, key=len)[0]
    return sorted(aliases, key=len)[0]


def build_alias_to_canonical_map(
    *,
    canonical_names: Iterable[str],
    extra_aliases: dict[str, Iterable[str]] | None = None,
) -> dict[str, str]:
    """Build alias -> canonical mapping.

    extra_aliases maps canonical_name -> additional aliases to consider.
    """
    mapping: dict[str, str] = {}
    for canonical in canonical_names:
        clean = normalize_character_name_token(canonical)
        if not clean:
            continue
        mapping.setdefault(clean, clean)
        for alias in extract_name_aliases(clean):
            mapping.setdefault(alias, clean)
        if extra_aliases and clean in extra_aliases:
            for alias in extra_aliases.get(clean) or []:
                a = normalize_character_name_token(str(alias))
                if a:
                    mapping.setdefault(a, clean)
                    for a2 in extract_name_aliases(a):
                        mapping.setdefault(a2, clean)
    return mapping


def normalize_to_registered_or_generic(
    name: str | None,
    *,
    alias_to_canonical: dict[str, str],
) -> str | None:
    """Return canonical name if registered, else allowed generic role, else None."""
    token = normalize_character_name_token(name)
    if not token:
        return "旁白"

    generic = normalize_generic_role(token)
    if generic:
        return generic

    if token in alias_to_canonical:
        return alias_to_canonical[token]

    # Nickname heuristics: 小X / 阿X / 老X -> try stripping the prefix if unique.
    if len(token) >= 2 and token[0] in {"小", "阿", "老"}:
        stripped = token[1:]
        if stripped in alias_to_canonical:
            return alias_to_canonical[stripped]
        # Try suffix matching (single-char stripped) only if it uniquely identifies a canonical.
        if len(stripped) == 1:
            matches = {
                canonical
                for alias, canonical in alias_to_canonical.items()
                if alias.endswith(stripped)
            }
            if len(matches) == 1:
                return next(iter(matches))

    return None
