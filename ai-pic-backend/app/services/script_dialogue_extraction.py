from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from app.models.script import Story


_QUOTE_PAIRS = (
    ("\u201c", "\u201d"),
    ("\u2018", "\u2019"),
    ('"', '"'),
    ("'", "'"),
)
_SPEECH_HINT_RE = re.compile(
    r"(?:说|道|问|答|喊|叫|嘟囔|询问|回应|低语|开口|自言自语|皱眉|耸肩|一笑|喘着气|坚定|无奈)"
)
_PRONOUN_RE = re.compile(r"^[，,。；;\s]*(?:他|她|TA|ta)")


def extract_dialogues_from_scene_summary(
    summary: str,
    scene_number: int,
    *,
    character_names: List[str] | None = None,
) -> List[Dict[str, Any]]:
    """Extract quoted spoken lines from a narrative scene summary."""
    text = str(summary or "")
    known_names = _clean_names(character_names or [])
    if not text:
        return []

    dialogues: List[Dict[str, Any]] = []
    seen_contents: set[str] = set()
    for start, end, content in _iter_quoted_segments(text):
        line = content.strip()
        if len(line) < 2 or line in seen_contents:
            continue
        speaker = _resolve_speaker(text, start, end, known_names)
        if not speaker:
            continue
        seen_contents.add(line)
        dialogues.append(
            {"scene_number": scene_number, "character": speaker, "content": line}
        )
    return dialogues


def character_names_for_scene(
    scene: Dict[str, Any], story: "Story | None" = None
) -> List[str]:
    raw_names: List[Any] = []
    for key in ("characters", "focus_characters", "characters_involved"):
        values = scene.get(key)
        if isinstance(values, list):
            raw_names.extend(values)
    if story is not None:
        raw_story_chars = getattr(story, "main_characters", None)
        if isinstance(raw_story_chars, list):
            raw_names.extend(raw_story_chars)
        for item in getattr(story, "story_characters", []) or []:
            if getattr(item, "is_deleted", False):
                continue
            raw_names.append(getattr(item, "character_name", None))
    return _clean_names(raw_names)


def _iter_quoted_segments(text: str) -> List[tuple[int, int, str]]:
    segments: List[tuple[int, int, str]] = []
    for open_quote, close_quote in _QUOTE_PAIRS:
        pattern = re.compile(
            f"{re.escape(open_quote)}([^{re.escape(close_quote)}]+){re.escape(close_quote)}"
        )
        for match in pattern.finditer(text):
            segments.append((match.start(), match.end(), match.group(1)))
    return sorted(segments, key=lambda item: item[0])


def _resolve_speaker(
    text: str, quote_start: int, quote_end: int, known_names: List[str]
) -> str | None:
    before = text[max(0, quote_start - 80) : quote_start]
    after = text[quote_end : quote_end + 40]

    before_name = _speaker_from_pre_quote(before, known_names)
    if before_name:
        return before_name

    after_name = _speaker_from_post_quote(after, before, known_names)
    if after_name:
        return after_name

    context_name = _nearest_known_name(before, known_names, reverse=True)
    if context_name and (_PRONOUN_RE.search(after) or len(known_names) == 1):
        return context_name
    return context_name if context_name and not known_names else None


def _speaker_from_pre_quote(before: str, known_names: List[str]) -> str | None:
    tail = before[-40:].rstrip()
    if not tail.endswith(("：", ":")):
        return None
    return _nearest_known_name(tail, known_names, reverse=True) or (
        _pronoun_context_name(before, known_names)
        if _SPEECH_HINT_RE.search(tail)
        else None
    )


def _speaker_from_post_quote(
    after: str, before: str, known_names: List[str]
) -> str | None:
    first_sentence = re.split(r"[。！？!?]", after, maxsplit=1)[0]
    if _PRONOUN_RE.search(first_sentence) and _SPEECH_HINT_RE.search(first_sentence):
        return _pronoun_context_name(before, known_names)
    if "：" in first_sentence or ":" in first_sentence:
        return None
    after_name = _nearest_known_name(first_sentence, known_names, reverse=False)
    if after_name and _SPEECH_HINT_RE.search(first_sentence):
        return after_name
    return None


def _pronoun_context_name(before: str, known_names: List[str]) -> str | None:
    for segment in reversed([p for p in re.split(r"[。！？!?；;]", before) if p]):
        matches = _known_name_matches(segment, known_names)
        if not matches:
            continue
        non_possessive = [
            (pos, name)
            for pos, name in matches
            if not segment[pos + len(name) :].startswith("的")
        ]
        return (non_possessive or matches)[0][1]
    return _nearest_known_name(before, known_names, reverse=True)


def _known_name_matches(text: str, known_names: List[str]) -> list[tuple[int, str]]:
    matches: list[tuple[int, str]] = []
    for name in known_names:
        start = 0
        while True:
            pos = text.find(name, start)
            if pos < 0:
                break
            matches.append((pos, name))
            start = pos + len(name)
    return sorted(matches)


def _nearest_known_name(
    text: str, known_names: List[str], *, reverse: bool
) -> str | None:
    matches: list[tuple[int, str]] = []
    for name in known_names:
        pos = text.rfind(name) if reverse else text.find(name)
        if pos >= 0:
            matches.append((pos, name))
    if not matches:
        return None
    return max(matches)[1] if reverse else min(matches)[1]


def _clean_names(raw_names: List[Any]) -> List[str]:
    seen: set[str] = set()
    names: List[str] = []
    for raw in raw_names:
        name: str | None = None
        if isinstance(raw, dict):
            value = raw.get("name") or raw.get("character_name") or raw.get("id")
            name = str(value).strip() if value else None
        elif raw is not None:
            name = str(raw).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        names.append(name)
    return sorted(names, key=len, reverse=True)
