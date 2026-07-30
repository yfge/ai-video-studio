"""Narrow syntax recovery for otherwise complete chapter packages."""

import json
import re

from app.utils.json_utils import extract_json_block


def extract_chapter_package_payload(text: str):
    payload = extract_json_block(text)
    if payload is not None:
        return payload
    raw = text.strip()
    recovered = (
        _recover_unwrapped_records(
            raw,
            field="beats",
            item_key="beat_id",
            next_field="character_motivations",
            allowed={"beat_id", "purpose", "target_chars", "bound_event_ids"},
        )
        or raw
    )
    recovered = (
        _recover_unwrapped_records(
            recovered,
            field="character_motivations",
            item_key="character_id",
            next_field="emotional_continuity",
            allowed={"character_id", "motivation"},
        )
        or recovered
    )
    return _decode_with_one_outer_close(recovered)


def _recover_unwrapped_records(
    raw: str, *, field: str, item_key: str, next_field: str, allowed: set[str]
) -> str | None:
    start = re.search(rf'"{re.escape(field)}"\s*:\s*\[', raw)
    following = re.search(
        rf'^\s*"{re.escape(next_field)}"\s*:',
        raw[start.end() :] if start else "",
        re.MULTILINE,
    )
    if not start or not following:
        return None
    following_start = start.end() + following.start()
    close = raw.rfind("]", start.end(), following_start)
    if close < start.end():
        return None
    body = raw[start.end() : close]
    matches = list(re.finditer(rf'^\s*"{re.escape(item_key)}"\s*:', body, re.MULTILINE))
    if not matches:
        return None
    beats = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        chunk = body[match.start() : end].strip().rstrip(",")
        try:
            item = json.loads("{" + chunk + "}")
        except json.JSONDecodeError:
            return None
        if set(item) != allowed:
            return None
        beats.append(item)
    encoded = json.dumps(beats, ensure_ascii=False, separators=(",", ":"))
    return raw[: start.start()] + f'"{field}":' + encoded + raw[close + 1 :]


def _decode_with_one_outer_close(raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        if exc.pos != len(raw) or not raw.startswith("{") or not raw.endswith("}"):
            return None
    try:
        return json.loads(raw + "}")
    except json.JSONDecodeError:
        return None
