from typing import Any, Dict, Optional

_MARKETING_KEYS = (
    "market_region",
    "micro_genre",
    "hook_plan",
    "twist_density",
    "cliffhanger_plan",
    "ad_snippets",
)


def merge_marketing_meta(*sources: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge marketing-related fields from multiple metadata sources."""
    merged: Dict[str, Any] = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in _MARKETING_KEYS:
            if key in merged:
                continue
            value = source.get(key)
            if value not in (None, "", [], {}):
                merged[key] = value
    return merged


def apply_marketing_overrides(
    base: Dict[str, Any], overrides: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Apply explicit marketing overrides onto a base dict."""
    if not overrides:
        return base
    for key in _MARKETING_KEYS:
        value = overrides.get(key)
        if value not in (None, "", [], {}):
            base[key] = value
    return base
