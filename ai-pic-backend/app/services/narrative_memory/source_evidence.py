"""Verify model evidence against the immutable source text."""

import re

_ELLIPSIS_PATTERN = re.compile(r"(?:…+|\.{3,})")
_CLAUSE_PATTERN = re.compile(r"[。！？!?；;]+")
_ATTRIBUTED_QUOTE_PATTERN = re.compile(
    r"^\s*(?P<speaker>[0-9A-Za-z\u4e00-\u9fff·]{1,20})"
    r'(?:说|道|问|答|喊|宣布|回应|表示)[：:]\s*[“"](?P<body>.+)[”"]\s*$',
    re.DOTALL,
)
_SPEECH_VERBS = r"(?:说|道|问|答|喊|宣布|回应|表示|开口)"


def source_contains_evidence(source_text: str, evidence: str) -> bool:
    if not _semantic_text(evidence):
        return False
    compact_source = re.sub(r"\s+", "", source_text)
    compact_evidence = re.sub(r"\s+", "", evidence)
    if compact_evidence in compact_source:
        return True
    if _ATTRIBUTED_QUOTE_PATTERN.fullmatch(evidence):
        return False
    parts = [
        _semantic_text(item)
        for item in _ELLIPSIS_PATTERN.split(evidence)
        if item.strip()
    ]
    if (
        len(parts) < 2
        or sum(map(len, parts)) < 16
        or any(len(item) < 3 for item in parts)
    ):
        return False
    source = _semantic_text(source_text)
    cursor = 0
    for part in parts:
        index = source.find(part, cursor)
        if index < 0:
            return False
        cursor = index + len(part)
    return True


def align_source_evidence(source_text: str, evidence: str) -> str:
    """Make omitted source text explicit without changing the quoted claims."""
    if not _semantic_text(evidence):
        return evidence
    if source_contains_evidence(source_text, evidence):
        return evidence
    attributed = _ATTRIBUTED_QUOTE_PATTERN.fullmatch(evidence)
    if attributed and _ELLIPSIS_PATTERN.search(attributed.group("body")):
        return evidence
    match_evidence = _attributed_quote_body(source_text, evidence) or evidence
    if match_evidence != evidence and source_contains_evidence(
        source_text, match_evidence
    ):
        return match_evidence
    semantic_source, offsets = _semantic_source(source_text)
    semantic_evidence = _semantic_text(match_evidence)
    direct_position = semantic_source.find(semantic_evidence)
    if len(semantic_evidence) >= 8 and direct_position >= 0:
        return _source_span(source_text, offsets, direct_position, semantic_evidence)
    parts = _matched_parts(semantic_source, match_evidence)
    candidate = "……".join(text for _, text in parts)
    if parts and source_contains_evidence(source_text, candidate):
        return candidate
    if parts:
        start = parts[0][0]
        end = parts[-1][0] + len(_semantic_text(parts[-1][1]))
        quoted_length = sum(len(_semantic_text(text)) for _, text in parts)
        if end - start - quoted_length <= 24:
            candidate = _source_span_range(source_text, offsets, start, end)
            if source_contains_evidence(source_text, candidate):
                return candidate
        expanded = _expanded_short_parts(source_text, offsets, parts)
        candidate = "……".join(expanded)
        if expanded and source_contains_evidence(source_text, candidate):
            return candidate
    return evidence


def _attributed_quote_body(source_text: str, evidence: str) -> str:
    match = _ATTRIBUTED_QUOTE_PATTERN.fullmatch(evidence)
    if not match:
        return ""
    body = match.group("body")
    if _ELLIPSIS_PATTERN.search(body):
        return ""
    if len(_semantic_text(body)) < 16:
        return ""
    speaker = re.escape(match.group("speaker"))
    quote = re.escape(body)
    name_char = r"0-9A-Za-z\u4e00-\u9fff·"
    prefix = (
        rf"(?<![{name_char}]){speaker}{_SPEECH_VERBS}\s*[：:]\s*" rf"[“\"]{quote}[”\"]"
    )
    suffix = rf"[“\"]{quote}[”\"]\s*{speaker}{_SPEECH_VERBS}" rf"(?![{name_char}])"
    return (
        body if re.search(prefix, source_text) or re.search(suffix, source_text) else ""
    )


