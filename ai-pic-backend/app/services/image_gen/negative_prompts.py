from __future__ import annotations

VIRTUAL_IP_NEGATIVE_PROMPT_EXTRA = (
    "multiple faces, multiple people, extra person, crowd, group"
)


def merge_negative_prompt(*parts: str | None) -> str | None:
    """Merge comma-separated negative prompt fragments, preserving order and deduping."""
    tokens: list[str] = []
    seen: set[str] = set()

    for part in parts:
        if not part:
            continue
        for raw in str(part).split(","):
            token = raw.strip()
            if not token:
                continue
            key = token.lower()
            if key in seen:
                continue
            seen.add(key)
            tokens.append(token)

    return ", ".join(tokens) if tokens else None
