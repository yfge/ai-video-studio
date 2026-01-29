from __future__ import annotations

import pytest
from app.core.validators.character_registry import (
    build_alias_to_canonical_map,
    extract_name_aliases,
    normalize_generic_role,
    normalize_to_registered_or_generic,
    preferred_display_name,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("路人", "路人"),
        ("路人甲", "路人"),
        ("路人1", "路人"),
        ("店员", "店员"),
        ("店员A", "店员"),
        ("旁白", "旁白"),
        ("旁白甲", None),
        ("陈哲", None),
        (None, None),
        ("", None),
    ],
)
def test_normalize_generic_role(raw: str | None, expected: str | None) -> None:
    assert normalize_generic_role(raw) == expected


@pytest.mark.unit
def test_extract_name_aliases_and_preferred_display_name() -> None:
    raw = "短剧E2E女主-林雪-2026-01-19T03-52-25-958Z"
    aliases = extract_name_aliases(raw)
    assert raw in aliases
    assert "短剧E2E女主" in aliases
    assert "林雪" in aliases
    assert preferred_display_name(raw) == "林雪"


@pytest.mark.unit
def test_normalize_to_registered_or_generic_supports_nickname_suffix_match() -> None:
    alias_to_canonical = build_alias_to_canonical_map(canonical_names=["林雪"])
    assert (
        normalize_to_registered_or_generic(
            "小雪", alias_to_canonical=alias_to_canonical
        )
        == "林雪"
    )


@pytest.mark.unit
def test_normalize_to_registered_or_generic_avoids_ambiguous_nicknames() -> None:
    alias_to_canonical = build_alias_to_canonical_map(canonical_names=["林雪", "张雪"])
    assert (
        normalize_to_registered_or_generic(
            "小雪", alias_to_canonical=alias_to_canonical
        )
        is None
    )