def _expanded_short_parts(
    source_text: str,
    offsets: list[int],
    parts: list[tuple[int, str]],
) -> list[str]:
    expanded = []
    for index, (position, text) in enumerate(parts):
        length = len(_semantic_text(text))
        if length >= 3:
            expanded.append(text)
            continue
        boundary = parts[index + 1][0] if index + 1 < len(parts) else len(offsets)
        end = min(position + 3, boundary)
        if end - position < 3:
            return []
        expanded.append(_source_span_range(source_text, offsets, position, end))
    return expanded


def _matched_parts(semantic_source: str, evidence: str) -> list[tuple[int, str]]:
    candidates = []
    sections = [
        item.strip() for item in _ELLIPSIS_PATTERN.split(evidence) if item.strip()
    ]
    for section in sections:
        semantic = _semantic_text(section)
        if semantic_source.find(semantic) >= 0:
            candidates.append(section)
        else:
            clauses = [
                item.strip()
                for item in _CLAUSE_PATTERN.split(section)
                if _semantic_text(item)
            ]
            if len(clauses) < 2:
                return []
            candidates.extend(clauses)
    matched = _closest_ordered_matches(semantic_source, candidates)
    if len(matched) < 2 or sum(len(_semantic_text(x)) for _, x in matched) < 16:
        return []
    return matched


def _closest_ordered_matches(
    semantic_source: str, candidates: list[str]
) -> list[tuple[int, str]]:
    states = [
        (position, position + len(_semantic_text(candidates[0])), 0, [position])
        for position in _occurrences(semantic_source, _semantic_text(candidates[0]))
    ]
    for candidate in candidates[1:]:
        semantic = _semantic_text(candidate)
        next_states, state_index, best_previous = [], 0, None
        for position in _occurrences(semantic_source, semantic):
            while state_index < len(states) and states[state_index][1] <= position:
                state = states[state_index]
                if best_previous is None or (
                    state[2] - state[1],
                    -state[0],
                ) < (
                    best_previous[2] - best_previous[1],
                    -best_previous[0],
                ):
                    best_previous = state
                state_index += 1
            if best_previous is None:
                continue
            next_states.append(
                (
                    best_previous[0],
                    position + len(semantic),
                    best_previous[2] + position - best_previous[1],
                    [*best_previous[3], position],
                )
            )
        states = next_states
        if not states:
            return []
    best = min(states, key=lambda state: (state[2], state[1] - state[0], state[0]))
    return list(zip(best[3], candidates))


def _occurrences(source: str, value: str) -> list[int]:
    if not value:
        return []
    positions, start = [], 0
    while (position := source.find(value, start)) >= 0:
        positions.append(position)
        start = position + 1
    return positions


def _semantic_source(value: str) -> tuple[str, list[int]]:
    chars, offsets = [], []
    for index, char in enumerate(value):
        if re.match(r"[0-9A-Za-z\u4e00-\u9fff]", char):
            chars.append(char)
            offsets.append(index)
    return "".join(chars), offsets


def _source_span(
    source_text: str, offsets: list[int], position: int, semantic_value: str
) -> str:
    return _source_span_range(
        source_text,
        offsets,
        position,
        position + len(semantic_value),
    )


def _source_span_range(
    source_text: str, offsets: list[int], start: int, end: int
) -> str:
    if not offsets or start < 0 or end <= start or end > len(offsets):
        return ""
    return source_text[offsets[start] : offsets[end - 1] + 1]


def _semantic_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", value)
